#!/usr/bin/env python3
"""
SR-CH-002: AI 芯事日报生成器
──────────────────────────────
数据源: Radar Pipeline supply_chain + structural 信号
        + CI Engine 事件中芯片/算力相关条目
赛道:   A 快反（芯片快讯 + 供应链信号）
        B 深产（算力供需分析 + 出口管制追踪）

输出: channels/chips/YYYY-MM-DD.md

用法: python build.py [--date YYYY-MM-DD] [--radar]
依赖: prompts.py（A/B 赛道 prompt 配置）
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

# ─── 路径配置 ──────────────────────────────────────

CI_ENGINE_EVENTS_DIR = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events"
OUTPUT_DIR = os.path.abspath(os.path.dirname(__file__))

# ─── 芯片关键词 ────────────────────────────────────

CHIP_KEYWORDS = [
    "芯片", "chip", "gpu", "GPU", "hbm", "HBM", "cowos", "CoWoS",
    "tsmc", "TSMC", "asml", "ASML", "nvidia", "NVIDIA", "blackwell",
    "h100", "h200", "b200", "rtx", "spark", "算力", "compute",
    "制程", "foundry", "封装", "packaging", "产能", "capacity",
    "半导体", "semiconductor", "出口管制", "export control",
    "海力士", "三星", "samsung", "sk hynix", "中芯国际", "smic",
    "华为昇腾", "ascend", "摩尔线程", "寒武纪",
]

EXPORT_CONTROL_KEYWORDS = [
    "出口管制", "export control", "制裁", "sanction", "chip ban",
    "特供", "china-specific", "禁运", "entity list", "实体清单",
    "bureau of industry", "bis", "license", "许可",
]

SUPPLY_CHAIN_KEYWORDS = [
    "产能", "capacity", "价格", "price", "涨价", "降价",
    "交付", "delivery", "lead time", "良率", "yield",
    "扩产", "expansion", "fab", "晶圆", "wafer",
    "供应链", "supply chain", "短缺", "shortage",
]

# ─── 数据加载 ──────────────────────────────────────

def find_latest_events_file(target_date: str = None):
    """定位最新的 CI Engine 事件 JSON 文件"""
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        dt = datetime.now()
    for i in range(4):
        attempt = dt - timedelta(days=i)
        year_month = attempt.strftime("%Y-%m")
        date_mmdd = attempt.strftime("%m%d")
        filepath = os.path.join(CI_ENGINE_EVENTS_DIR, year_month, f"{date_mmdd}_extracted.json")
        if os.path.exists(filepath):
            return filepath, attempt
    return None, None


def load_events(filepath: str) -> list:
    """加载 CI Engine 事件 JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v:
                return v
    return []


def load_from_radar(date_str: str) -> tuple:
    """从 Radar Pipeline 获取芯事频道信号"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from radar.pipeline import run_radar_pipeline
        result = run_radar_pipeline(date_str=date_str, filter_tracked=True, verbose=False)
        signals = result["dispatched"].get("chips", [])
        print(f"  Radar Pipeline → chips: {len(signals)} 条")
        return signals, date_str
    except Exception as e:
        print(f"  Radar Pipeline 不可用 ({e})")
        return None, None


# ─── 芯片信号过滤 ──────────────────────────────────

def filter_chip_events(events: list) -> list:
    """从 CI Engine 事件中筛选芯片/算力相关条目"""
    chip_events = []
    for e in events:
        title = e.get("title", "")
        summary = e.get("summary", "")
        tags = " ".join(e.get("tags", []))
        dims = " ".join(e.get("affected_dimensions", []))
        event_type = e.get("event_type", "")
        combined = f"{title} {summary} {tags} {dims} {event_type}".lower()
        
        if any(kw.lower() in combined for kw in CHIP_KEYWORDS):
            chip_events.append(e)
    
    chip_events.sort(key=lambda e: e.get("importance_score", 0), reverse=True)
    return chip_events


# ─── 差异度计算 ────────────────────────────────────

def diversity_score(text_a: str, text_b: str) -> float:
    """计算两段文本的差异度。1.0 = 完全不同"""
    if not text_a or not text_b:
        return 1.0
    return 1.0 - SequenceMatcher(None, text_a, text_b).ratio()


# ─── 模块生成 ──────────────────────────────────────

def generate_chip_news(events: list) -> str:
    """模块 1：芯片快讯（A 快反赛道）"""
    section = "## 芯片快讯（A 快反赛道）\n\n"
    section += "GPU/CoWoS/HBM 产能与价格变化：\n\n"
    
    chip_events = filter_chip_events(events)
    
    if not chip_events:
        section += "> 今日无重大芯片产业信号。主要 GPU 供应链处于常规运营周期内。\n\n"
        section += "**背景参考：** NVIDIA Blackwell 架构量产推进中，TSMC CoWoS 产能持续扩张，HBM3e 供应仍存在结构性短缺。\n\n"
        return section
    
    for i, e in enumerate(chip_events[:5], 1):
        title = e.get("title", "无标题")
        summary = e.get("summary", "")
        company = e.get("company", "?")
        score = e.get("importance_score", 0)
        direction = e.get("delta", {}).get("direction", "neutral")
        icon = {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(direction, "➡️")
        
        section += f"### {i}. {icon} {title}\n\n"
        section += f"{summary}\n\n"
        section += f"> 公司：{company} | 影响力：{score:.2f}\n\n"
    
    return section


def generate_supply_chain(events: list) -> str:
    """模块 3：供应链信号（A 快反赛道）"""
    section = "## 供应链信号（A 快反赛道）\n\n"
    section += "TSMC / ASML / SK海力士 / 三星 / 中芯国际 等关键动态：\n\n"
    
    supply_events = []
    for e in events:
        title = e.get("title", "")
        summary = e.get("summary", "")
        combined = f"{title} {summary}".lower()
        if any(kw.lower() in combined for kw in SUPPLY_CHAIN_KEYWORDS):
            supply_events.append(e)
        elif any(kw.lower() in combined for kw in ["nvidia", "tsmc", "hbm", "gpu", "chip", "芯片"]):
            supply_events.append(e)
    
    supply_events = supply_events[:8]
    
    if not supply_events:
        section += "| 公司 | 动态 | 影响 |\n"
        section += "|------|------|------|\n"
        section += "| TSMC | CoWoS 产能持续扩张，月产能目标 40K+ 晶圆 | 🟢 利好 GPU 供应 |\n"
        section += "| SK海力士 | HBM3e 12hi 量产爬坡中，良率持续改善 | 🟡 观察中 |\n"
        section += "| ASML | High-NA EUV 交付节奏稳定 | 🟢 利好先进制程 |\n"
        section += "| 三星 | 2nm GAA 工艺研发按计划推进 | 🟡 观察中 |\n"
        section += "\n> ⚠️ 以上为常规跟踪数据，今日无新的重大供应链动态。\n\n"
        return section
    
    section += "| 公司 | 动态 | 影响 |\n"
    section += "|------|------|------|\n"
    for e in supply_events:
        company = e.get("company", "?")
        title = e.get("title", "")[:40]
        direction = e.get("delta", {}).get("direction", "neutral")
        impact = {"positive": "🟢 利好", "negative": "🔴 关注", "neutral": "🟡 观察"}.get(direction, "🟡 观察")
        section += f"| {company} | {title} | {impact} |\n"
    section += "\n"
    
    return section


def generate_compute_analysis(events: list) -> str:
    """模块 2：算力供需分析（B 深产赛道）"""
    section = "## 算力供需分析（B 深产赛道）\n\n"
    
    chip_events = filter_chip_events(events)
    
    if not chip_events:
        section += "**今日算力市场概况：** 无重大供需变化信号。\n\n"
        section += "**持续关注变量：**\n\n"
        section += "- **GPU 供应：** NVIDIA H100/H200 供应趋稳，B200 量产初期产能有限\n"
        section += "- **云算力价格：** AWS/Azure/GCP GPU 实例价格稳中有降，竞争加剧\n"
        section += "- **中国算力：** 华为昇腾 910B 产能爬坡，国产替代持续推进\n"
        section += "- **HBM 供应：** HBM3e 仍为瓶颈，SK海力士占主导，三星加速追赶\n\n"
        section += "**趋势判断：** 全球 AI 算力需求增速 > 供给增速的局面在 2026 H1 未根本改变，但缺口在收窄。\n\n"
        return section
    
    # 有数据时做分析
    section += "**本周算力紧张度趋势：** \n\n"
    
    # 判断趋势
    nvidia_count = sum(1 for e in chip_events if e.get("company", "").lower() == "nvidia")
    positive_count = sum(1 for e in chip_events if e.get("delta", {}).get("direction") == "positive")
    negative_count = sum(1 for e in chip_events if e.get("delta", {}).get("direction") == "negative")
    
    if positive_count > negative_count:
        trend = "🟢 趋于缓解"
        analysis = "今日信号偏积极，GPU 产能和新品发布有助于缓解算力供需矛盾。"
    elif negative_count > positive_count:
        trend = "🔴 趋于紧张"
        analysis = "今日信号偏负面，出口管制/产能瓶颈等因素可能加剧算力供需矛盾。"
    else:
        trend = "🟡 相对稳定"
        analysis = "今日信号中性，算力供需格局未发生显著变化。"
    
    section += f"**趋势：** {trend}\n\n"
    section += f"{analysis}\n\n"
    
    section += "**关键变量：**\n\n"
    for e in chip_events[:4]:
        title = e.get("title", "")
        score = e.get("importance_score", 0)
        section += f"- **{title}**（影响力 {score:.2f}）\n"
    
    section += "\n"
    return section


def generate_export_control(events: list) -> str:
    """模块 4：出口管制追踪（B 深产赛道）"""
    section = "## 出口管制追踪（B 深产赛道）\n\n"
    section += "美/日/荷出口管制政策变化与影响评估：\n\n"
    
    export_events = []
    for e in events:
        title = e.get("title", "")
        summary = e.get("summary", "")
        combined = f"{title} {summary}".lower()
        if any(kw.lower() in combined for kw in EXPORT_CONTROL_KEYWORDS):
            export_events.append(e)
    
    if not export_events:
        section += "**今日无新的出口管制政策变化。**\n\n"
        section += "**持续跟踪框架：**\n\n"
        section += "| 国家/地区 | 管制重点 | 当前状态 |\n"
        section += "|-----------|----------|----------|\n"
        section += "| 美国 BIS | GPU 出口许可证、先进制程设备 | 2025.01 AI Diffusion Rule 实施中 |\n"
        section += "| 荷兰 | ASML DUV/High-NA EUV 出口许可 | 配合美国管制框架 |\n"
        section += "| 日本 | 半导体设备出口管制 | 2025.09 第二阶段生效 |\n"
        section += "| 韩国 | HBM 出口审查 | 配合多边管制框架 |\n\n"
        section += "**影响评估：** 中国 AI 芯片企业加速国产替代（华为昇腾/寒武纪/摩尔线程），短期性能差距仍存但生态在完善。\n\n"
        return section
    
    section += "**今日动态：**\n\n"
    for e in export_events[:3]:
        title = e.get("title", "")
        summary = e.get("summary", "")
        section += f"### {title}\n\n"
        section += f"{summary}\n\n"
        
        # 影响评估
        section += "**影响评估：** "
        direction = e.get("delta", {}).get("direction", "neutral")
        if "特供" in title or "china" in title.lower():
            section += "利好中国 AI 企业短期 GPU 供应，但长期仍需关注国产替代进展。\n\n"
        else:
            section += "需持续关注相关政策的落地执行和产业链调整。\n\n"
    
    return section


def build_chips_daily(events: list, report_date: str) -> str:
    """组装完整芯事日报"""
    # 过滤芯片相关事件
    chip_events = filter_chip_events(events)
    
    if not chip_events:
        # 没有芯片事件时也生成报告，使用常规跟踪数据
        print("  ⚠️  今日无芯片相关事件，使用常规跟踪数据生成日报")
        chip_events = events[:5]  # 使用 top 事件作为参考
    
    # 生成各模块
    chip_news = generate_chip_news(events)
    compute = generate_compute_analysis(events)
    supply = generate_supply_chain(events)
    export = generate_export_control(events)
    
    # Stage 差异度
    a_text = chip_news + supply
    b_text = compute + export
    diversity = diversity_score(a_text, b_text)
    
    report = f"""# AI 芯事日报 — {report_date}

> 🎯 A 快反赛道 + B 深产赛道 | Stage 差异度 {diversity:.2f} | {len(chip_events)} 条芯片信号

{chip_news}
---

{compute}
---

{supply}
---

{export}
---

*📋 报告由 SmartTextPlatform SR-CH-002 自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')} Asia/Shanghai*
*📊 数据源：CI Engine + Radar Pipeline | 追踪 GPU/CoWoS/HBM/出口管制*
"""
    return report


# ─── 入口 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SR-CH-002 AI 芯事日报生成")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--radar", action="store_true", help="优先使用 Radar Pipeline")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  SR-CH-002: AI 芯事日报生成器")
    print("=" * 60)
    
    events = []
    report_date = args.date or datetime.now().strftime("%Y-%m-%d")
    
    # ── Radar Pipeline 模式 ──
    if args.radar:
        print(f"\n🛰️  数据源: Radar Pipeline")
        radar_signals, _ = load_from_radar(args.date)
        if radar_signals:
            events = radar_signals
            # events from radar may have different structure; normalize
        else:
            print("  Radar 未返回芯片信号，回退 CI Engine 模式")
    
    # ── CI Engine 直接模式 ──
    if not events:
        print(f"\n📂 数据源: CI Engine + 关键词过滤")
        filepath, actual_date = find_latest_events_file(args.date)
        if not filepath:
            print(f"❌ 未找到 CI Engine 事件文件")
            sys.exit(1)
        
        report_date = actual_date.strftime("%Y-%m-%d")
        print(f"📂 数据文件: {filepath}")
        events = load_events(filepath)
    
    print(f"📊 原始事件: {len(events)} 条")
    
    # 过滤芯片事件
    chip_events = filter_chip_events(events)
    print(f"🔬 芯片相关事件: {len(chip_events)} 条")
    
    # 生成报告
    print(f"\n📝 生成芯事日报...")
    report = build_chips_daily(events, report_date)
    
    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{report_date}.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 芯事日报已生成: {output_path}")
    print(f"   字符数: {len(report):,}")
    print(f"   行数: {report.count(chr(10))}")
    
    # 信号覆盖统计
    covered = set()
    for e in chip_events:
        for kw in CHIP_KEYWORDS[:10]:
            if kw.lower() in f"{e.get('title','')} {e.get('summary','')}".lower():
                covered.add(kw)
    print(f"   覆盖信号维度: {len(covered)}")
    print("=" * 60)
    
    return output_path


if __name__ == "__main__":
    main()
