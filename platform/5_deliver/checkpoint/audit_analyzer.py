# -*- coding: utf-8 -*-
"""
audit_analyzer.py — SPDT-005 Policy Audit 分析器
===============================================

功能：
  1. 读取 policy_audit.jsonl
  2. 分析 gap_events、severity、content_type 分布
  3. 生成可读报告
  4. 输出：控制台 + 可选 JSON 摘要

使用方式：
  python audit_analyzer.py                    # 全量分析
  python audit_analyzer.py --last 24          # 最近 24h
  python audit_analyzer.py --pipeline PL_xxx  # 单条管线详情
  python audit_analyzer.py --json            # 输出 JSON 摘要

配合 cron 使用（每日 9:00）：
  mavis cron create --every "0 9 * * *" --prompt "cd D:/2_products/media/SPDT-005_MediaContent && python platform/5_deliver/checkpoint/audit_analyzer.py"
"""

from __future__ import annotations

import argparse
import json
import sys
import io
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
AUDIT_LOG = REPO_ROOT / "platform" / "5_deliver" / "checkpoint" / "policy_audit.jsonl"


# ─────────────────────────────────────────────────────────────────
# 分析器
# ─────────────────────────────────────────────────────────────────

class AuditAnalyzer:
    """Policy Audit 分析器"""

    EVENT_TYPE_LABELS = {
        "route_resolved":         "[路由] 类型命中",
        "route_fallback":         "[路由] 回退默认",
        "checkpoint_pass_auto":   "[检查点] 自动通过",
        "checkpoint_pass":        "[检查点] 人工通过",
        "checkpoint_hold":        "[检查点] 暂停待审",
        "checkpoint_rejected":    "[检查点] 拒绝",
        "quality_gate_passed":   "[质量门] 通过",
        "quality_gate_failed":    "[质量门] 失败",
        "stage_failed":           "[阶段] 执行失败",
        "gray_zone_triggered":   "[灰区] 触发",
        "checkpoint_ticket_saved": "[工单] 已创建",
        "gray_zone_ticket_saved": "[工单] 灰区已创建",
        "decision_unmatched":     "[决策] 无匹配规则",
    }

    def __init__(self, log_path: Path = AUDIT_LOG):
        self.log_path = log_path
        self.events: list[dict] = []
        self.load()

    def load(self):
        if not self.log_path.exists():
            return
        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        for line in lines:
            try:
                self.events.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    def filter_window(self, hours: int) -> list[dict]:
        """过滤最近 N 小时的事件"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [e for e in self.events if e.get("timestamp", "") >= cutoff.isoformat()]

    def summarize(self, events: list[dict] | None = None) -> dict:
        """生成统计摘要"""
        evs = events if events is not None else self.events
        if not evs:
            return {"total_events": 0, "gap_events": 0, "error_events": 0}

        gap_events = [e for e in evs if e.get("gap")]
        severities = defaultdict(int)
        type_counts = defaultdict(int)
        stage_counts = defaultdict(int)
        pipelines = set()
        content_types = defaultdict(int)

        for e in evs:
            severities[e.get("severity", "info")] += 1
            type_counts[e.get("event_type", "unknown")] += 1
            stage_counts[e.get("stage", "system")] += 1
            pipelines.add(e.get("pipeline_id", ""))
            ct = e.get("content_type", "")
            if ct:
                content_types[ct] += 1

        # 质量门分数提取
        quality_scores = []
        for e in evs:
            if e.get("event_type") == "quality_gate_passed":
                d = e.get("details", {})
                score = d.get("total_score", 0)
                if score:
                    quality_scores.append(score)

        _avg = round(sum(quality_scores)/len(quality_scores), 1) if quality_scores else 0
        _p90 = round(sorted(quality_scores)[int(len(quality_scores)*0.9)], 1) if quality_scores else 0
        _gap_rate = round(len(gap_events)/len(evs)*100, 1) if evs else 0
        return {
            "total_events": len(evs),
            "gap_events": len(gap_events),
            "gap_rate": _gap_rate,
            "error_events": severities.get("error", 0),
            "warn_events": severities.get("warn", 0),
            "severity_breakdown": dict(severities),
            "event_type_top10": dict(sorted(type_counts.items(), key=lambda x: -x[1])[:10]),
            "stage_breakdown": dict(sorted(stage_counts.items(), key=lambda x: -x[1])),
            "content_type_breakdown": dict(sorted(content_types.items(), key=lambda x: -x[1])),
            "unique_pipelines": len(pipelines),
            "quality_scores": quality_scores,
            "quality_avg": _avg,
            "quality_p90": _p90,
            "time_range": {
                "oldest": min((e.get("timestamp","") for e in evs), default=""),
                "newest": max((e.get("timestamp","") for e in evs), default=""),
            },
        }

    def render_text_report(self, summary: dict, hours: int | None = None) -> str:
        """渲染文本报告"""
        scope = f"最近 {hours}h" if hours else "全量"
        lines = [
            f"{'═' * 56}",
            f"  SPDT-005 Policy Audit 报告  |  {scope}",
            f"{'═' * 56}",
            "",
            f"  事件总数       {summary['total_events']:>6}",
            f"  Gap 事件      {summary['gap_events']:>6}  ({summary['gap_rate']}%)",
            f"  错误事件      {summary['error_events']:>6}",
            f"  警告事件      {summary['warn_events']:>6}",
            f"  独立管线数    {summary['unique_pipelines']:>6}",
            "",
        ]

        # 质量门分数
        if summary["quality_scores"]:
            lines += [
                "  ── 质量门分数 ──────────────────────",
                f"  平均分         {summary['quality_avg']:>6.1f}",
                f"  P90           {summary['quality_p90']:>6.1f}",
                "",
            ]

        # 类型分布
        if summary.get("event_type_top10"):
            lines += ["  ── 事件类型 Top5 ────────────────────", ""]
            for etype, count in list(summary["event_type_top10"].items())[:5]:
                label = self.EVENT_TYPE_LABELS.get(etype, etype)
                bar = "█" * min(count, 30)
                lines.append(f"  {label:<26} {count:>4} {bar}")

        # content_type 分布
        if summary.get("content_type_breakdown"):
            lines += ["", "  ── 内容类型分布 ────────────────────", ""]
            for ct, count in list(summary["content_type_breakdown"].items())[:5]:
                bar = "█" * min(count, 30)
                lines.append(f"  {ct:<28} {count:>4} {bar}")

        # 时间范围
        tr = summary.get("time_range", {})
        if tr.get("oldest"):
            lines += ["", f"  时间范围: {tr['oldest'][:19]} → {tr['newest'][:19]}", ""]

        # Gap 警告
        if summary["gap_events"] > 0:
            lines += [
                "",
                f"  [!] 有 {summary['gap_events']} 个 Gap 事件，需要人工关注。",
                "     运行 audit_analyzer.py --detail 查看详情。",
            ]

        lines += [f"{'═' * 56}", ""]
        return "\n".join(lines)

    def render_json_report(self, summary: dict) -> str:
        return json.dumps(summary, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="SPDT-005 Policy Audit Analyzer")
    parser.add_argument("--last", type=int, default=None, help="只看最近 N 小时")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--pipeline", type=str, default=None, help="查看单条管线详情")
    parser.add_argument("--detail", action="store_true", help="显示 Gap 事件详情")
    args = parser.parse_args()

    analyzer = AuditAnalyzer()

    if args.pipeline:
        events = [e for e in analyzer.events if args.pipeline in e.get("pipeline_id", "")]
        print(f"\n=== Pipeline: {args.pipeline} ===")
        print(f"共 {len(events)} 条事件:\n")
        for e in events:
            ts = e.get("timestamp", "")[:19]
            label = AuditAnalyzer.EVENT_TYPE_LABELS.get(e.get("event_type",""), e.get("event_type",""))
            severity = e.get("severity","")
            gap = "[GAP]" if e.get("gap") else ""
            print(f"  {ts} {gap} {severity:5} {label} | {e.get('action_taken','')}")
        return

    window = args.last
    events = analyzer.filter_window(window) if window else analyzer.events
    summary = analyzer.summarize(events)

    if args.json:
        print(analyzer.render_json_report(summary))
    else:
        print(analyzer.render_text_report(summary, window))

    if args.detail and summary["gap_events"] > 0:
        gaps = [e for e in events if e.get("gap")]
        print(f"\n=== Gap 事件详情（共 {len(gaps)} 条）===\n")
        for e in gaps[:20]:
            ts = e.get("timestamp","")[:19]
            print(f"  {ts} | {e.get('pipeline_id','')} | {e.get('event_type','')}")
            print(f"    {e.get('action_taken','')} | matched: {e.get('matched_rule','')}")
            details = e.get("details", {})
            if details:
                print(f"    details: {str(details)[:120]}")
            print()


if __name__ == "__main__":
    main()
