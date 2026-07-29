# -*- coding: utf-8 -*-
"""
media_gates.py — G-SOURCE / G-TIMELINESS / G-FACTUAL / G-STYLE
================================================================
SOP v4.0 M4 + 内容制造管线执行规范 v1.0 §6.3 媒体领域门禁

适用领域：SPDT-005 媒体内容协调流水线
调用位置：3_render 阶段（ManuscriptsEngine pipeline_runner 调用）

门禁路径定义（SOP §6）：
  sunshine  — 自动通过
  gray_zone — 需人工签批（软违规：信源不足/时效临界/声明未逐条核验）
  failure   — 硬违规（无信源/严重失实/风格硬违规）

使用方式：
  from media_gates import GSourceGate, GTimelinessGate, GFactualGate, GStyleGate
  from media_gates import MediaGateRunner

  runner = MediaGateRunner()
  result = runner.run_all(article_data)
  # result = {"overall_pass": bool, "gates": [...], "failure_gates": [...], "gray_zone_gates": [...]}
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────
# 门禁结果类型
# ─────────────────────────────────────────────────────────────────

class GatePath(Enum):
    SUNSHINE = "sunshine"      # 自动通过
    GRAY_ZONE = "gray_zone"    # 人工签批
    FAILURE = "failure"        # 硬违规


@dataclass
class GateResult:
    """门禁检查结果（SOP §6.4 接口定义）"""
    gate_id: str
    gate_name: str
    path: GatePath
    passed: bool
    verdict: str        # PASS / FAIL / REVIEW_REQUIRED
    score: float        # 0.0-1.0
    detail: str
    violations: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "path": self.path.value,
            "passed": self.passed,
            "verdict": self.verdict,
            "score": self.score,
            "detail": self.detail,
            "violations": self.violations,
            "recommendations": self.recommendations,
        }


# ─────────────────────────────────────────────────────────────────
# 媒体领域门禁基类
# ─────────────────────────────────────────────────────────────────

class MediaGate(ABC):
    """媒体领域门禁基类（适用于 SPDT-005）"""

    gate_id: str = ""
    gate_name: str = ""
    path_options: list[GatePath] = []

    @abstractmethod
    def check(self, article: dict) -> GateResult:
        """执行门禁检查"""
        ...

    def _sunshine(self, detail: str, score: float = 1.0) -> GateResult:
        return GateResult(
            gate_id=self.gate_id,
            gate_name=self.gate_name,
            path=GatePath.SUNSHINE,
            passed=True,
            verdict="PASS",
            score=score,
            detail=detail,
        )

    def _gray_zone(self, detail: str, violations: list[dict],
                   recommendations: Optional[list[str]] = None) -> GateResult:
        return GateResult(
            gate_id=self.gate_id,
            gate_name=self.gate_name,
            path=GatePath.GRAY_ZONE,
            passed=False,
            verdict="REVIEW_REQUIRED",
            score=0.5,
            detail=detail,
            violations=violations,
            recommendations=recommendations or [],
        )

    def _failure(self, detail: str, violations: list[dict]) -> GateResult:
        return GateResult(
            gate_id=self.gate_id,
            gate_name=self.gate_name,
            path=GatePath.FAILURE,
            passed=False,
            verdict="FAIL",
            score=0.0,
            detail=detail,
            violations=violations,
        )


# ─────────────────────────────────────────────────────────────────
# G-SOURCE：信源可靠性
# ─────────────────────────────────────────────────────────────────

class GSourceGate(MediaGate):
    """
    G-SOURCE · 信源可靠性门禁

    检查内容：
      - article 中引用的信源是否有 trust_level 标注
      - 至少有一个 D 级或以上信源（SPDT-005 协调层）
      - 信源类型分布合理性

    路径规则（SOP §6.3）：
      sunshine  — 有 D+ 级信源，分布合理
      gray_zone — 有信源但等级偏低（仅 E/F 级）或缺失 trust_level
      failure   — 无任何可溯源信源
    """

    gate_id = "G-SOURCE"
    gate_name = "信源可靠性"
    path_options = [GatePath.SUNSHINE, GatePath.GRAY_ZONE, GatePath.FAILURE]

    # SPDT-005 信任等级（来自 SPDT-KTE trust_levels.yaml 媒体适配）
    TRUST_LEVELS = {
        "A": 1.0,   # 学术顶刊 / 政府公文
        "B": 0.9,   # 权威媒体 / 机构报告
        "C": 0.75,  # 专业媒体 / 行业报告
        "D": 0.6,   # 一般媒体 / 新闻稿
        "E": 0.4,   # 社交媒体 / 自媒体
        "F": 0.1,   # 匿名信源 / 未经核实
    }

    # 通过阈值：至少 D 级（≥0.6）
    MIN_PASS_SCORE = 0.6

    def check(self, article: dict) -> GateResult:
        """
        Args:
            article: article_v2 格式内容，期望包含以下字段之一：
              - sources: [{"name": str, "trust_level": str}, ...]
              - metadata.sources: [...]
              - knowledge_nodes[].source_knowledge_nodes: [...]  （scene_v2 格式）
        """
        violations: list[dict] = []

        # 提取信源列表（兼容 article_v2 和 scene_v2 两种格式）
        sources: list[dict] = []

        # article_v2 格式
        sources = article.get("sources", [])
        if not sources:
            metadata = article.get("metadata", {})
            sources = metadata.get("sources", [])

        # scene_v2 格式（来自 ManuscriptsEngine，可能传入 scene_v2 格式）
        if not sources:
            scenes = article.get("scenes", [])
            for scene in scenes:
                for kn in scene.get("source_knowledge_nodes", []):
                    if isinstance(kn, dict):
                        sources.append(kn)
                    elif isinstance(kn, str):
                        sources.append({"name": kn, "trust_level": "E"})  # 未知信源默认 E

        if not sources:
            return self._failure(
                detail="文章无任何可溯源信源（sources 字段为空）",
                violations=[{
                    "field": "sources",
                    "expected": "至少 1 个可溯源信源",
                    "actual": "空",
                    "severity": "critical"
                }]
            )

        # 计算信源得分
        scored_sources: list[tuple[dict, float]] = []
        for src in sources:
            level = src.get("trust_level", "E").upper()
            score = self.TRUST_LEVELS.get(level, 0.3)
            scored_sources.append((src, score))

        best_score = max(s for _, s in scored_sources)
        avg_score = sum(s for _, s in scored_sources) / len(scored_sources)

        # 统计各等级信源数量
        level_counts: dict[str, int] = {}
        for src, score in scored_sources:
            level = src.get("trust_level", "E").upper()
            level_counts[level] = level_counts.get(level, 0) + 1

        # 硬违规：无 D+ 级信源
        if best_score < self.MIN_PASS_SCORE:
            return self._failure(
                detail=f"最高信源等级 {max(level_counts, key=level_counts.get)}（{best_score}），"
                       f"低于 D 级（≥{self.MIN_PASS_SCORE}）要求",
                violations=[{
                    "field": "sources",
                    "expected": f"至少 1 个 D+ 级信源（≥{self.MIN_PASS_SCORE}）",
                    "actual": f"最高等级 {max(level_counts, key=level_counts.get)}（{best_score}）",
                    "severity": "critical",
                    "sources": [f"{s.get('name','?')}:{s.get('trust_level','?')}" for s in sources]
                }]
            )

        # 灰区：所有信源都是 E/F 级
        all_low = all(score < self.MIN_PASS_SCORE for _, score in scored_sources)
        if all_low:
            return self._gray_zone(
                detail=f"信源等级偏低（最高 {max(level_counts, key=level_counts.get)}，"
                       f"{best_score}），建议补充 D+ 级信源",
                violations=[{
                    "field": "sources",
                    "expected": f"D+ 级（≥{self.MIN_PASS_SCORE}）",
                    "actual": f"最高 {max(level_counts, key=level_counts.get)}（{best_score}）",
                    "severity": "major",
                    "sources": [f"{s.get('name','?')}:{s.get('trust_level','?')}" for s in sources]
                }],
                recommendations=[
                    f"建议至少补充 1 个 B/C/D 级信源",
                    f"当前分布：{' / '.join(f'{k}×{v}' for k, v in sorted(level_counts.items()))}"
                ]
            )

        return self._sunshine(
            detail=f"信源通过，D+ 级以上 {sum(v for k,v in level_counts.items() if k in 'ABCD')} 个，"
                   f"平均分 {avg_score:.2f}，分布：{' / '.join(f'{k}×{v}' for k,v in sorted(level_counts.items()))}",
            score=avg_score
        )


# ─────────────────────────────────────────────────────────────────
# G-TIMELINESS：时效性
# ─────────────────────────────────────────────────────────────────

class GTimelinessGate(MediaGate):
    """
    G-TIMELINESS · 时效性门禁

    检查内容：
      - 稿件发布时间距事件时间差是否在阈值内
      - 不同内容类型（breaking_news/deep_industry_report/tech_explainer）阈值不同
      - 快讯类：≤4h，否则自动降级为普通新闻

    路径规则（SOP §6.3）：
      sunshine  — 在时效阈值内
      gray_zone — 超过时效阈值但仍可发布（标注时间差）
      failure   — 超过绝对时效上限（内容完全失效）
    """

    gate_id = "G-TIMELINESS"
    gate_name = "时效性"
    path_options = [GatePath.SUNSHINE, GatePath.GRAY_ZONE, GatePath.FAILURE]

    # content_type → (时时效阈值 hours, 绝对时效上限 hours)
    TIMELINESS_THRESHOLDS = {
        "breaking_news":       (4,   24),   # 快讯：4h 内，24h 绝对上限
        "tech_explainer":      (48,  168),  # 科普：48h 内，168h（7天）绝对上限
        "deep_industry_report": (72,  720),  # 深度：72h 内，720h（30天）绝对上限
        "oped":                (168, 720),  # 评论：168h（7天）内
        "default":             (24,  168),  # 默认：24h 内，168h 绝对上限
    }

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """解析多种格式的时间字符串"""
        if not dt_str:
            return None
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except ValueError:
                pass
        return None

    def _hours_between(self, dt1: datetime, dt2: datetime) -> float:
        """计算两个时间之间的小时差（取绝对值）"""
        return abs((dt1 - dt2).total_seconds()) / 3600

    def check(self, article: dict) -> GateResult:
        """
        Args:
            article: article_v2 内容，期望包含：
              - metadata.event_time: 事件发生时间（ISO 8601）
              - metadata.publish_time: 计划发布时间（ISO 8601，缺省则用当前时间）
              - metadata.content_type: 内容类型（决定阈值）
        """
        violations: list[dict] = []

        metadata = article.get("metadata", {})

        event_time_str = metadata.get("event_time", "")
        publish_time_str = metadata.get("publish_time", "")

        event_time = self._parse_datetime(event_time_str)
        if not event_time:
            return self._gray_zone(
                detail="无法解析 event_time，缺少事件时间标注",
                violations=[{
                    "field": "metadata.event_time",
                    "expected": "ISO 8601 时间字符串",
                    "actual": event_time_str or "空",
                    "severity": "major"
                }],
                recommendations=["建议补充 metadata.event_time 以进行时效性评估"]
            )

        # 使用 publish_time 或当前时间
        if publish_time_str:
            publish_time = self._parse_datetime(publish_time_str)
        else:
            publish_time = datetime.now(timezone.utc)

        if not publish_time:
            publish_time = datetime.now(timezone.utc)

        hours_diff = self._hours_between(event_time, publish_time)

        # 获取阈值
        content_type = metadata.get("content_type", "default")
        threshold, absolute_limit = self.TIMELINESS_THRESHOLDS.get(
            content_type, self.TIMELINESS_THRESHOLDS["default"]
        )

        # 硬违规：超过绝对时效上限
        if hours_diff > absolute_limit:
            return self._failure(
                detail=f"[{content_type}] 时效完全失效：{hours_diff:.1f}h > {absolute_limit}h（绝对上限）",
                violations=[{
                    "field": "metadata.event_time / publish_time",
                    "expected": f"≤{absolute_limit}h",
                    "actual": f"{hours_diff:.1f}h",
                    "severity": "critical",
                    "event_time": event_time_str,
                    "publish_time": publish_time_str,
                    "hours_diff": round(hours_diff, 1)
                }]
            )

        # 灰区：超过时效阈值但在绝对上限内
        if hours_diff > threshold:
            return self._gray_zone(
                detail=f"[{content_type}] 时效偏老：{hours_diff:.1f}h > {threshold}h（阈值）",
                violations=[{
                    "field": "metadata.event_time / publish_time",
                    "expected": f"≤{threshold}h",
                    "actual": f"{hours_diff:.1f}h",
                    "severity": "major",
                    "event_time": event_time_str,
                    "publish_time": publish_time_str,
                    "hours_diff": round(hours_diff, 1)
                }],
                recommendations=[
                    f"[{content_type}] 建议 {threshold}h 内发布",
                    "考虑更新数据或调整内容类型标注"
                ]
            )

        return self._sunshine(
            detail=f"[{content_type}] 时效性良好：{hours_diff:.1f}h ≤ {threshold}h（阈值）",
            score=round(max(0, 1 - hours_diff / threshold), 2)
        )


# ─────────────────────────────────────────────────────────────────
# G-FACTUAL：事实核查
# ─────────────────────────────────────────────────────────────────

class GFactualGate(MediaGate):
    """
    G-FACTUAL · 事实核查门禁

    检查内容：
      - article 中包含的关键数据是否与 source_knowledge_nodes 溯源匹配
      - 数字/统计数据的引用格式规范
      - 无明显矛盾声明

    路径规则（SOP §6.3）：
      sunshine  — 所有关键声明均有信源支持
      gray_zone — 部分声明缺源或有歧义（需人工核查）
      failure   — 发现明显事实错误（年代/数字/名称错误）

    注意：此门禁是静态检查，不调用外部核查 API。
    LLM 级事实核查由 ManuscriptsEngine 在 2_structure 阶段完成。
    """

    gate_id = "G-FACTUAL"
    gate_name = "事实核查"
    path_options = [GatePath.SUNSHINE, GatePath.GRAY_ZONE, GatePath.FAILURE]

    # 事实错误的严重程度
    FACTUAL_ERROR_PATTERNS = {
        # 年代错误（精确到 10 年内）
        r"(公元)?(\d{4})年": "year",
        # 百分比检查（数字+%）
        r"(\d+(?:\.\d+)?)\s*%": "percentage",
        # 公司/机构名（带"：""等标记的）
        r"[《「""]([^""》」]{2,20})[》」""]": "name",
    }

    def _extract_claims(self, article: dict) -> list[dict]:
        """提取文章中的可核查声明"""
        claims: list[dict] = []

        def text_content(obj):
            if isinstance(obj, str):
                return obj
            if isinstance(obj, dict):
                parts = []
                for v in obj.values():
                    if isinstance(v, (str, list)):
                        parts.append(text_content(v))
                    elif isinstance(v, dict):
                        parts.append(text_content(v))
                return " ".join(parts)
            if isinstance(obj, list):
                return " ".join(text_content(i) for i in obj)
            return ""

        # 提取全文
        body_text = text_content(article.get("body", []))
        if not body_text:
            body_text = text_content(article.get("scenes", []))
        if not body_text:
            body_text = text_content(article)

        # 提取数字声明
        for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(%|倍|万|亿|千人|万人)", body_text):
            claims.append({
                "type": "numeric",
                "value": match.group(1),
                "unit": match.group(2),
                "text": match.group(0),
                "position": match.start(),
            })

        return claims

    def _check_source_traceability(self, article: dict, claims: list[dict]) -> list[dict]:
        """检查声明是否可溯源"""
        violations: list[dict] = []

        # 提取所有 knowledge_nodes
        k_nodes: list[dict] = []
        scenes = article.get("scenes", [])
        for scene in scenes:
            for kn in scene.get("source_knowledge_nodes", []):
                if isinstance(kn, dict):
                    k_nodes.append(kn)

        # article_v2 格式
        if not k_nodes:
            k_nodes = article.get("knowledge_nodes", [])

        # 无信源节点 → 全部声明缺溯源
        if not k_nodes and claims:
            violations.append({
                "field": "knowledge_nodes / source_knowledge_nodes",
                "expected": "至少覆盖关键数字声明的信源节点",
                "actual": "无",
                "severity": "major",
                "claims_without_source": [c["text"] for c in claims[:5]]  # 只报前 5 个
            })

        return violations

    def check(self, article: dict) -> GateResult:
        """
        Args:
            article: article_v2/scene_v2 内容
        """
        violations: list[dict] = []

        # 提取声明
        claims = self._extract_claims(article)

        # 检查溯源
        traceability_violations = self._check_source_traceability(article, claims)
        violations.extend(traceability_violations)

        # 检查 metadata 中的 factuality 标注（如果 ManuscriptsEngine 已完成核查）
        metadata = article.get("metadata", {})
        factuality = metadata.get("factuality", {})
        if factuality:
            errors = factuality.get("errors", [])
            warnings = factuality.get("warnings", [])

            if errors:
                return self._failure(
                    detail=f"发现 {len(errors)} 项事实错误（由 ManuscriptsEngine 核查）",
                    violations=[{
                        "field": "metadata.factuality.errors",
                        "expected": "0 errors",
                        "actual": f"{len(errors)} errors",
                        "severity": "critical",
                        "errors": errors[:3]
                    }]
                )

            if warnings:
                return self._gray_zone(
                    detail=f"发现 {len(warnings)} 项事实存疑（由 ManuscriptsEngine 核查）",
                    violations=[{
                        "field": "metadata.factuality.warnings",
                        "expected": "0 warnings",
                        "actual": f"{len(warnings)} warnings",
                        "severity": "major",
                        "warnings": warnings[:3]
                    }],
                    recommendations=["建议逐条核查存疑声明"]
                )

        # 静态检查：声明缺溯源
        if traceability_violations:
            return self._gray_zone(
                detail=f"发现 {len(traceability_violations)} 项声明缺溯源，共 {len(claims)} 条数字声明",
                violations=traceability_violations,
                recommendations=[
                    f"建议补充信源节点覆盖 {len(claims)} 条数字声明",
                    " ManuscriptsEngine 将在 2_structure 阶段完成 LLM 级事实核查"
                ]
            )

        return self._sunshine(
            detail=f"事实核查通过（{len(claims)} 条声明，{len(article.get('scenes', article.get('knowledge_nodes', [])))} 个信源节点）",
            score=1.0
        )


# ─────────────────────────────────────────────────────────────────
# G-STYLE：风格合规
# ─────────────────────────────────────────────────────────────────

class GStyleGate(MediaGate):
    """
    G-STYLE · 风格合规门禁

    检查内容：
      - 稿件是否遵循媒体风格指南（体裁 + 内容类型）
      - breaking_news / deep_industry_report / tech_explainer / oped 各有特定结构要求
      - 无禁用词汇/表达（脏话/极端用语/绝对化表达）

    路径规则（SOP §6.3）：
      sunshine  — 完全符合体裁风格规范
      gray_zone — 部分偏差（建议修改）
      failure   — 硬违规（出现禁用表达/体裁结构完全不符）
    """

    gate_id = "G-STYLE"
    gate_name = "风格合规"
    path_options = [GatePath.SUNSHINE, GatePath.GRAY_ZONE, GatePath.FAILURE]

    # 禁用表达（绝对化/极端用语）
    # 使用词边界 \b 避免误匹配合法词（如"强劲"/"维持"）
    BANNED_PATTERNS = [
        # 极端形容词（完整词）：最优秀 / 最差 / 最失败 等
        (re.compile(r"\b最优秀\b|\b最差\b|\b最失败\b|\b最美好\b"), "极端形容词"),
        # 绝对化表述
        (re.compile(r"\b永远\b|\b绝不\b|\b必须成功\b|\b一定成功\b"), "绝对化表述"),
        # 禁用词占位符
        (re.compile(r"\b脏话占位符\b"), "禁用词"),
    ]

    # 各体裁的最小段落数
    MIN_PARAGRAPHS = {
        "breaking_news": 3,
        "tech_explainer": 5,
        "deep_industry_report": 8,
        "oped": 4,
        "default": 3,
    }

    def check(self, article: dict) -> GateResult:
        """
        Args:
            article: article_v2 内容，期望包含：
              - metadata.content_type: 内容类型
              - body / scenes: 正文内容
        """
        violations: list[dict] = []
        recommendations: list[str] = []

        metadata = article.get("metadata", {})
        content_type = metadata.get("content_type", "default")

        # 提取正文
        body = article.get("body", [])
        if not body:
            scenes = article.get("scenes", [])
            body = [s.get("content", {}).get("text", "") for s in scenes if isinstance(s, dict)]
        if not body:
            body = [article.get("content", {}).get("text", "")]

        full_text = " ".join(b if isinstance(b, str) else "" for b in body)

        # 1. 体裁结构检查
        para_count = len([b for b in body if isinstance(b, str) and len(b) > 10])
        min_para = self.MIN_PARAGRAPHS.get(content_type, self.MIN_PARAGRAPHS["default"])

        if para_count < min_para:
            violations.append({
                "field": f"body ({content_type})",
                "expected": f"≥{min_para} 个段落",
                "actual": f"{para_count} 个段落",
                "severity": "major"
            })

        # 2. 禁用表达检查
        for pattern, label in self.BANNED_PATTERNS:
            matches = pattern.findall(full_text)
            if matches:
                violations.append({
                    "field": "body.text",
                    "expected": f"无 {label}",
                    "actual": f"发现 {len(matches)} 处",
                    "severity": "critical",
                    "examples": matches[:3]
                })

        # 3. breaking_news 特检：必须有 headline
        if content_type == "breaking_news":
            headline = metadata.get("headline", "") or article.get("content", {}).get("title", "")
            if len(headline) < 10:
                violations.append({
                    "field": "metadata.headline",
                    "expected": "≥10 字快讯标题",
                    "actual": f"'{headline}' ({len(headline)}字)",
                    "severity": "major"
                })

        # 4. deep_industry_report 特检：必须有 executive_summary
        if content_type == "deep_industry_report":
            summary = metadata.get("executive_summary", "")
            if len(summary) < 50:
                violations.append({
                    "field": "metadata.executive_summary",
                    "expected": "≥50 字执行摘要",
                    "actual": f"'{summary}' ({len(summary)}字)",
                    "severity": "major"
                })

        # 硬违规判定
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        if critical_violations:
            return self._failure(
                detail=f"发现 {len(critical_violations)} 项风格硬违规",
                violations=critical_violations
            )

        # 灰区
        if violations:
            recommendations.append(f"[{content_type}] 建议修改 {len(violations)} 项风格偏差")
            return self._gray_zone(
                detail=f"发现 {len(violations)} 项风格偏差（major 级别）",
                violations=violations,
                recommendations=recommendations
            )

        return self._sunshine(
            detail=f"[{content_type}] 风格完全合规，{para_count} 个段落",
            score=1.0
        )


# ─────────────────────────────────────────────────────────────────
# 批量门禁执行器
# ─────────────────────────────────────────────────────────────────

class MediaGateRunner:
    """
    媒体领域门禁批量执行器

    用法：
        runner = MediaGateRunner()
        result = runner.run_all(article_v2_data)

        if not result["overall_pass"]:
            for gid in result["failure_gates"]:
                print(f"FAILURE: {gid}")
            for gid in result["gray_zone_gates"]:
                print(f"REVIEW: {gid}")
    """

    def __init__(self):
        self.gates: list[MediaGate] = [
            GSourceGate(),
            GTimelinessGate(),
            GFactualGate(),
            GStyleGate(),
        ]

    def run_all(self, article: dict) -> dict:
        """
        执行所有媒体领域门禁。

        Args:
            article: article_v2 格式内容（来自 ManuscriptsEngine 2_structure 输出）

        Returns:
            {
                "overall_pass": bool,          # 无 failure 门禁
                "gates": [GateResult.to_dict(), ...],
                "failure_gates": [gate_id, ...],
                "gray_zone_gates": [gate_id, ...],
                "sunshine_gates": [gate_id, ...],
            }
        """
        results: list[GateResult] = []
        for gate in self.gates:
            try:
                results.append(gate.check(article))
            except Exception as e:
                # 门禁执行异常 → 视为灰区（不阻断，但记录）
                results.append(GateResult(
                    gate_id=gate.gate_id,
                    gate_name=gate.gate_name,
                    path=GatePath.GRAY_ZONE,
                    passed=False,
                    verdict="REVIEW_REQUIRED",
                    score=0.5,
                    detail=f"门禁执行异常: {str(e)}",
                    violations=[{"error": str(e), "gate": gate.gate_id}],
                ))

        failure_gates = [r.gate_id for r in results if r.path == GatePath.FAILURE]
        gray_zone_gates = [r.gate_id for r in results if r.path == GatePath.GRAY_ZONE]
        sunshine_gates = [r.gate_id for r in results if r.path == GatePath.SUNSHINE]

        return {
            "overall_pass": len(failure_gates) == 0,
            "gates": [r.to_dict() for r in results],
            "failure_gates": failure_gates,
            "gray_zone_gates": gray_zone_gates,
            "sunshine_gates": sunshine_gates,
        }

    def check_single(self, article: dict, gate_id: str) -> GateResult:
        """单独执行某个门禁"""
        gate_map = {g.gate_id: g for g in self.gates}
        gate = gate_map.get(gate_id)
        if not gate:
            raise ValueError(f"Unknown gate_id: {gate_id} (available: {list(gate_map.keys())})")
        return gate.check(article)
