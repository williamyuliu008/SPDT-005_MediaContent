#!/usr/bin/env python3
"""
Radar Pipeline 主控 — Pipeline
===============================
整合全部 Radar 模块: ingest → classify → score → verify → dispatch

用法:
  python radar/pipeline.py                          # 运行今天
  python radar/pipeline.py --date 2026-06-17        # 指定日期
  python radar/pipeline.py --output report.json     # 输出 JSON

输出:
  - 标准化信号 JSON
  - 频道分发清单
  - 管道统计摘要
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from radar.ingest import ingest_ci_engine, load_source_registry
from radar.signal_taxonomy import classify_batch, classification_stats
from radar.scoring_rubric import score_batch, format_score_detail
from radar.verifiability import verify_batch, verification_stats, format_verification_summary
from radar.dispatch import dispatch, format_dispatch_summary

# ══════════════════════════════════════════════
# Pipeline
# ══════════════════════════════════════════════

def run_radar_pipeline(date_str: str = None,
                       events_dir: str = None,
                       filter_tracked: bool = True,
                       verbose: bool = True) -> dict:
    """
    Radar Pipeline 全流程。
    
    1. ingest  — 从 CI Engine JSON 摄入原始事件
    2. classify— 信号分类（6 种类型）
    3. score   — 按类型拆维评分，加权聚合
    4. verify  — 可验证性 L1-L4 标注，置信度调整
    5. dispatch— 按信号类型路由到目标频道
    
    Args:
        date_str:      日期 YYYY-MM-DD，默认今天
        events_dir:    CI Engine 事件目录
        filter_tracked:是否只保留 10 家追踪公司
    
    Returns:
        {
            "meta": {...},          # 管道元信息
            "signals": [...],       # 标准化信号列表
            "dispatched": {...},    # {"compete": [...], "chips": [...], ...}
            "stats": {...},         # 统计摘要
        }
    """
    t_start = datetime.now()
    
    # ═══ Step 1: Ingest ═══
    if verbose:
        print("[1/5] 信号摄入 (Ingest)...")
    
    ingest_kwargs = {"date_str": date_str, "filter_tracked": filter_tracked}
    if events_dir:
        ingest_kwargs["events_dir"] = events_dir
    events, report_date, ingest_meta = ingest_ci_engine(**ingest_kwargs)
    
    if not events:
        return {
            "meta": ingest_meta,
            "signals": [],
            "dispatched": {},
            "stats": {"error": "No events found"},
        }
    
    raw_count = len(events)
    if verbose:
        print(f"  摄入 {raw_count} 条原始事件")
        companies = set(e.get("company", "?").lower() for e in events)
        print(f"  覆盖 {len(companies)}/10 家公司: {', '.join(sorted(companies))}")
    
    # ═══ Step 2: Classify ═══
    if verbose:
        print("[2/5] 信号分类 (Classify)...")
    
    events = classify_batch(events)
    cls_stats = classification_stats(events)
    
    if verbose:
        uncl = cls_stats.get("unclassified", 0)
        print(f"  已分类: {cls_stats['total'] - uncl}/{cls_stats['total']}")
        print(f"  未分类: {uncl}")
        for st, count in cls_stats.get("by_type", {}).items():
            if count > 0:
                print(f"    {st:20s} {count:3d} 条")
    
    # ═══ Step 3: Score ═══
    if verbose:
        print("[3/5] 信号评分 (Score)...")
    
    events = score_batch(events)
    scores = [e.get("importance_score", 0) for e in events]
    
    if verbose:
        print(f"  最高分: {max(scores):.2f} | 最低分: {min(scores):.2f} | 平均分: {sum(scores)/len(scores):.2f}")
        print(f"  ≥ 0.80 高分: {sum(1 for s in scores if s >= 0.80)} 条")
    
    # ═══ Step 4: Verify ═══
    if verbose:
        print("[4/5] 验证标注 (Verify)...")
    
    events = verify_batch(events)
    verif_stats = verification_stats(events)
    
    if verbose:
        print(f"  L4: {verif_stats['by_level']['L4']} | L3: {verif_stats['by_level']['L3']} | "
              f"L2: {verif_stats['by_level']['L2']} | L1: {verif_stats['by_level']['L1']}")
        print(f"  平均置信度: {verif_stats['avg_confidence']:.2f}")
    
    # ═══ Step 5: Dispatch ═══
    if verbose:
        print("[5/5] 信号分发 (Dispatch)...")
    
    dispatch_result = dispatch(events)
    
    if verbose:
        for ch, sigs in dispatch_result["dispatched"].items():
            print(f"  → {ch}: {len(sigs)} 条信号")
    
    # ═══ Assembly ═══
    t_end = datetime.now()
    elapsed = (t_end - t_start).total_seconds()
    
    result = {
        "meta": {
            "pipeline_version": "2a.0",
            "ran_at": t_end.isoformat(),
            "report_date": report_date,
            "elapsed_seconds": round(elapsed, 2),
            "source_file": ingest_meta.get("source_file", ""),
        },
        "signals": events,
        "dispatched": dispatch_result["dispatched"],
        "stats": {
            "ingest": ingest_meta,
            "classification": cls_stats,
            "verifiability": verif_stats,
            "dispatch": dispatch_result["summary"],
            "scores": {
                "max": round(max(scores), 2),
                "min": round(min(scores), 2),
                "mean": round(sum(scores) / len(scores), 2),
                "high_count": sum(1 for s in scores if s >= 0.80),
                "mid_count": sum(1 for s in scores if 0.60 <= s < 0.80),
                "low_count": sum(1 for s in scores if s < 0.60),
            },
        },
    }
    
    if verbose:
        print(f"\n[OK] Pipeline 完成 ({elapsed:.1f}s)")
    
    return result


# ══════════════════════════════════════════════
# 格式化输出
# ══════════════════════════════════════════════

def print_full_report(result: dict):
    """打印完整的 Pipeline 运行报告"""
    print("\n" + "=" * 70)
    print("  🛰️  Radar Pipeline 运行报告")
    print("=" * 70)
    
    meta = result["meta"]
    stats = result["stats"]
    
    print(f"\n📅 报告日期: {meta['report_date']}")
    print(f"⏱️  耗时: {meta['elapsed_seconds']}s")
    print(f"📂 数据源: {os.path.basename(meta.get('source_file', ''))}")
    
    # ── 分类 ──
    print(f"\n── 信号分类 ──")
    cls = stats["classification"]
    for st in ["capability", "structural", "supply_chain", "ecosystem", "paradigm", "risk", "unclassified"]:
        count = cls.get("by_type", {}).get(st, 0)
        if count > 0:
            print(f"  {st:20s} {count:3d} 条 ({cls.get('by_type_pct', {}).get(st, 0)}%)")
    print(f"  规则覆盖率: {cls.get('accuracy_estimate', 0)}%")
    
    # ── 验证 ──
    print(f"\n── 可验证性分布 ──")
    verif = stats["verifiability"]
    for lvl in ["L4", "L3", "L2", "L1"]:
        count = verif["by_level"].get(lvl, 0)
        if count > 0:
            print(f"  {lvl}: {count} 条 ({verif['by_level_pct'].get(lvl, 0)}%)")
    print(f"  平均置信度: {verif['avg_confidence']:.2f}")
    
    # ── 评分样例 ──
    print(f"\n── 评分维度分解样例（Top 3）──")
    signals = sorted(result["signals"], key=lambda e: e.get("importance_score", 0), reverse=True)
    for i, e in enumerate(signals[:3], 1):
        print(f"\n样例 {i}:")
        print(format_score_detail(e))
    
    # ── 分发 ──
    print(f"\n── 频道分发清单 ──")
    print(format_dispatch_summary({"summary": result["stats"]["dispatch"]}))
    
    print(f"\n{'=' * 70}")


def save_results(result: dict, output_path: str):
    """保存 Pipeline 完整结果到 JSON"""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    # 序列化（处理 datetime）
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=default_serializer)
    
    print(f"\n💾 结果已保存: {output_path}")


# ══════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🛰️  Radar Pipeline — 信号摄入→分类→评分→验证→分发",
    )
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD，默认今天")
    parser.add_argument("--output", type=str, help="输出 JSON 文件路径")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    parser.add_argument("--all-companies", action="store_true", help="不按 10 家过滤")
    args = parser.parse_args()
    
    result = run_radar_pipeline(
        date_str=args.date,
        filter_tracked=not args.all_companies,
        verbose=not args.quiet,
    )
    
    if result["stats"].get("error"):
        print(f"❌ {result['stats']['error']}")
        sys.exit(1)
    
    print_full_report(result)
    
    if args.output:
        save_results(result, args.output)
    
    return result


if __name__ == "__main__":
    main()
