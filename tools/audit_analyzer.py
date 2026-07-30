#!/usr/bin/env python3
"""
audit_analyzer.py — Policy Audit 自动分析工具
==============================================
扫描 policy_audit.jsonl，输出 gap 报告、覆盖率评分、逐类型建议。

用法:
    python tools/audit_analyzer.py [--days 7] [--output report.md]

输出:
    - Markdown 格式的 gap 分析报告
    - 覆盖率评分（Coverage Score）
    - 按事件类型的统计摘要
    - 每类 gap 的修复建议
"""

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ── 固定配置 ──────────────────────────────────────────────────────────────────

AUDIT_LOG = Path(__file__).parent.parent / "platform" / "5_deliver" / "checkpoint" / "policy_audit.jsonl"

# 每类事件的修复建议模板
GAP_SUGGESTIONS: dict[str, dict] = {
    "route_fallback": {
        "severity": "low",
        "title": "路由未命中（fallback 兜底）",
        "description": "请求的内容类型 / 关键词 / 场景未在 registry 中找到精确匹配，"
                       "系统使用了默认 fallback 规则。这不是错误，但说明 Policy File "
                       "缺少对这类请求的显式路由规则。",
        "fix": "在 content_type_registry.yaml 中添加对应路由条目，"
               "或更新 'keyword_routes' 列表覆盖该关键词。",
        "action": "自动修复（无需人工介入）",
        "auto_fixable": True,
    },
    "route_resolved": {
        "severity": "info",
        "title": "正常路由命中",
        "description": "Pipeline 成功匹配到 registry 中的路由规则，无 gap。",
        "fix": "无需处理。",
        "action": "—",
        "auto_fixable": None,
    },
    "checkpoint_pass_auto": {
        "severity": "info",
        "title": "Checkpoint 自动通过",
        "description": "该 Checkpoint 配置为 skip/auto，管线自动通过，无需人工介入。",
        "fix": "无需处理。",
        "action": "—",
        "auto_fixable": None,
    },
    "checkpoint_hold": {
        "severity": "high",
        "title": "Checkpoint 等待人工确认",
        "description": "该 Checkpoint 无法自动判定，已创建 CHK 工单等待编辑确认。"
                       "这是 Policy 设计的预期行为——但若频繁出现，说明自动化程度偏低。",
        "fix": "评估该场景是否可以模板化：若是偶发型场景，"
               "保持 hold 策略；若是高频场景，考虑在 gray_zone_rules 中增加规则。",
        "action": "需要人工审查",
        "auto_fixable": False,
    },
    "checkpoint_pass": {
        "severity": "info",
        "title": "Checkpoint 人工确认通过",
        "description": "编辑确认后通过，无异常。",
        "fix": "无需处理。",
        "action": "—",
        "auto_fixable": None,
    },
    "quality_gate_passed": {
        "severity": "info",
        "title": "质量门通过",
        "description": "Scorecard 总分超过阈值，管线继续。",
        "fix": "无需处理。",
        "action": "—",
        "auto_fixable": None,
    },
    "quality_gate_failed": {
        "severity": "high",
        "title": "质量门未通过（Veto）",
        "description": "Scorecard 总分低于阈值，内容被 veto。gap=True 表示此次 veto "
                       "是因为 Policy File 的阈值设置与实际内容质量存在偏差。",
        "fix": "1) 检查阈值设置是否合理（factual < 70 是硬 veto，"
               "其他维度的阈值是否过于严格/宽松）。"
               "2) 审查 Scorecard 的评分维度权重是否与业务优先级一致。"
               "3) 若内容质量本身偏低，应改进上游 Render 模块而非调低阈值。",
        "action": "质量团队审查",
        "auto_fixable": False,
    },
    "stage_failed": {
        "severity": "critical",
        "title": "Stage 执行失败",
        "description": "管线某个 Stage（ingest/structure/render/adapt/deliver）执行失败。"
                       "gap=True 说明该失败原因未被 Policy File 覆盖，可能在生产环境"
                       "中导致静默失败。",
        "fix": "1) 定位失败 stage，查看 pipeline_router.py 的异常处理逻辑。"
               "2) 在 gray_zone_rules 或 failure_rules 中增加对应条目。"
               "3) 若是 LLM API 超时/报错，应在 pipeline_router.py 中加入 retry 逻辑。",
        "action": "开发团队排查 + Policy 补充",
        "auto_fixable": False,
    },
    "gray_zone_triggered": {
        "severity": "high",
        "title": "灰区规则触发",
        "description": "内容命中了 gray_zone_rules 中的某条规则，执行了对应动作"
                       "（flag_source_grade / hold_publish / double_verify 等）。"
                       "gap=True 说明触发频率超出预期，或规则本身需要重新评估。",
        "fix": "1) 统计该 gray_zone 规则的触发频率。"
               "2) 若频率过高，考虑调整阈值或细化规则条件。"
               "3) 若规则本身合理，保持现状并增加人工复核资源。",
        "action": "内容策略团队审查",
        "auto_fixable": False,
    },
    "decision_unmatched": {
        "severity": "medium",
        "title": "决策分支未匹配",
        "description": "Policy 决策表中存在未匹配到的分支，系统使用了默认行为。"
                       "gap=True 表示存在未归档的决策路径。",
        "fix": "在 Policy 决策表（docs/0731-Policy决策表.md）中补充该分支的规则，"
               "并在 content_type_registry.yaml 的对应 gray_zone_rules 或 checkpoint "
               "配置中写入明确的处理策略。",
        "action": "Policy 维护者补充规则",
        "auto_fixable": False,
    },
}


@dataclass
class EventStats:
    total: int = 0
    gap_count: int = 0
    by_severity: dict = field(default_factory=lambda: defaultdict(int))
    by_content_type: dict = field(default_factory=lambda: defaultdict(int))
    by_stage: dict = field(default_factory=lambda: defaultdict(int))
    samples: list = field(default_factory=list)


@dataclass
class GapGroup:
    event_type: str
    count: int
    suggestion: dict
    pipeline_ids: list
    sample_event: dict


class AuditAnalyzer:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.events: list[dict] = []
        self.stats: dict[str, EventStats] = defaultdict(EventStats)
        self._total_events = 0
        self._total_gaps = 0
        self._time_range: tuple[str, str] = ("", "")

    def load(self) -> None:
        """加载并解析 JSONL 文件。"""
        if not self.log_path.exists():
            print(f"[!] Audit log not found: {self.log_path}", file=sys.stderr)
            self.events = []
            return

        events = []
        with self.log_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"[!] JSON parse error: {e} | line: {line[:80]}", file=sys.stderr)

        self.events = events
        self._aggregate()

    def _aggregate(self) -> None:
        """按 event_type 聚合统计。"""
        if not self.events:
            return

        timestamps = [e.get("timestamp", "") for e in self.events if e.get("timestamp")]
        if timestamps:
            self._time_range = (timestamps[-1], timestamps[0])

        for e in self.events:
            et = e.get("event_type", "unknown")
            s = self.stats[et]
            s.total += 1
            self._total_events += 1

            if e.get("gap", False):
                s.gap_count += 1
                self._total_gaps += 1

            sev = e.get("severity", "info")
            s.by_severity[sev] += 1

            ct = e.get("content_type", "unknown")
            s.by_content_type[ct] += 1

            stage = e.get("stage", "system")
            s.by_stage[stage] += 1

            # 保留最近 3 条样本
            if len(s.samples) < 3:
                s.samples.append(e)

    @property
    def coverage_score(self) -> float:
        """Policy 覆盖率评分 = 1 - (gap 事件数 / 总事件数)。"""
        if self._total_events == 0:
            return 100.0
        return round((self._total_events - self._total_gaps) / self._total_events * 100, 1)

    def get_gap_groups(self) -> list[GapGroup]:
        """收集所有 gap=True 的事件，按类型分组。"""
        gap_events = [e for e in self.events if e.get("gap", False)]
        grouped: dict[str, list[dict]] = defaultdict(list)
        for e in gap_events:
            grouped[e.get("event_type", "unknown")].append(e)

        result = []
        for et, evs in sorted(grouped.items(), key=lambda x: -len(x[1])):
            suggestion = GAP_SUGGESTIONS.get(et, {
                "severity": "unknown",
                "title": f"未知事件类型：{et}",
                "description": "该事件类型未在 GAP_SUGGESTIONS 中注册。",
                "fix": "在 GAP_SUGGESTIONS 字典中添加对应条目。",
                "action": "未知",
                "auto_fixable": False,
            })
            result.append(GapGroup(
                event_type=et,
                count=len(evs),
                suggestion=suggestion,
                pipeline_ids=[e.get("pipeline_id", "") for e in evs],
                sample_event=evs[0],
            ))
        return result

    def get_pipeline_runs(self) -> dict[str, int]:
        """统计各 content_type 的 pipeline 运行次数。"""
        runs: dict[str, int] = defaultdict(int)
        for e in self.events:
            if e.get("event_type") == "route_resolved":
                ct = e.get("content_type", "unknown")
                runs[ct] += 1
        return dict(sorted(runs.items(), key=lambda x: -x[1]))

    def render_markdown(self) -> str:
        """生成 Markdown 分析报告。"""
        lines = []
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # ── 标题 ────────────────────────────────────────────────────────────────
        lines.append(f"# Policy Audit 分析报告")
        lines.append(f"> 自动生成 | {now}")
        lines.append("")

        # ── 总览卡片 ───────────────────────────────────────────────────────────
        score = self.coverage_score
        score_emoji = "🟢" if score >= 95 else ("🟡" if score >= 80 else "🔴")
        lines.append(f"## 总览")
        lines.append("")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|:---|:---|")
        lines.append(f"| 总事件数 | {self._total_events} |")
        lines.append(f"| Gap 事件数 | {self._total_gaps} |")
        lines.append(f"| **Policy 覆盖率** | **{score_emoji} {score}%** |")
        runs = self.get_pipeline_runs()
        if runs:
            lines.append(f"| Pipeline 运行次数 | {sum(runs.values())} |")
        lines.append("")

        # ── Pipeline 运行统计 ──────────────────────────────────────────────────
        if runs:
            lines.append("## Pipeline 运行统计")
            lines.append("")
            lines.append("| 内容类型 | 运行次数 |")
            lines.append(f"|:---|:---|")
            for ct, cnt in runs.items():
                lines.append(f"| `{ct}` | {cnt} |")
            lines.append("")

        # ── 事件类型分布 ───────────────────────────────────────────────────────
        lines.append("## 事件类型分布")
        lines.append("")
        lines.append("| 事件类型 | 总数 | Gap数 | 覆盖率 | 严重性 |")
        lines.append(f"|:---|---:|---:|---:|:---|")
        for et in sorted(self.stats, key=lambda x: -self.stats[x].total):
            s = self.stats[et]
            cov = round((s.total - s.gap_count) / s.total * 100, 1) if s.total > 0 else 100.0
            sev = GAP_SUGGESTIONS.get(et, {}).get("severity", "info")
            sev_icon = {"info": "ℹ️", "low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(sev, "⚪")
            lines.append(f"| `{et}` | {s.total} | {s.gap_count} | {cov}% | {sev_icon} {sev} |")
        lines.append("")

        # ── Gap 详情（如果有） ─────────────────────────────────────────────────
        gaps = self.get_gap_groups()
        if gaps:
            lines.append("## ⚠️ Gap 事件详情（需处理）")
            lines.append("")
            lines.append(f"> 共发现 **{len(gaps)}** 类 gap 事件，合计 **{self._total_gaps}** 条记录。")
            lines.append("")
            for g in gaps:
                s = g.suggestion
                auto_icon = ""
                if s.get("auto_fixable") is True:
                    auto_icon = " ✅ 自动可修复"
                elif s.get("auto_fixable") is False:
                    auto_icon = " 🔒 需人工处理"

                lines.append(f"### {g.event_type}")
                lines.append(f"- **数量**: {g.count} 条")
                lines.append(f"- **严重性**: {s.get('severity', 'unknown').upper()}{auto_icon}")
                lines.append(f"- **标题**: {s.get('title', '—')}")
                lines.append(f"- **描述**: {s.get('description', '—')}")
                lines.append(f"- **修复建议**: {s.get('fix', '—')}")
                lines.append(f"- **责任方**: {s.get('action', '—')}")
                lines.append(f"- **Pipeline IDs**: `{'`, `'.join(g.pipeline_ids[:5])}`"
                             + (f" … 等{len(g.pipeline_ids)}条" if len(g.pipeline_ids) > 5 else ""))
                lines.append("")
        else:
            lines.append("## ✅ 无 Gap 事件")
            lines.append("")
            lines.append("所有 Policy 决策均命中已知规则，覆盖率 100%。")
            lines.append("")

        # ── 维度分析 ────────────────────────────────────────────────────────────
        # 质量门统计
        qg = self.stats.get("quality_gate_passed")
        qf = self.stats.get("quality_gate_failed")
        if qg or qf:
            lines.append("## 质量门（Scorecard）分析")
            lines.append("")
            if qg:
                lines.append(f"- **通过**: {qg.total} 次")
            if qf:
                lines.append(f"- **未通过（Veto）**: {qf.total} 次")
            lines.append("")

        # Stage 分布
        if self.stats:
            lines.append("## Stage 执行分布")
            lines.append("")
            stage_total: dict[str, int] = defaultdict(int)
            stage_gap: dict[str, int] = defaultdict(int)
            for et, s in self.stats.items():
                for st, cnt in s.by_stage.items():
                    stage_total[st] += cnt
                    if s.gap_count > 0:
                        stage_gap[st] += s.gap_count
            if stage_total:
                lines.append("| Stage | 事件数 | Gap数 |")
                lines.append(f"|:---|---:|---:|")
                for st in ["ingest", "structure", "render", "adapt", "deliver", "system"]:
                    if stage_total.get(st):
                        lines.append(f"| `{st}` | {stage_total[st]} | {stage_gap.get(st, 0)} |")
                lines.append("")

        # ── 时间范围 ────────────────────────────────────────────────────────────
        lines.append("---")
        if self._time_range[0]:
            lines.append(f"**审计日志时间范围**: {self._time_range[0]} ~ {self._time_range[1]}")
        lines.append(f"**报告生成时间**: {now}")

        return "\n".join(lines)

    def print_summary(self) -> None:
        """控制台简洁摘要。"""
        score = self.coverage_score
        score_str = f"Coverage: {score}% ({self._total_events - self._total_gaps}/{self._total_events})"
        gaps = self.get_gap_groups()
        if gaps:
            print(f"⚠️  Gap 发现: {self._total_gaps} 条 | {score_str}")
            for g in gaps:
                auto = " [auto]" if g.suggestion.get("auto_fixable") else ""
                print(f"  [{g.suggestion.get('severity', '?').upper()}] {g.event_type}: {g.count} 条{auto}")
        else:
            print(f"✅ 无 Gap | {score_str}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Policy Audit 分析工具")
    parser.add_argument("--log", type=Path, default=AUDIT_LOG,
                        help=f"审计日志路径（默认: {AUDIT_LOG}）")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="输出 Markdown 报告路径（默认输出到 stdout）")
    parser.add_argument("--json", action="store_true",
                        help="输出 JSON 格式结果（供程序调用）")
    args = parser.parse_args()

    analyzer = AuditAnalyzer(args.log)
    analyzer.load()

    if args.json:
        # 程序化调用：返回结构化结果
        gaps = analyzer.get_gap_groups()
        result = {
            "total_events": analyzer._total_events,
            "total_gaps": analyzer._total_gaps,
            "coverage_score": analyzer.coverage_score,
            "gap_groups": [
                {
                    "event_type": g.event_type,
                    "count": g.count,
                    "severity": g.suggestion.get("severity"),
                    "title": g.suggestion.get("title"),
                    "fix": g.suggestion.get("fix"),
                    "action": g.suggestion.get("action"),
                    "auto_fixable": g.suggestion.get("auto_fixable"),
                    "pipeline_ids": g.pipeline_ids[:5],
                }
                for g in gaps
            ],
            "pipeline_runs": analyzer.get_pipeline_runs(),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 默认：Markdown 报告
    report = analyzer.render_markdown()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
        print(f"\u2705 Report written: {args.output}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(report)

    # 控制台摘要（ASCII-safe）
    score = analyzer.coverage_score
    gaps = analyzer.get_gap_groups()
    if gaps:
        print(f"\n[!] Gaps found: {analyzer._total_gaps}/{analyzer._total_events} ({score}% coverage)")
        for g in gaps:
            auto = " [AUTO]" if g.suggestion.get("auto_fixable") else " [MANUAL]"
            print(f"  [{g.suggestion.get('severity', '?').upper()}] {g.event_type}: {g.count}条{auto}")
    else:
        print(f"\n[OK] No gaps | {score}% coverage")


if __name__ == "__main__":
    main()
