#!/usr/bin/env python3
"""
PT-047 Phase 0 — COG CLI 诊断系统
PT-047_SocSciAgent | 三层漏斗决策过程可视化工具

功能:
  接收 COG JSON 配置 → 输出三层漏斗决策过程的 JSON Lines 结构化日志。
  输入: COG JSON 配置文件路径。
  输出: stdout + 可选 .jsonl 文件，每个决策节点含 layer/score/candidates/reason。
  约束: 纯 CLI，≤500 行代码，无任何图形界面依赖。
  复用: module_lib.hmi (日志格式化)，module_lib.output (报告生成)。

用法:
  python cog_diag.py --input cog_config.json
  python cog_diag.py --input cog_config.json --output result.jsonl
  python cog_diag.py --input cog_config.json --verbose
  python cog_diag.py --validate-template template_registry.yaml
"""

import sys
import json
import yaml
import argparse
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
from functools import reduce

__version__ = "0.1.0"
__author__ = "PT-047 SDC Build | Phase 0"

# ═══════════════════════════════════════════════════════════════════════
# 路径配置 — 兼容 module_lib 复用约定
# ═══════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent.resolve()
# cog_diag.py is at: PT-047_SocSciAgent/diagnostics/cog_cli/cog_diag.py
# parents[0]=cog_cli, [1]=diagnostics, [2]=PT-047_SocSciAgent (THIS is correct)
PT047_ROOT = SCRIPT_DIR.parents[1]
TEMPLATE_REGISTRY_PATH = PT047_ROOT / "templates" / "template_registry.yaml"
DEFAULT_TEMPLATE_REGISTRY = TEMPLATE_REGISTRY_PATH

# ═══════════════════════════════════════════════════════════════════════
# 数据结构 — COG 三层漏斗决策节点
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class FunnelNode:
    """单个漏斗决策节点。"""
    run_id: str
    layer: int           # 1=L1必选标签过滤, 2=L2亲和度评分, 3=L3张力弧终选
    stage: str           # 阶段名
    score: Optional[float]
    candidates: list     # 候选模板 ID 列表
    reason: str          # 决策理由
    timestamp: str

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "FunnelNode":
        return cls(**d)


# ═══════════════════════════════════════════════════════════════════════
# 模块复用桥接 — module_lib.output 报告生成（fallback: 纯内置）
# ═══════════════════════════════════════════════════════════════════════

try:
    sys.path.insert(0, r"D:\9_infra\module_lib")
    from modules.output.output_format_converter import OutputFormatConverter
    _HAS_OUTPUT_LIB = True
except Exception:
    _HAS_OUTPUT_LIB = False


def _format_hmi_log(level: str, message: str) -> str:
    """module_lib.hmi 风格的结构化日志格式化（兼容 fallback）。"""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    level_tag = f"[{level.upper():^8}]"
    return f"{timestamp} {level_tag} {message}"


def _emit_jsonl(node: FunnelNode, out_handle, verbose: bool = False):
    """输出单条 JSON Lines 记录到文件和 stdout。"""
    line = node.to_jsonl()
    out_handle.write(line + "\n")
    out_handle.flush()
    if verbose:
        print(line)


# ═══════════════════════════════════════════════════════════════════════
# Layer 1 — 必选标签过滤 (Required Tag Filter)
# ═══════════════════════════════════════════════════════════════════════

def layer1_required_tag_filter(
    templates: list,
    cog: dict
) -> tuple[list[dict], FunnelNode]:
    """
    漏斗第一层: 按必选标签过滤。

    规则:
      - 若 COG 指定了 required_tags，取同时满足所有 required_tags 的模板
      - 若无 required_tags，全部模板通过
      - 排除任一 forbidden_tag 被命中的模板
    """
    required = set(cog.get("required_tags", []))
    forbidden = set(cog.get("forbidden_tags", []))

    candidates = []
    for tpl in templates:
        tpl_tags = set(tpl.get("required_tags", []))
        tpl_forbidden = set(tpl.get("forbidden_tags", []))
        # 必须覆盖所有 required_tags
        # 不得包含任何 forbidden_tags
        if required and not required.issubset(tpl_tags):
            continue
        if forbidden & tpl_forbidden:
            continue
        candidates.append(tpl)

    reason = (
        f"L1过滤: 必选标签={sorted(required) if required else '无'}, "
        f"禁用标签={sorted(forbidden) if forbidden else '无'} → "
        f"{len(candidates)}/{len(templates)} 模板通过"
    )
    return candidates, reason


# ═══════════════════════════════════════════════════════════════════════
# Layer 2 — 亲和度评分 (Affinity Scoring)
# ═══════════════════════════════════════════════════════════════════════

CHAPTER_ROLE_KEYS = ["anchor_event", "deep_dive", "counterpoint",
                     "macro_frame", "synthesis", "bridge"]


def layer2_affinity_scoring(
    candidates: list,
    cog: dict,
    chapter_affinity: dict
) -> tuple[list[tuple], FunnelNode]:
    """
    漏斗第二层: 按章节角色亲和度矩阵评分。

    规则:
      - 读取 COG 中的 chapter_role_weights（6维向量，权重之和=1）
      - 读取模板的 chapter_role_affinity 矩阵
      - 计算加权余弦相似度
      - 分数归一化到 [0,1]
    """
    weights = cog.get("chapter_role_weights", {})
    # 默认均匀权重
    if not weights:
        weights = {k: 1.0 / len(CHAPTER_ROLE_KEYS) for k in CHAPTER_ROLE_KEYS}
    else:
        total = sum(weights.values()) or 1.0
        weights = {k: v / total for k, v in weights.items()}

    scored = []
    for tpl in candidates:
        tpl_affinity = tpl.get("chapter_role_affinity", {})
        score = 0.0
        for role_key in CHAPTER_ROLE_KEYS:
            w = weights.get(role_key, 0.0)
            # 亲和度: 3=首选, 2=次选, 1=勉强, 0=违和
            affinity = tpl_affinity.get(role_key, 0)
            score += w * affinity / 3.0  # 归一化到 [0,1]
        scored.append((score, tpl))

    # 按分数降序排列
    scored.sort(key=lambda x: x[0], reverse=True)
    reason = (
        f"L2亲和度评分: 章节角色权重={weights} → "
        f"最高分={scored[0][0]:.3f}({scored[0][1]['template_id']})"
        if scored else "L2无候选"
    )
    top_k = [t["template_id"] for _, t in scored[:5]]
    return scored, reason


# ═══════════════════════════════════════════════════════════════════════
# Layer 3 — 张力弧终选 (Tension Arc Final Ranking)
# ═══════════════════════════════════════════════════════════════════════

TENSION_ARC_KEYS = [
    "narrative_hook", "rising_tension", "climax_decision",
    "reflective_close", "dramatic_irony", "structural_reveal",
    "quiet_daily_life", "disruption", "resilience",
    "curiosity_hook", "cultural_shock", "analytical_expansion",
    "character_intro", "hope_buildup", "tragic_climax",
    "status_quo", "disruptive_event", "structural_shift",
    "intellectual_discomfort", "breakthrough_moment", "social_resistance",
    "familiar_narrative", "cognitive_conflict", "paradigm_shift",
    "slow_buildup", "long_term_impact", "macro_reflection",
    "stasis", "slow_acceleration", "sudden_emergence",
    "neutral_setup", "divergent_views", "structural_inevitability",
    "tragic_ambiguity", "nuanced_conclusion",
]


def layer3_tension_arc_final(
    scored: list[tuple],
    cog: dict,
    top_k: int = 3
) -> tuple[list[tuple], FunnelNode]:
    """
    漏斗第三层: 张力弧(Tension Arc)评分 + 最终排序。

    规则:
      - 读取 COG 指定的 desired_tension_arcs（期望的张力弧序列）
      - 计算每条模板张力弧与期望弧的 Jaccard 重叠度
      - 与 L2 分数做加权组合: final = 0.6*L2 + 0.4*tension_score
      - 输出 Top-K 推荐结果
    """
    desired_arcs = set(cog.get("desired_tension_arcs", []))
    tension_weight = cog.get("tension_weight", 0.4)
    l2_weight = 1.0 - tension_weight

    final_scored = []
    for l2_score, tpl in scored:
        tpl_arcs = set(tpl.get("tension_arc", []))
        if not desired_arcs or not tpl_arcs:
            tension_score = 0.5  # 无偏好时给中性分
        else:
            jaccard = len(desired_arcs & tpl_arcs) / max(len(desired_arcs | tpl_arcs), 1)
            tension_score = jaccard

        final_score = l2_weight * l2_score + tension_weight * tension_score
        final_scored.append((final_score, l2_score, tension_score, tpl))

    final_scored.sort(key=lambda x: x[0], reverse=True)
    top_results = final_scored[:top_k]
    reason = (
        f"L3张力弧终选: desired_arcs={sorted(desired_arcs) if desired_arcs else '无'} "
        f"→ Top{top_k}: "
        + ", ".join(
            f"{t['template_id']}(L2={l2:.3f},T={tension:.3f},F={f:.3f})"
            for f, l2, tension, t in top_results
        )
    )
    return final_scored, reason


# ═══════════════════════════════════════════════════════════════════════
# 主入口 — 三层漏斗流水线
# ═══════════════════════════════════════════════════════════════════════

def run_cog_diagnostic(
    cog_config: dict,
    template_registry: list,
    chapter_affinity: dict,
    run_id: str,
    out_handle,
    verbose: bool = False,
) -> list[FunnelNode]:
    """
    运行完整的三层漏斗诊断流水线。
    返回所有漏斗节点的列表。
    """
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    nodes = []

    # ── Layer 1: Required Tag Filter ──────────────────────────────
    l1_candidates, l1_reason = layer1_required_tag_filter(
        template_registry, cog_config
    )
    node_l1 = FunnelNode(
        run_id=run_id,
        layer=1,
        stage="required_tag_filter",
        score=None,
        candidates=[t["template_id"] for t in l1_candidates],
        reason=l1_reason,
        timestamp=timestamp,
    )
    nodes.append(node_l1)
    _emit_jsonl(node_l1, out_handle, verbose)
    print(_format_hmi_log("INFO", f"L1过滤后候选: {len(l1_candidates)}"))

    if not l1_candidates:
        print(_format_hmi_log("WARN", "L1过滤后无候选，漏斗终止"))
        return nodes

    # ── Layer 2: Affinity Scoring ──────────────────────────────────
    l2_scored, l2_reason = layer2_affinity_scoring(
        l1_candidates, cog_config, chapter_affinity
    )
    node_l2 = FunnelNode(
        run_id=run_id,
        layer=2,
        stage="affinity_scoring",
        score=l2_scored[0][0] if l2_scored else None,
        candidates=[t["template_id"] for _, t in l2_scored[:5]],
        reason=l2_reason,
        timestamp=timestamp,
    )
    nodes.append(node_l2)
    _emit_jsonl(node_l2, out_handle, verbose)
    print(_format_hmi_log("INFO", f"L2评分 Top-5: {[t['template_id'] for _,t in l2_scored[:5]]}"))

    if not l2_scored:
        print(_format_hmi_log("WARN", "L2评分后无候选，漏斗终止"))
        return nodes

    # ── Layer 3: Tension Arc Final Ranking ─────────────────────────
    top_k = cog_config.get("top_k", 3)
    l3_scored, l3_reason = layer3_tension_arc_final(
        l2_scored, cog_config, top_k=top_k
    )
    final_top = l3_scored[:top_k]
    node_l3 = FunnelNode(
        run_id=run_id,
        layer=3,
        stage="tension_arc_final",
        score=final_top[0][0] if final_top else None,
        candidates=[t["template_id"] for _, _, _, t in final_top],
        reason=l3_reason,
        timestamp=timestamp,
    )
    nodes.append(node_l3)
    _emit_jsonl(node_l3, out_handle, verbose)

    # ── 最终推荐摘要 ────────────────────────────────────────────────
    print(_format_hmi_log("INFO", "═" * 50))
    print(_format_hmi_log("RESULT", f"推荐模板 Top-{top_k}:"))
    for rank, (f_score, l2_score, t_score, tpl) in enumerate(final_top, 1):
        print(_format_hmi_log(
            "RESULT",
            f"  #{rank} {tpl['template_id']}: "
            f"final={f_score:.3f}(L2={l2_score:.3f},T={t_score:.3f}) "
            f"«{tpl.get('name','?')}»"
        ))
    print(_format_hmi_log("INFO", "═" * 50))

    return nodes


# ═══════════════════════════════════════════════════════════════════════
# 模板注册表加载
# ═══════════════════════════════════════════════════════════════════════

def load_template_registry(path: str | Path) -> tuple[list, dict]:
    """
    加载 YAML 模板注册表。
    返回: (templates_list, chapter_role_matrix)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"模板注册表不存在: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    templates = raw.get("templates", [])
    matrix = raw.get("chapter_role_matrix", {})
    print(_format_hmi_log("INFO", f"加载模板注册表: {len(templates)} 个模板"))
    return templates, matrix


# ═══════════════════════════════════════════════════════════════════════
# COG 配置验证
# ═══════════════════════════════════════════════════════════════════════

def validate_cog_config(cog: dict) -> list[str]:
    """返回警告消息列表（空=验证通过）。"""
    warnings = []
    if "required_tags" not in cog and "forbidden_tags" not in cog:
        warnings.append("COG配置无标签过滤条件（required_tags/forbidden_tags均为空）")
    if "desired_tension_arcs" not in cog:
        warnings.append("COG配置无张力弧偏好（desired_tension_arcs为空）")
    if not cog.get("chapter_role_weights") and not cog.get("required_tags"):
        warnings.append("COG配置无章节角色权重，将使用均匀权重")
    return warnings


# ═══════════════════════════════════════════════════════════════════════
# CLI 入口 — argparse
# ═══════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cog_diag.py",
        description="PT-047 COG CLI 诊断系统 — 三层漏斗决策过程可视化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", "-i", dest="input",
        help="COG JSON 配置文件路径",
    )
    parser.add_argument(
        "--output", "-o", dest="output",
        help="JSON Lines 输出文件路径（省略则仅输出到 stdout）",
    )
    parser.add_argument(
        "--template-registry", "-t", dest="registry",
        default=str(DEFAULT_TEMPLATE_REGISTRY),
        help=f"模板注册表 YAML 路径（默认: {DEFAULT_TEMPLATE_REGISTRY}）",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="输出完整 JSON Lines 到 stderr",
    )
    parser.add_argument(
        "--validate-template", dest="validate", nargs="?", const="__DEFAULT__",
        help="仅验证模板注册表 YAML（不运行漏斗），默认验证默认路径",
    )
    parser.add_argument(
        "--run-id", "-r", dest="run_id",
        help="手动指定 run_id（用于追踪）",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    run_id = args.run_id or f"COG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # ── 模式: 模板注册表验证 ───────────────────────────────────────
    if args.validate:
        validate_path = DEFAULT_TEMPLATE_REGISTRY if args.validate == "__DEFAULT__" else args.validate
        print(_format_hmi_log("INFO", f"验证模板注册表: {validate_path}"))
        try:
            templates, matrix = load_template_registry(validate_path)
            print(_format_hmi_log("OK", f"验证通过: {len(templates)} 模板, "
                                       f"{len(matrix)} 条亲和度矩阵"))
            for tpl in templates:
                tpl_id = tpl.get("template_id", "?")
                name = tpl.get("name", "?")
                tags = tpl.get("required_tags", [])
                arcs = tpl.get("tension_arc", [])
                print(f"  {tpl_id}: {name} | 标签:{tags} | 张力弧:{arcs}")
        except Exception as e:
            print(_format_hmi_log("ERROR", f"验证失败: {e}"))
            sys.exit(1)
        return

    # ── 主模式: COG 漏斗诊断 ───────────────────────────────────────
    # 1. 加载 COG 配置
    if not args.input:
        print(_format_hmi_log("ERROR", "缺少 --input 参数（使用 --validate-template 可跳过）"))
        sys.exit(1)
    print(_format_hmi_log("INFO", f"[{run_id}] PT-047 COG CLI 诊断系统启动"))
    print(_format_hmi_log("INFO", f"输入配置: {args.input}"))

    if not os.path.exists(args.input):
        print(_format_hmi_log("ERROR", f"COG配置文件不存在: {args.input}"))
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        cog = json.load(f)

    warnings = validate_cog_config(cog)
    for w in warnings:
        print(_format_hmi_log("WARN", w))

    # 2. 加载模板注册表
    try:
        templates, matrix = load_template_registry(args.registry)
    except FileNotFoundError:
        print(_format_hmi_log("ERROR", f"模板注册表不存在: {args.registry}"))
        sys.exit(1)

    # 3. 打开输出文件
    out_handle = sys.stdout
    close_handle = False
    if args.output:
        out_handle = open(args.output, "w", encoding="utf-8")
        close_handle = True
        print(_format_hmi_log("INFO", f"输出文件: {args.output}"))

    try:
        nodes = run_cog_diagnostic(
            cog_config=cog,
            template_registry=templates,
            chapter_affinity=matrix,
            run_id=run_id,
            out_handle=out_handle,
            verbose=args.verbose,
        )
    finally:
        if close_handle:
            out_handle.close()

    # 4. 摘要
    print(_format_hmi_log("INFO", f"[{run_id}] 漏斗完成: {len(nodes)} 个决策节点"))
    print(_format_hmi_log("INFO", "诊断报告已生成。"))


if __name__ == "__main__":
    main()
