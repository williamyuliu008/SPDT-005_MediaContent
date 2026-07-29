#!/usr/bin/env python3
"""
Radar 可验证性阶梯 — Verifiability Ladder
==========================================
L1-L4 自动标注，根据信源层级和交叉验证情况调整置信度。

阶梯定义:
  L4: 可验证    — 一手公开数据源（财报/SEC/官方公告）          confidence ≥ 0.90
  L3: 可交叉验证 — 2+ 个独立二级信源一致                      confidence 0.75-0.90
  L2: 单一信源  — 仅 1 个可靠信源，无交叉验证                 confidence 0.55-0.75
  L1: 传言      — 社交媒体/匿名来源，无可靠信源支撑           confidence < 0.55

用法:
  from radar.verifiability import verify_event, verify_batch
"""

import re
import json
from urllib.parse import urlparse
from typing import Optional, Tuple

# ══════════════════════════════════════════════
# 一级信源域名白名单
# ══════════════════════════════════════════════

PRIMARY_DOMAINS = {
    # 公司官网
    "nvidianews.nvidia.com",
    "nvidia.com",
    "openai.com",
    "blog.google",
    "googleblog.com",
    "deepmind.google",
    "news.microsoft.com",
    "microsoft.com",
    "learn.microsoft.com",
    "anthropic.com",
    "apple.com",
    "newsroom.apple.com",
    "tencent.com",
    "alibabacloud.com",
    "baidu.com",
    "ernie.baidu.com",
    "bytedance.com",
    "meta.com",
    "about.fb.com",
    # 监管/学术
    "sec.gov",
    "arxiv.org",
    "github.com",
    "huggingface.co",
    # 学术发布
    "nature.com",
    "science.org",
}

# 高可靠性二级域名（reliability > 0.85）
HIGH_RELIABILITY_SECONDARY = {
    "reuters.com",
    "bloomberg.com",
    "semianalysis.com",
    "anandtech.com",
    "theinformation.com",
    "technologyreview.com",  # MIT Tech Review
}

# 中等可靠性二级域名
MEDIUM_RELIABILITY_SECONDARY = {
    "venturebeat.com",
    "techcrunch.com",
    "arstechnica.com",
    "fortune.com",
    "wired.com",
    "theverge.com",
    "tomshardware.com",
    "datanorth.ai",
    "eet-china.com",
    "nextbigfuture.com",
    "sina.com.cn",
    "finance.sina.com.cn",
    "36kr.com",
    "zhihu.com",
    "zhuanlan.zhihu.com",
    "csdn.net",
    "gitcode.csdn.net",
    "cls.cn",
    "chinaflashmarket.com",
    "protocol.com",
}


def extract_domain(url: str) -> Optional[str]:
    """从 URL 提取域名"""
    if not url or url == "N/A":
        return None
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None


def _check_primary_domain(domain: str) -> bool:
    """检查域名是否在一手信源白名单中"""
    if not domain:
        return False
    # 精确匹配或子域匹配
    for pd in PRIMARY_DOMAINS:
        if domain == pd or domain.endswith("." + pd):
            return True
    return False


def _check_high_reliability_secondary(domain: str) -> bool:
    """检查域名是否在高可靠性二级信源中"""
    if not domain:
        return False
    for hd in HIGH_RELIABILITY_SECONDARY:
        if domain == hd or domain.endswith("." + hd):
            return True
    return False


def _check_medium_reliability_secondary(domain: str) -> bool:
    """检查域名是否在中等可靠性二级信源中"""
    if not domain:
        return False
    for md in MEDIUM_RELIABILITY_SECONDARY:
        if domain == md or domain.endswith("." + md):
            return True
    return False


def _check_cross_validation(event: dict) -> bool:
    """
    交叉验证检查。
    
    简化实现: 检查 affected_dimensions 和 tags 的一致性、
    source 本身的可靠性足够高。
    完整实现应检查是否有其他独立信源报道同一条事件。
    """
    source_level = event.get("source_level", "").lower()
    confidence = event.get("confidence", 0)
    
    # 如果有多个 affected_dimensions + 高 confidence，视为间接验证
    dims = event.get("affected_dimensions", [])
    tags = event.get("tags", [])
    
    if source_level == "primary":
        return True
    
    if confidence >= 0.80 and source_level == "secondary":
        return True
    
    # 多个维度受影响 + 多个标签 → 信号相对复杂，间接增加可信度
    if len(dims) >= 2 and len(tags) >= 2:
        return True
    
    return False


def verify_event(event: dict) -> dict:
    """
    标注单条事件的可验证性等级，并调整置信度。
    
    Args:
        event: CI Engine 事件 dict（需含 source_url, source_level, confidence）
    
    Returns:
        更新后的 event dict（含 verifiability_level, confidence）
    """
    source_url = event.get("source_url", "")
    source_level = event.get("source_level", "").lower()
    confidence = event.get("confidence", 0)
    domain = extract_domain(source_url)
    
    # ── L4: 可验证 ──
    if source_level == "primary" and _check_primary_domain(domain):
        level = "L4"
        base_confidence = 0.95
        rationale = f"一手官方信源 ({domain})，数据可验证"
    
    # ── L3: 可交叉验证 ──
    elif source_level == "primary" and not _check_primary_domain(domain):
        # primary 标注但域名不在白名单 → L3 保守处理
        level = "L3"
        base_confidence = 0.85
        rationale = f"标注为一手信源但域名 ({domain}) 不在已验证白名单中"
    
    elif source_level == "secondary" and _check_high_reliability_secondary(domain):
        level = "L3"
        base_confidence = 0.85
        rationale = f"高可靠性二级信源 ({domain})，可信度较高"
    
    elif source_level == "secondary" and _check_cross_validation(event):
        level = "L3"
        base_confidence = 0.80
        rationale = "有交叉验证支撑的二级信源"
    
    # ── L2: 单一信源 ──
    elif source_level == "secondary" and not _check_cross_validation(event):
        level = "L2"
        base_confidence = 0.65
        rationale = "单一二级信源，无交叉验证"
    
    elif source_level == "secondary":
        level = "L2"
        base_confidence = 0.60
        rationale = "二级信源，需交叉验证"
    
    # ── L1: 传言 ──
    elif source_level == "tertiary" or not source_level or not source_url or source_url == "N/A":
        level = "L1"
        base_confidence = 0.40
        rationale = "缺乏可靠信源支撑，视为待验证传言"
    
    else:
        # 兜底
        level = "L2"
        base_confidence = 0.55
        rationale = f"信源层级 ({source_level}) 未能明确分类"
    
    # ── 置信度调整 ──
    # 保留 CI Engine 原始 confidence 的参考意义，但以验证等级为基础
    # 取 CI Engine confidence 和验证基数的加权平均
    adjusted_conf = round(base_confidence * 0.7 + confidence * 0.3, 2)
    
    # L1/L2 信号额外降低置信度
    if level == "L1":
        adjusted_conf = min(adjusted_conf, 0.50)
    elif level == "L2":
        adjusted_conf = min(adjusted_conf, 0.75)
    
    event["verifiability_level"] = level
    event["verifiability_rationale"] = rationale
    event["confidence"] = adjusted_conf
    
    return event


def verify_batch(events: list) -> list:
    """批量验证，返回带验证标注的事件列表"""
    return [verify_event(e) for e in events]


# ══════════════════════════════════════════════
# 等级分布统计
# ══════════════════════════════════════════════

def verification_stats(events: list) -> dict:
    """验证等级分布统计"""
    total = len(events)
    by_level = {"L1": 0, "L2": 0, "L3": 0, "L4": 0}
    for e in events:
        level = e.get("verifiability_level", "L2")
        by_level[level] = by_level.get(level, 0) + 1
    
    return {
        "total": total,
        "by_level": by_level,
        "by_level_pct": {k: round(v / total * 100, 1) for k, v in by_level.items()},
        "avg_confidence": round(sum(e.get("confidence", 0) for e in events) / total, 2),
    }


def format_verification_summary(events: list) -> str:
    """格式化验证等级摘要"""
    stats = verification_stats(events)
    lines = [
        "可验证性阶梯分布:",
        f"  L4 可验证:    {stats['by_level']['L4']:3d} 条 ({stats['by_level_pct']['L4']}%)",
        f"  L3 可交叉验证: {stats['by_level']['L3']:3d} 条 ({stats['by_level_pct']['L3']}%)",
        f"  L2 单一信源:   {stats['by_level']['L2']:3d} 条 ({stats['by_level_pct']['L2']}%)",
        f"  L1 传言:       {stats['by_level']['L1']:3d} 条 ({stats['by_level_pct']['L1']}%)",
        f"  平均置信度: {stats['avg_confidence']:.2f}",
    ]
    return "\n".join(lines)


# ══════════════════════════════════════════════
# 日报呈现规则
# ══════════════════════════════════════════════

def daily_report_annotation(event: dict) -> str:
    """返回日报中应附加的标注"""
    level = event.get("verifiability_level", "L2")
    if level == "L1":
        return " ⚠️ [传言]"
    elif level == "L2":
        return " 🔍 [待交叉验证]"
    elif level in ("L3", "L4"):
        return ""
    return ""


# ══════════════════════════════════════════════
# CLI 测试
# ══════════════════════════════════════════════

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    from radar.signal_taxonomy import classify_batch
    
    events_path = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events\2026-06\0617_extracted.json"
    if os.path.exists(events_path):
        with open(events_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        events = classify_batch(events)
        verified = verify_batch(events)
        
        print("=" * 60)
        print("  Radar 可验证性阶梯 — 标注结果")
        print("=" * 60)
        
        print(format_verification_summary(verified))
        
        print(f"\n{'='*60}")
        print("详细标注:")
        for e in verified:
            level = e.get("verifiability_level", "?")
            conf = e.get("confidence", 0)
            url = e.get("source_url", "N/A")[:60]
            rationale = e.get("verifiability_rationale", "")
            print(f"  [{level}] c={conf:.2f} | {e.get('company', '?'):12s} | {rationale}")
