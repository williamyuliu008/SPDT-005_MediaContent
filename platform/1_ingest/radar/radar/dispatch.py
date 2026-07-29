#!/usr/bin/env python3
"""
Radar 信号分发模块 — Dispatch
==============================
将标准化信号按 signal_type 路由到目标频道。
同时处理 structural 信号的副本分发（compete + chips）。

分发规则:
  capability    → compete
  structural    → compete (主) + chips (副，如涉及供应链)
  supply_chain  → chips
  ecosystem     → oss
  paradigm      → design
  risk          → (future: public_welfare)

用法:
  from radar.dispatch import dispatch, get_channel_signals
"""

import json
from typing import Dict, List, Optional

# ══════════════════════════════════════════════
# 频道映射
# ══════════════════════════════════════════════

TYPE_TO_CHANNEL = {
    "capability": "compete",
    "structural": "compete",       # 主频道
    "supply_chain": "chips",
    "ecosystem": "oss",
    "paradigm": "design",
    "risk": None,                  # 未来: public_welfare
}

# structural 信号中同时涉及供应链的 tags → 额外分发到 chips
SUPPLY_CHAIN_TAGS = {
    "gpu", "hardware", "chip", "semiconductor", "supply_chain",
    "manufacturing", "blackwell", "grace_blackwell", "h100", "h200", "b200",
    "edge_ai", "compute", "gpu_shortage", "export_control", "china_gpu",
    "产能", "制程", "产能变化", "价格", "特供",
}

CHANNEL_NAMES = {
    "compete": "竞争态势频道",
    "chips": "芯事频道",
    "oss": "开源雷达频道",
    "design": "设计前线频道",
}


def _has_supply_chain_relevance(event: dict) -> bool:
    """检查 structural 事件是否涉及供应链"""
    tags = {t.lower() for t in event.get("tags", [])}
    dims = {d.lower() for d in event.get("affected_dimensions", [])}
    title = event.get("title", "").lower()
    summary = event.get("summary", "").lower()
    
    # 检查 tags 交集
    if tags & SUPPLY_CHAIN_TAGS:
        return True
    
    # 检查文本关键词
    supply_kw = ["芯片", "gpu", "硬件", "制造", "制程", "供应链", "特供"]
    text = title + summary
    for kw in supply_kw:
        if kw in text:
            return True
    
    return False


def dispatch(events: list) -> Dict[str, Dict]:
    """
    信号分发器。
    
    Args:
        events: 已分类+评分+验证的标准化信号列表
    
    Returns:
        {
            "signals": [...],           # 全量信号
            "dispatched": {
                "compete": [...],       # capability + structural
                "chips": [...],         # supply_chain + structural(供应链相关)
                "oss": [...],           # ecosystem
                "design": [...],        # paradigm
            },
            "summary": { ... },         # 分发摘要
        }
    """
    channels = {
        "compete": [],
        "chips": [],
        "oss": [],
        "design": [],
    }
    
    for e in events:
        signal_type = e.get("signal_type", "unclassified")
        channel = TYPE_TO_CHANNEL.get(signal_type)
        
        if channel and channel in channels:
            e_copy = dict(e)
            e_copy["dispatched_to"] = [channel]
            channels[channel].append(e_copy)
        
        # structural 信号额外分发到 chips（如涉及供应链）
        if signal_type == "structural" and _has_supply_chain_relevance(e):
            e_extra = dict(e)
            if "dispatched_to" not in e_extra:
                e_extra["dispatched_to"] = []
            if "chips" not in e_extra["dispatched_to"]:
                e_extra["dispatched_to"].append("chips")
                channels["chips"].append(e_extra)
        
        # 标记原始事件的分发目标
        if "dispatched_to" not in e:
            e["dispatched_to"] = [channel] if channel else []
    
    # 各频道按 importance_score 降序
    for ch in channels:
        channels[ch].sort(key=lambda e: e.get("importance_score", 0), reverse=True)
    
    # 摘要
    summary = {
        "total_signals": len(events),
        "by_channel": {
            ch: {"count": len(channels[ch]), "name": CHANNEL_NAMES.get(ch, ch)}
            for ch in channels
        },
        "unrouted": sum(1 for e in events if not e.get("dispatched_to")),
    }
    
    return {
        "signals": events,
        "dispatched": channels,
        "summary": summary,
    }


def get_channel_signals(dispatch_output: dict, channel: str) -> list:
    """从分发结果中提取指定频道的信号"""
    return dispatch_output.get("dispatched", {}).get(channel, [])


def format_dispatch_summary(dispatch_output: dict) -> str:
    """格式化分发摘要"""
    summary = dispatch_output.get("summary", {})
    lines = [
        "频道分发清单:",
    ]
    for ch, info in summary.get("by_channel", {}).items():
        lines.append(f"  {info['name']:10s} ({ch:8s}): {info['count']:3d} 条")
    lines.append(f"  未路由: {summary.get('unrouted', 0)} 条")
    return "\n".join(lines)


# ══════════════════════════════════════════════
# CLI 测试
# ══════════════════════════════════════════════

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    from radar.signal_taxonomy import classify_batch
    from radar.scoring_rubric import score_batch
    from radar.verifiability import verify_batch
    
    events_path = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events\2026-06\0617_extracted.json"
    if os.path.exists(events_path):
        with open(events_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        # Pipeline
        events = classify_batch(events)
        events = score_batch(events)
        events = verify_batch(events)
        result = dispatch(events)
        
        print("=" * 60)
        print("  Radar 信号分发 — 结果")
        print("=" * 60)
        print(format_dispatch_summary(result))
        
        # 各频道 Top 信号
        for ch, signals in result["dispatched"].items():
            print(f"\n── {CHANNEL_NAMES.get(ch, ch)} (Top 3) ──")
            for i, e in enumerate(signals[:3], 1):
                print(f"  {i}. [{e.get('signal_type', '?'):15s}] {e.get('importance_score', 0):.2f} | {e.get('title', '')[:60]}")
