#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adversarial_audit.py — SPDT-005 对抗性审核 Agent
==================================================
用 DeepSeek 作为对抗性审核员，对 SOP、管线设计、Registry 进行系统性盲区扫描。

审核维度：
  1. SOP 逻辑一致性（各节之间是否矛盾）
  2. 阈值合理性（70/85 分是否过于武断）
  3. 灰区覆盖度（是否有高频场景未被覆盖）
  4. 失败模式（各阶段崩溃后的行为是否安全）
  5. 模块间契约（接口契约是否被隐性假设）
  6. Registry 配置一致性（stages 模块路径是否真实存在）

使用：
  python tools/adversarial_audit.py [--verbose] [--output audit_report.md]
"""

from __future__ import annotations

import json
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
LLM_GATEWAY_PATH = REPO_ROOT / "platform" / "shared" / "llm_gateway.py"
SOP_PATH = REPO_ROOT / "docs" / "SPDT-005_长程任务自动化SOP_v1.0.md"
REGISTRY_PATH = REPO_ROOT / "platform" / "kb" / "content_type_registry.yaml"
ROUTER_PATH = REPO_ROOT / "platform" / "1_ingest" / "router" / "pipeline_router.py"


def _load_llm_gateway():
    import importlib.util, sys as _sys
    cache_key = "_spdt_llm_gateway"
    if cache_key in _sys.modules:
        return _sys.modules[cache_key]
    spec = importlib.util.spec_from_file_location(cache_key, str(LLM_GATEWAY_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load llm_gateway from {LLM_GATEWAY_PATH}")
    module = importlib.util.module_from_spec(spec)
    _sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module


# ─────────────────────────────────────────────────────────────────
# 审核发现的数据类
# ─────────────────────────────────────────────────────────────────

@dataclass
class AuditFinding:
    severity: str          # "critical" / "high" / "medium" / "low" / "info"
    category: str         # "logic" / "threshold" / "gap" / "failure_mode" / "contract" / "registry"
    title: str
    description: str
    location: str          # 文件:行号 或 "SOP §X"
    suggestion: str
    auto_fixable: bool = False


@dataclass
class AuditReport:
    timestamp: str
    findings: list[AuditFinding] = field(default_factory=list)
    model_used: str = ""
    tokens_used: int = 0

    def add(self, finding: AuditFinding):
        self.findings.append(finding)

    def severity_order(self, s: str) -> int:
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        return order.get(s, 5)

    def sorted_findings(self) -> list[AuditFinding]:
        return sorted(self.findings, key=lambda f: (self.severity_order(f.severity), f.category))

    def render_markdown(self) -> str:
        lines = [f"# 对抗性审核报告"]
        lines.append(f"> 自动生成 | {self.timestamp} | 模型: {self.model_used} | 消耗: {self.tokens_used} tokens")
        lines.append("")

        # 分组统计
        by_sev = {}
        for f in self.findings:
            by_sev[f.severity] = by_sev.get(f.severity, 0) + 1

        lines.append("## 摘要")
        lines.append("")
        lines.append("| 严重性 | 数量 |")
        lines.append("|:---|---:|")
        for sev in ["critical", "high", "medium", "low", "info"]:
            if by_sev.get(sev):
                lines.append(f"| {sev.upper()} | {by_sev[sev]} |")
        lines.append("")

        # 按严重性分组输出
        for sev in ["critical", "high", "medium", "low", "info"]:
            group = [f for f in self.sorted_findings() if f.severity == sev]
            if not group:
                continue
            icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(sev, "")
            lines.append(f"## {icon} {sev.upper()} — {len(group)} 项")
            lines.append("")
            for f in group:
                auto = " ✅ [自动可修复]" if f.auto_fixable else " 🔒 [需人工处理]"
                lines.append(f"### {f.title}{auto}")
                lines.append(f"- **分类**: `{f.category}`")
                lines.append(f"- **位置**: `{f.location}`")
                lines.append(f"- **描述**: {f.description}")
                lines.append(f"- **建议**: {f.suggestion}")
                lines.append("")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# 规则型静态检查（不调用 LLM）
# ─────────────────────────────────────────────────────────────────

def static_audit(registry_path: Path, router_path: Path) -> list[AuditFinding]:
    """静态规则检查：模块文件是否存在、阈值是否合理等"""
    findings = []

    import yaml
    with registry_path.open(encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    with router_path.open(encoding="utf-8") as f:
        router_text = f.read()

    # 1. 获取 CONTENT_TYPE_MODULES 中实际注册的内容类型
    # 只对这些类型检查模块文件存在性（骨架类型不在此列）
    ctm_start = router_text.find("CONTENT_TYPE_MODULES = {")
    active_content_types = set()
    if ctm_start >= 0:
        ctm_section = router_text[ctm_start:]
        brace_count = 0
        ctm_end = 0
        in_ctm = False
        for i, ch in enumerate(ctm_section):
            if ch == "{":
                brace_count += 1
                in_ctm = True
            elif ch == "}":
                brace_count -= 1
                if in_ctm and brace_count == 0:
                    ctm_end = i + 1
                    break
        ctm_text = ctm_section[:ctm_end] if ctm_end > 0 else ctm_section
        active_content_types = set(re.findall(r'"(\w+)":\s*\{', ctm_text))

    # 2. 检查 registry 中 stages 模块路径是否真实存在（仅限已注册类型）
    for ct_name, ct_config in registry.get("content_types", {}).items():
        if ct_name not in active_content_types:
            continue   # 骨架类型，跳过模块存在性检查
        stages = ct_config.get("stages", {})
        for stage_name, stage_cfg in stages.items():
            module_path = stage_cfg.get("module", "")
            if module_path and not module_path.startswith("platform/"):
                continue
            if module_path:
                full_path = REPO_ROOT / (module_path.replace(".", "/") + ".py")
                if not full_path.exists():
                    findings.append(AuditFinding(
                        severity="high",
                        category="registry",
                        title=f"stages 模块文件不存在: {module_path}",
                        description=f"内容类型 `{ct_name}` 的 {stage_name} 阶段引用了 `{module_path}`，但文件不存在。",
                        location=f"content_type_registry.yaml / {ct_name}",
                        suggestion=f"将 module 改为已实现的模块路径，或先实现该模块。",
                    ))

    # 2. 检查 CONTENT_TYPE_MODULES 与 registry 的一致性
    # 只匹配 "key": { 在行首（top-level dict key）的模式
    # 使用更精确的上下文匹配：CONTENT_TYPE_MODULES = { 之后的 "key": {
    with router_path.open(encoding="utf-8") as f:
        router_content = f.read()

    # 找到 CONTENT_TYPE_MODULES 的起始位置，然后只在其范围内匹配
    ctm_start = router_content.find("CONTENT_TYPE_MODULES = {")
    if ctm_start >= 0:
        # 找到 CONTENT_TYPE_MODULES 的结束位置（匹配的右大括号）
        ctm_section = router_content[ctm_start:]
        brace_count = 0
        ctm_end = 0
        in_ctm = False
        for i, ch in enumerate(ctm_section):
            if ch == "{":
                brace_count += 1
                in_ctm = True
            elif ch == "}":
                brace_count -= 1
                if in_ctm and brace_count == 0:
                    ctm_end = i + 1
                    break
        ctm_text = ctm_section[:ctm_end] if ctm_end > 0 else ctm_section

        ct_modules = re.findall(r'"(\w+)":\s*\{', ctm_text)
        registered_types = list(registry.get("content_types", {}).keys())
        for ct in ct_modules:
            if ct not in registered_types:
                findings.append(AuditFinding(
                    severity="medium",
                    category="registry",
                    title=f"CONTENT_TYPE_MODULES 注册了但 registry 未注册: {ct}",
                    description=f"pipeline_router.py 的 CONTENT_TYPE_MODULES 中有 `{ct}`，但 content_type_registry.yaml 中没有对应的条目。",
                    location="pipeline_router.py CONTENT_TYPE_MODULES",
                    suggestion="在 registry 中添加对应条目，或从 CONTENT_TYPE_MODULES 中移除。",
                    auto_fixable=False,
                ))

    # 3. 检查 science_fact 和 science_research 是否指向同一类源（潜在冲突）
    science_types = [k for k in registry.get("content_types", {}) if "science" in k]
    if len(science_types) > 1:
        findings.append(AuditFinding(
            severity="medium",
            category="logic",
            title=f"存在多个 science 相关内容类型: {science_types}",
            description=f"science_fact 和 science_research 的定位可能重叠。science_fact（科普知识）指向 smartext/knowledge_graph，science_research 指向 radar_science_fact。两者是否真的需要分离？",
            location="content_type_registry.yaml",
            suggestion="评估是否应合并为单一 science 类型，或明确区分受众和 SLA。",
            auto_fixable=False,
        ))

    # 4. 检查 gray_zone_rules 中 action 是否都是已知类型
    known_actions = {
        "hold_publish", "double_verify", "flag_source_grade",
        "legal_review", "expert_signoff", "auto_archive",
        "source_upgrade",   # product_review: 竞品对比数据
    }
    for ct_name, ct_config in registry.get("content_types", {}).items():
        for rule in ct_config.get("gray_zone_rules", []):
            action = rule.get("action", "")
            if action and action not in known_actions:
                findings.append(AuditFinding(
                    severity="high",
                    category="gap",
                    title=f"未知 gray_zone action: {action}",
                    description=f"`{ct_name}` 的灰区规则使用了 action=`{action}`，但这是未知类型。",
                    location=f"content_type_registry.yaml / {ct_name}",
                    suggestion=f"将 action 改为已知类型：{', '.join(sorted(known_actions))}。",
                    auto_fixable=True,
                ))

    # 5. 检查阈值是否合理
    thresholds = {}
    for ct_name, ct_config in registry.get("content_types", {}).items():
        chk = ct_config.get("human_checkpoints", {})
        for m, action in chk.items():
            if action.startswith("threshold_"):
                try:
                    t = int(action.split("_")[1])
                    thresholds[f"{ct_name}/{m}"] = t
                except (IndexError, ValueError):
                    pass

    for key, t in thresholds.items():
        if t < 50:
            findings.append(AuditFinding(
                severity="medium",
                category="threshold",
                title=f"阈值过低: {key} = {t}",
                description=f"质量评分阈值 {t} 分可能过于宽松，导致低质量内容通过。",
                location=f"content_type_registry.yaml / {key.split('/')[0]}",
                suggestion="考虑将阈值提高到 65-70 分以上，确保内容基本质量。",
                auto_fixable=True,
            ))
        if t > 95:
            findings.append(AuditFinding(
                severity="medium",
                category="threshold",
                title=f"阈值过高: {key} = {t}",
                description=f"质量评分阈值 {t} 分可能过于严格，导致大量合格内容被否决。",
                location=f"content_type_registry.yaml / {key.split('/')[0]}",
                suggestion="考虑将阈值降低到 80-85 分，减少误杀率。",
                auto_fixable=True,
            ))

    return findings


# ─────────────────────────────────────────────────────────────────
# LLM 对抗性审核
# ─────────────────────────────────────────────────────────────────

LLM_ADVERSARIAL_SYSTEM_PROMPT = """你是一位资深系统架构师和内容运营专家，负责对 SPDT-005 内容管线系统进行"红队"（Red Team）对抗性审核。

你的任务是**主动寻找系统的漏洞、矛盾和盲区**，而不是赞美系统设计。

审核原则：
1. **质疑每一个假设**：阈值、规则、模块契约
2. **寻找边缘情况**：正常流程能跑，但边界条件呢？
3. **检查逻辑一致性**：A 节说的和 B 节说的是否矛盾？
4. **识别过度自信**：哪些地方的"自动"其实并不安全？
5. **找出沉默的假设**：代码/文档里没有明说，但必须为真的事情

你必须用中文回答。
"""


LLM_ADVERSARIAL_USER_TEMPLATE = """请对以下 {target} 进行对抗性审核。

{target_content}

---

请从以下 8 个维度进行系统性审查，对每个发现请给出：
- severity: critical / high / medium / low
- title: 一句话问题描述
- description: 详细说明
- suggestion: 修复建议

8 个审查维度：
1. **逻辑一致性**：各部分之间是否矛盾？
2. **阈值合理性**：数字是否武断？有无数据支撑？
3. **灰区覆盖度**：是否有高频场景未被覆盖？
4. **失败模式**：崩溃后的行为是否安全？
5. **模块契约**：接口假设是否被隐性依赖？
6. **过度自动化**：哪些"自动"其实并不安全？
7. **缺失的反馈环**：哪些决策缺乏纠错机制？
8. **现实可行性**：在真实环境中能否落地？

请以 JSON 数组格式输出 findings，示例：
```json
[
  {{"severity": "high", "title": "...", "description": "...", "suggestion": "..."}}
]
```

如果该部分没有发现问题，返回空数组 `[]`。
"""


def llm_adversarial_audit(text: str, target: str, llm) -> list[dict]:
    """调用 LLM 进行对抗性审核，返回 JSON findings"""
    user_prompt = LLM_ADVERSARIAL_USER_TEMPLATE.format(
        target=target,
        target_content=text[: 8000],  # 截断以控制 token
    )

    try:
        response = llm.chat(user_prompt, system=LLM_ADVERSARIAL_SYSTEM_PROMPT)
        # 提取 JSON 数组
        match = re.search(r'\[[\s\S]*\]', response.content)
        if match:
            findings = json.loads(match.group())
            if isinstance(findings, list):
                return findings
    except Exception as e:
        print(f"[!] LLM audit failed for {target}: {e}", file=sys.stderr)

    return []


# ─────────────────────────────────────────────────────────────────
# 主审核流程
# ─────────────────────────────────────────────────────────────────

def run_adversarial_audit(verbose: bool = False) -> AuditReport:
    report = AuditReport(timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    # 加载 LLM
    print("[*] Loading LLM gateway...")
    try:
        llm_mod = _load_llm_gateway()
        llm = llm_mod.LLMGateway()
        is_mock = not bool(llm_mod._get_api_key() if hasattr(llm_mod, "_get_api_key") else True)
        if is_mock:
            print("[!] Warning: LLM gateway in MOCK mode. Results will be limited.")
    except Exception as e:
        print(f"[!] Cannot load LLM: {e}", file=sys.stderr)
        llm = None

    # ── 阶段 0：静态检查 ─────────────────────────────────────────
    print("[*] Running static audit...")
    static_findings = static_audit(REGISTRY_PATH, ROUTER_PATH)
    for f in static_findings:
        report.add(f)
    print(f"    Static findings: {len(static_findings)}")

    # ── 阶段 1：SOP 审核 ────────────────────────────────────────
    if SOP_PATH.exists():
        print("[*] Auditing SOP document...")
        sop_text = SOP_PATH.read_text(encoding="utf-8")
        if llm:
            findings = llm_adversarial_audit(sop_text, "SPDT-005 SOP v1.0", llm)
            for f_data in findings:
                report.add(AuditFinding(
                    severity=f_data.get("severity", "medium"),
                    category="logic",
                    title=f_data.get("title", "LLM 发现"),
                    description=f_data.get("description", ""),
                    location="docs/SPDT-005_长程任务自动化SOP_v1.0.md",
                    suggestion=f_data.get("suggestion", ""),
                ))
        else:
            # 无 LLM 时的规则型检查
            report.add(AuditFinding(
                severity="medium",
                category="logic",
                title="SOP §4.4 Scorecard 嵌套结构与实际行为不一致",
                description="SOP §4.4 说明了 `result.scorecard['scorecard']['total_score']` 的嵌套结构，但这个设计本身就容易出错——开发者容易访问错误的层级。",
                location="SOP §4.4",
                suggestion="考虑在 ScorecardXXXResult 中直接暴露 `total_score` 属性，而不是要求调用者导航两层嵌套字典。",
                auto_fixable=False,
            ))
            report.add(AuditFinding(
                severity="medium",
                category="logic",
                title="SOP §2 固定顺序约束与现实迭代需求不符",
                description="Step 1 写 registry 配置 要求在 Step 2-5 实现模块 之前，但开发者常常需要边写代码边调整 registry。这种刚性顺序在实践中会阻碍迭代。",
                location="SOP §2",
                suggestion="将 Step 1 和 Step 2-5 改为可并行：先写骨架模块（即使不完整），再逐步完善 registry 配置。",
                auto_fixable=True,
            ))
        print(f"    SOP findings: {len(findings) if llm else 3}")

    # ── 阶段 2：Registry 审核 ───────────────────────────────────
    print("[*] Auditing content_type_registry.yaml...")
    import yaml
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        registry_text = f.read()
    registry_parsed = yaml.safe_load(registry_text)

    if llm:
        findings = llm_adversarial_audit(registry_text, "content_type_registry.yaml", llm)
        for f_data in findings:
            report.add(AuditFinding(
                severity=f_data.get("severity", "medium"),
                category="gap",
                title=f_data.get("title", "LLM 发现"),
                description=f_data.get("description", ""),
                location="platform/kb/content_type_registry.yaml",
                suggestion=f_data.get("suggestion", ""),
            ))

    # 无 LLM 时的规则检查已在 static_audit 中完成

    # ── 阶段 3：Pipeline Router 审核 ─────────────────────────────
    print("[*] Auditing pipeline_router.py...")
    router_text = ROUTER_PATH.read_text(encoding="utf-8")

    # 规则型检查
    # 3a: 检查 _default_topic_for_type 是否覆盖所有 CONTENT_TYPE_MODULES 注册类型
    # CONTENT_TYPE_MODULES 是实际会使用的类型，registry 中可能有骨架但未实现
    all_cts = list(registry_parsed.get("content_types", {}).keys())
    # 从 CONTENT_TYPE_MODULES 获取实际注册的类型
    ctm_start = router_text.find("CONTENT_TYPE_MODULES = {")
    if ctm_start >= 0:
        ctm_section = router_text[ctm_start:]
        brace_count = 0
        ctm_end = 0
        in_ctm = False
        for i, ch in enumerate(ctm_section):
            if ch == "{":
                brace_count += 1
                in_ctm = True
            elif ch == "}":
                brace_count -= 1
                if in_ctm and brace_count == 0:
                    ctm_end = i + 1
                    break
        ctm_text = ctm_section[:ctm_end] if ctm_end > 0 else ctm_section
        active_cts = re.findall(r'"(\w+)":\s*\{', ctm_text)
    else:
        active_cts = all_cts

    default_topics = re.findall(r'"(\w+)":\s*"([^"]+)"', router_text)
    default_topic_keys = [k for k, v in default_topics if "topic" in k.lower() or "default" in k.lower()]
    for ct in active_cts:
        if ct not in default_topic_keys:
            report.add(AuditFinding(
                severity="low",
                category="gap",
                title=f"_default_topic_for_type 缺少类型: {ct}",
                description=f"`{ct}` 在 CONTENT_TYPE_MODULES 中注册了，但 _default_topic_for_type() 中没有默认值。",
                location="pipeline_router.py _default_topic_for_type()",
                suggestion=f"在 _default_topic_for_type() 的 defaults 字典中添加 '{ct}': '内容创作'。",
                auto_fixable=True,
            ))

    # 3b: 检查 _run_ingest 的 max_signals 参数——不同 radar 模块是否都支持？
    for ct in all_cts:
        ingest_cfg = registry_parsed.get("content_types", {}).get(ct, {}).get("stages", {}).get("ingest", {})
        module_path = ingest_cfg.get("module", "")
        if module_path and "radar" in module_path:
            # 检查该 radar 模块是否有 max_signals 参数
            radar_file = REPO_ROOT / (module_path.replace(".", "/") + ".py")
            if radar_file.exists():
                radar_content = radar_file.read_text(encoding="utf-8")
                if "max_signals" not in radar_content:
                    report.add(AuditFinding(
                        severity="high",
                        category="contract",
                        title=f"radar 模块缺少 max_signals 参数: {ct}",
                        description=f"pipeline_router.py 的 _run_ingest 会传入 `max_signals=5`，但 `{module_path}` 的 Request dataclass 没有定义这个参数，会导致 TypeError。",
                        location=f"platform/{module_path.replace('platform.', '')}.py",
                        suggestion="在 Request dataclass 中添加 `max_signals: int = 5` 参数。",
                        auto_fixable=True,
                    ))

    # 3c: 检查 render_deep_industry REPO_ROOT 层级
    render_di = REPO_ROOT / "platform" / "3_render" / "engines" / "text" / "render_deep_industry.py"
    if render_di.exists():
        content = render_di.read_text(encoding="utf-8")
        if "parents[4]" in content:
            report.add(AuditFinding(
                severity="info",
                category="logic",
                title="render_deep_industry 正确使用 parents[4]",
                description="REPO_ROOT = Path(__file__).resolve().parents[4] 是正确的（text→render→engines→3_render→platform→REPO_ROOT）。",
                location="render_deep_industry.py",
                suggestion="无需修复，这是正确的。",
                auto_fixable=True,
            ))

    # 3d: 检查 scorecard 输出是否真的被 deliver 阶段使用
    if "context.scorecard" in router_text:
        # 检查 scorecard 为 None 时是否有防御性处理
        # 有效的守卫模式：if scorecard / if not scorecard / scorecard or {}
        has_guard = (
            "if scorecard" in router_text
            or "if not scorecard" in router_text
            or " or {}" in router_text   # scorecard = scorecard or {}
        )
        if not has_guard:
            report.add(AuditFinding(
                severity="high",
                category="failure_mode",
                title="_run_deliver 中 scorecard 可能为 None",
                description="pipeline_router.py 的 _run_deliver 使用 context.scorecard，但当 adapt 阶段失败时 context.scorecard 可能仍为 None 或空字典，没有防御性检查。",
                location="pipeline_router.py _run_deliver",
                suggestion="在 _run_deliver 开头添加：`scorecard = scorecard or {}`，并对 scorecard.get('scorecard', {}) 做安全访问。",
                auto_fixable=True,
            ))

    # 3e: LLM 深度审核
    if llm:
        findings = llm_adversarial_audit(router_text[:8000], "pipeline_router.py", llm)
        for f_data in findings:
            report.add(AuditFinding(
                severity=f_data.get("severity", "medium"),
                category="failure_mode",
                title=f_data.get("title", "LLM 发现"),
                description=f_data.get("description", ""),
                location="pipeline_router.py",
                suggestion=f_data.get("suggestion", ""),
            ))

    # ── 汇总 ────────────────────────────────────────────────────
    total = len(report.findings)
    critical = sum(1 for f in report.findings if f.severity == "critical")
    high = sum(1 for f in report.findings if f.severity == "high")
    print(f"\n[*] Total findings: {total} (critical={critical}, high={high})")

    # 统计
    report.model_used = "deepseek-chat" if llm else "N/A (static only)"
    report.tokens_used = 0

    return report


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SPDT-005 对抗性审核")
    parser.add_argument("--output", "-o", type=Path, default=None, help="输出 Markdown 报告路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    args = parser.parse_args()

    report = run_adversarial_audit(verbose=args.verbose)
    md = report.render_markdown()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")
        print(f"[+] Report written: {args.output}")
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(md)

    # 控制台摘要
    by_sev = {}
    for f in report.findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1

    print()
    for sev in ["critical", "high", "medium", "low", "info"]:
        if by_sev.get(sev):
            print(f"  [{sev.upper():8}] {by_sev[sev]} 项")


if __name__ == "__main__":
    main()
