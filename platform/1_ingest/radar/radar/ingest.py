#!/usr/bin/env python3
"""
Radar 信号摄入模块 — Ingest
============================
从 CI Engine JSON 加载原始事件，标准化为 Radar 信号格式。

用法:
  from radar.ingest import ingest_ci_engine, load_source_registry
"""

import json
import os
import yaml
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict


# ══════════════════════════════════════════════
# 默认路径配置
# ══════════════════════════════════════════════

CI_ENGINE_EVENTS_DIR = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events"
SOURCE_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "source_registry.yaml")

# 10 家追踪公司
TRACKED_COMPANIES = [
    "openai", "google", "microsoft", "anthropic", "nvidia",
    "bytedance", "baidu", "alibaba", "tencent", "perplexity"
]


def find_latest_events_file(target_date: Optional[str] = None,
                            events_dir: str = CI_ENGINE_EVENTS_DIR) -> Tuple[Optional[str], Optional[datetime]]:
    """定位最新的 CI Engine 事件 JSON 文件"""
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        dt = datetime.now()
    
    for i in range(5):  # 回退最多 5 天
        attempt = dt - timedelta(days=i)
        year_month = attempt.strftime("%Y-%m")
        date_mmdd = attempt.strftime("%m%d")
        filepath = os.path.join(events_dir, year_month, f"{date_mmdd}_extracted.json")
        if os.path.exists(filepath):
            return filepath, attempt
    
    return None, None


def load_events(filepath: str) -> list:
    """加载 CI Engine 事件 JSON，支持 list / {"events": [...]} / 嵌套 dict"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "events" in data:
        return data["events"]
    # 尝试找数组值
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def load_source_registry(path: str = SOURCE_REGISTRY_PATH) -> dict:
    """加载信源注册表"""
    if not os.path.exists(path):
        return {"sources": []}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def ingest_ci_engine(date_str: Optional[str] = None,
                     events_dir: str = CI_ENGINE_EVENTS_DIR,
                     filter_tracked: bool = True) -> Tuple[list, str, dict]:
    """
    从 CI Engine JSON 摄入原始事件。
    
    Args:
        date_str: 指定日期 YYYY-MM-DD，默认今天
        events_dir: CI Engine 事件目录
        filter_tracked: 是否只保留 10 家追踪公司
    
    Returns:
        (events, report_date, meta)
    """
    filepath, actual_date = find_latest_events_file(date_str, events_dir)
    if not filepath:
        return [], "", {"error": f"未找到 CI Engine 事件文件 (date={date_str or 'today'})"}
    
    report_date = actual_date.strftime("%Y-%m-%d")
    events = load_events(filepath)
    
    if filter_tracked:
        events = [e for e in events if e.get("company", "").lower() in TRACKED_COMPANIES]
    
    meta = {
        "source_file": filepath,
        "report_date": report_date,
        "raw_count": len(load_events(filepath)),
        "tracked_count": len(events),
        "companies_covered": len(set(e.get("company", "").lower() for e in events)),
    }
    
    return events, report_date, meta


# ══════════════════════════════════════════════
# CLI 测试
# ══════════════════════════════════════════════

if __name__ == "__main__":
    events, date, meta = ingest_ci_engine()
    print("=" * 60)
    print("  Radar 信号摄入")
    print("=" * 60)
    print(f"日期: {date}")
    print(f"原始事件: {meta.get('raw_count')} 条")
    print(f"目标公司: {meta.get('tracked_count')} 条")
    print(f"覆盖公司: {meta.get('companies_covered')}/10")
    print(f"\n数据源: {meta.get('source_file')}")
    
    # 公司分布
    by_company = {}
    for e in events:
        c = e.get("company", "unknown")
        by_company[c] = by_company.get(c, 0) + 1
    for c, count in sorted(by_company.items(), key=lambda x: -x[1]):
        print(f"  {c:15s} {count} 条")
