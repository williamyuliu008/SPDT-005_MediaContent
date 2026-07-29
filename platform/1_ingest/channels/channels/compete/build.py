#!/usr/bin/env python3
"""
SR-CH-001: AI 竞争态势日报生成器
──────────────────────────────────
读取 CI Engine 每日简报 JSON → STP B 深产/F 观点赛道 → Markdown 日报

数据源: ci-engine/events/
输出:   channels/compete/YYYY-MM-DD.md

用法: python build.py [--date YYYY-MM-DD]
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# ─── 配置 ──────────────────────────────────────────

CI_ENGINE_EVENTS_DIR = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "")  # same dir as build.py
OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)

# 10 家追踪公司（MKT 内阁确认）
TRACKED_COMPANIES = [
    "openai", "google", "microsoft", "anthropic", "nvidia",
    "bytedance", "baidu", "alibaba", "tencent", "perplexity"
]

# importance_score ≥ 0.80 → "重大信号"，其余 → "值得关注"
MAJOR_SIGNAL_THRESHOLD = 0.80

# 公司显示名映射
COMPANY_NAMES = {
    "openai": "OpenAI", "google": "Google DeepMind", "microsoft": "Microsoft",
    "anthropic": "Anthropic", "nvidia": "NVIDIA", "bytedance": "字节跳动",
    "baidu": "百度", "alibaba": "阿里巴巴", "tencent": "腾讯", "perplexity": "Perplexity",
}

COMPANY_DOMAINS = {
    "openai": "大模型/基础研究", "google": "大模型/搜索/云", "microsoft": "云/AI平台/办公",
    "anthropic": "大模型/安全", "nvidia": "AI芯片/硬件", "bytedance": "大模型/应用/推荐",
    "baidu": "大模型/自动驾驶", "alibaba": "云/大模型/开源", "tencent": "大模型/社交/游戏",
    "perplexity": "AI搜索/Agent",
}

DIRECTION_ICONS = {"positive": "📈", "negative": "📉", "neutral": "➡️"}

# ─── 数据加载 ──────────────────────────────────────

def find_latest_events_file(target_date: str = None):
    """定位最新的 CI Engine 事件 JSON 文件"""
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        dt = datetime.now()

    attempts = [dt]
    # 回退最多 3 天
    for i in range(1, 4):
        attempts.append(dt - timedelta(days=i))

    for attempt in attempts:
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
    # 支持直接 list 或 {"events": [...]} 两种格式
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


# ─── 核心逻辑 ──────────────────────────────────────

def classify_events(events: list) -> dict:
    """将事件按类型、公司、赛道分类"""
    model_keywords = ["model", "gpt", "gemini", "claude", "llama", "mistral",
                      "文心", "通义", "混元", "deepseek", "qwen"]
    app_keywords = ["app", "product", "application", "launch", "feature"]

    model_events = []
    app_events = []
    other_events = []

    for e in events:
        title = e.get("title", "").lower()
        summary = e.get("summary", "").lower()
        tags = [t.lower() for t in e.get("tags", [])]
        event_type = e.get("event_type", "").lower()
        combined = title + " " + summary + " " + " ".join(tags) + " " + event_type

        if any(kw in combined for kw in model_keywords):
            model_events.append(e)
        elif any(kw in combined for kw in app_keywords) or event_type in ("product_launch", "feature"):
            app_events.append(e)
        else:
            other_events.append(e)

    # 按公司分组
    by_company = {}
    for e in events:
        company = e.get("company", "unknown").lower()
        by_company.setdefault(company, []).append(e)

    return {
        "model": model_events,
        "app": app_events,
        "other": other_events,
        "by_company": by_company,
    }


def difflib_diversity_score(text_a: str, text_b: str) -> float:
    """计算两段文本的差异度。1.0 = 完全不同，0.0 = 完全相同。"""
    if not text_a or not text_b:
        return 1.0
    similarity = SequenceMatcher(None, text_a, text_b).ratio()
    return 1.0 - similarity


# ─── 报告生成 ──────────────────────────────────────

def generate_major_signals(top_events: list) -> str:
    """模块 1：今日重大信号（B 深产赛道）"""
    section = "## 今日重大信号（B 深产赛道）\n\n"
    section += f"共追踪 {len(TRACKED_COMPANIES)} 家 AI 核心公司，今日捕获重大信号如下：\n\n"

    major = [e for e in top_events if e.get("importance_score", 0) >= MAJOR_SIGNAL_THRESHOLD]

    if not major:
        section += "> ⚠️ 今日无 importance_score ≥ 0.80 的重大信号。以下为排名前 5 的相对重要事件。\n\n"
        major = top_events[:5]

    for i, event in enumerate(major[:5], 1):
        company_key = event.get("company", "unknown").lower()
        company_name = COMPANY_NAMES.get(company_key, company_key.capitalize())
        domain = COMPANY_DOMAINS.get(company_key, "")
        title = event.get("title", "无标题")
        summary = event.get("summary", "暂无详细描述")
        importance = event.get("importance_score", 0)
        direction = event.get("delta", {}).get("direction", "neutral")
        icon = DIRECTION_ICONS.get(direction, "➡️")
        source = event.get("source_url", "N/A")
        dims = ", ".join(event.get("affected_dimensions", []))
        tags = ", ".join(event.get("tags", []))

        section += f"### {i}. {icon} {company_name} · {domain}\n"
        section += f"**{title}**\n\n"
        section += f"{summary}\n\n"
        section += f"> 影响力：{importance:.2f} | 维度：{dims} | 标签：{tags}\n\n"

    return section


def generate_landscape_judgment(top_events: list) -> str:
    """模块 2：格局变化判断（F 观点赛道）"""
    section = "## 格局变化判断（F 观点赛道）\n\n"

    major = [e for e in top_events if e.get("importance_score", 0) >= MAJOR_SIGNAL_THRESHOLD]

    if not major:
        section += "今日信号温和，未出现足以改变竞争格局的重大事件。以下基于现有信号做出谨慎判断。\n\n"
        major = top_events[:5]

    # 统计受影响维度
    dims = {}
    for e in major:
        for d in e.get("affected_dimensions", []):
            dims[d] = dims.get(d, 0) + 1
        for d in e.get("tags", []):
            dims[d] = dims.get(d, 0) + 1

    # 识别竞争信号
    section += "### 核心判断\n\n"

    if "tech" in dims:
        section += "**技术竞争：** 模型能力竞赛持续深化。"
        section += "上下文窗口、推理能力和多模态仍然是区分头部玩家的核心维度。\n\n"
    if "business" in dims:
        section += "**商业模式：** 免费化趋势对中小厂商构成挤压，生态绑定（云+模型+应用）成为竞争壁垒。\n\n"
    if "finance" in dims:
        section += "**资本动态：** AI 领域投资热度维持高位，头部公司持续获得资本青睐。\n\n"

    # 竞争关系变化
    section += "### 竞争关系变化\n\n"
    companies_involved = set(e.get("company", "").lower() for e in major)
    if len(companies_involved) >= 3:
        cnames = [COMPANY_NAMES.get(c, c) for c in list(companies_involved)[:3]]
        section += f"- 今日主要活跃者：{'、'.join(cnames)}\n"
        section += "- 建议关注其直接竞品在 24-48h 内的反应\n\n"

    section += "### 信号解读\n\n"

    for e in major[:3]:
        company = COMPANY_NAMES.get(e.get("company", "").lower(), e.get("company", ""))
        title = e.get("title", "")
        delta = e.get("delta", {}).get("description", "")
        direction = e.get("delta", {}).get("direction", "neutral")

        if direction == "positive":
            signal_reading = "利好信号，可能推动其所在赛道的竞争加速"
        elif direction == "negative":
            signal_reading = "负面信号，建议关注其对相关生态的传导效应"
        else:
            signal_reading = "中性信号，需结合后续发展判断方向"

        section += f"- **{company}**《{title}》→ {signal_reading}。{delta}\n"

    section += "\n"
    return section


def generate_model_layer(model_events: list) -> str:
    """模块 3：模型层动态（B 深产赛道）"""
    section = "## 模型层动态（B 深产赛道）\n\n"

    if not model_events:
        section += "今日无新的模型层动态。各公司旗舰模型处于常规迭代周期内。\n\n"
        return section

    section += "| 公司 | 变化摘要 | 影响评估 |\n"
    section += "|------|----------|----------|\n"

    for e in model_events[:8]:
        company = COMPANY_NAMES.get(e.get("company", "").lower(), e.get("company", ""))
        title = e.get("title", "")[:40]
        direction = e.get("delta", {}).get("direction", "neutral")
        impact = {"positive": "🟢 利好", "negative": "🔴 压力", "neutral": "🟡 观察"}.get(direction, "🟡 观察")
        section += f"| {company} | {title} | {impact} |\n"

    section += "\n"
    return section


def generate_app_breakout(app_events: list, all_events: list) -> str:
    """模块 4：应用层突围（F 观点赛道）"""
    section = "## 应用层突围（F 观点赛道）\n\n"

    candidates = app_events or [e for e in all_events
                                if e.get("event_type") in ("product_launch", "funding")
                                and e.get("importance_score", 0) >= 0.60]

    if not candidates:
        section += "今日无显著的应用层突围信号。AI 原生应用的创新集中在既有方向上的渐进改进。\n\n"
        return section

    for e in candidates[:3]:
        title = e.get("title", "")
        summary = e.get("summary", "")
        delta = e.get("delta", {}).get("description", "")
        company = COMPANY_NAMES.get(e.get("company", "").lower(), e.get("company", ""))

        section += f"### {title}\n\n"
        section += f"{summary}\n\n"

        # 论证为什么值得关注
        section += f"**为什么值得关注：** "

        if e.get("importance_score", 0) >= 0.85:
            section += f"高影响力信号。{delta if delta else '该事件可能改变其所在细分市场的竞争格局。'}"
        elif "frontier" in e.get("tags", []):
            section += "前沿探索性产品，代表了 AI 能力边界的新尝试。"
        elif e.get("event_type") == "funding":
            section += f"资本认可——融资事件往往预示细分赛道的热度上升。"
        else:
            section += f"{delta if delta else '产品创新可能影响用户使用 AI 的习惯和预期。'}"

        section += "\n\n"
        section += f"> 公司：{company} | 影响力：{e.get('importance_score', 0):.2f}\n\n"

    return section


def generate_tomorrow_focus(top_events: list) -> str:
    """模块 5：明日关注（B 深产赛道）"""
    section = "## 明日关注（B 深产赛道）\n\n"

    focus_items = []

    # 规则驱动的明日关注生成
    for e in top_events:
        company = COMPANY_NAMES.get(e.get("company", "").lower(), e.get("company", ""))
        title = e.get("title", "")
        event_type = e.get("event_type", "")

        if event_type == "product_launch" and len(focus_items) < 3:
            focus_items.append(
                f"**{company} 产品反馈追踪**：关注其 {title[:20]}... 发布后的用户反馈和竞品反应。"
            )
        elif event_type == "partnership" and len(focus_items) < 3:
            focus_items.append(
                f"**{company} 合作深化**：关注此次合作的后续落地动作和生态影响。"
            )
        elif event_type == "funding" and len(focus_items) < 3:
            focus_items.append(
                f"**{company} 融资后续**：关注融资后的团队扩张和产品节奏变化。"
            )
        elif event_type == "model_release" and len(focus_items) < 3:
            focus_items.append(
                f"**{company} 模型动态跟踪**：关注其 {title[:20]}... 发布后的基准测试结果和开发者反馈。"
            )

    # 补充通用关注项
    defaults = [
        "**开源动态**：关注 GitHub Trending 上新涌现的 AI 项目，可能预示下一波技术方向。",
        "**政策与监管**：关注各国 AI 监管政策的最新动向，特别是出口管制和技术标准。",
        "**算力供需**：关注 GPU/TPU 供应变化和云服务价格调整信号。",
    ]

    for d in defaults:
        if len(focus_items) >= 5:
            break
        focus_items.append(d)

    # 统一编号：在拼接阶段按序添加序号
    numbered_items = []
    for i, item in enumerate(focus_items[:5], 1):
        numbered_items.append(f"{i}. {item}")

    section += "\n".join(numbered_items) + "\n\n"
    return section


def build_daily_report(events: list, report_date: str) -> str:
    """组装完整日报"""
    sorted_events = sorted(events, key=lambda e: e.get("importance_score", 0), reverse=True)
    classified = classify_events(sorted_events)

    # 生成各模块
    major_signals = generate_major_signals(sorted_events)
    landscape = generate_landscape_judgment(sorted_events)
    model_layer = generate_model_layer(classified["model"])
    app_breakout = generate_app_breakout(classified["app"], sorted_events)
    tomorrow = generate_tomorrow_focus(sorted_events)

    # 计算 Stage 差异度（B vs F 赛道）
    b_text = major_signals + model_layer + tomorrow
    f_text = landscape + app_breakout
    diversity = difflib_diversity_score(b_text, f_text)

    # 拼装
    report = f"""# AI 竞争态势日报 — {report_date}

> 🎯 B 深产赛道 + F 观点赛道 | Stage 差异度 {diversity:.2f} | {len(sorted_events)} 条原始事件

{major_signals}
---

{landscape}
---

{model_layer}
---

{app_breakout}
---

{tomorrow}
---

*📋 报告由 SmartTextPlatform SR-CH-001 自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')} Asia/Shanghai*
*📊 数据源：CI Engine 每日简报 | 追踪 {len(TRACKED_COMPANIES)} 家公司*
"""
    return report


# ─── Radar 对接 ──────────────────────────────────

def load_events_from_radar(target_date: str) -> list:
    """
    从 Radar Pipeline 获取竞争频道信号（替代直接读 CI Engine JSON）。
    
    Radar Pipeline: CI Engine → classify → score → verify → dispatch
    竞争频道取 dispatch.compete（capability + structural 信号）。
    """
    try:
        radar_dir = os.path.join(os.path.dirname(__file__), "..", "..", "radar")
        radar_dir = os.path.abspath(radar_dir)
        project_root = os.path.dirname(radar_dir)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from radar.pipeline import run_radar_pipeline
        
        result = run_radar_pipeline(
            date_str=target_date,
            filter_tracked=True,
            verbose=False,
        )
        
        if result["stats"].get("error"):
            print(f"⚠️  Radar Pipeline 错误: {result['stats']['error']}，回退到 CI Engine 直接模式")
            return None
        
        signals = result["dispatched"].get("compete", [])
        print(f"  来源: Radar Pipeline → compete 频道: {len(signals)} 条")
        
        # Radar Pipeline 已经在事件上标注了 signal_type / dimension_scores / verifiability_level
        # 这些字段对 build_daily_report 是透明的，直接使用即可
        return signals
    
    except ImportError as e:
        print(f"⚠️  无法导入 Radar Pipeline ({e})，回退到 CI Engine 直接模式")
        return None
    except Exception as e:
        print(f"⚠️  Radar Pipeline 异常 ({e})，回退到 CI Engine 直接模式")
        return None


# ─── 入口 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SR-CH-001 AI 竞争态势日报生成")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD，默认今天")
    parser.add_argument("--radar", action="store_true", help="使用 Radar Pipeline 作为数据源（替代直接读 CI Engine JSON）")
    args = parser.parse_args()

    print("=" * 60)
    print("  SR-CH-001: AI 竞争态势日报生成器")
    print("=" * 60)

    tracked = None
    report_date = None

    # ── Radar Pipeline 模式 ──
    if args.radar:
        print(f"\n🛰️  数据源: Radar Pipeline")
        tracked = load_events_from_radar(args.date)
        if tracked is not None:
            # 从 Radar 元信息中获取日期
            from datetime import datetime as dt
            if args.date:
                report_date = args.date
            else:
                report_date = dt.now().strftime("%Y-%m-%d")
    
    # ── CI Engine 直接模式（默认 / Radar 回退）──
    if tracked is None:
        if args.radar:
            print("  回退到 CI Engine 模式...")
        else:
            print(f"\n📂 数据源: CI Engine JSON 直接读取")
        
        # 1. 定位数据
        events_file, actual_date = find_latest_events_file(args.date)
        if not events_file:
            print(f"❌ 未找到 CI Engine 事件文件（搜索日期: {args.date or '今天'}）")
            print(f"   检查路径: {CI_ENGINE_EVENTS_DIR}")
            sys.exit(1)

        report_date = actual_date.strftime("%Y-%m-%d")
        print(f"📂 数据文件: {events_file}")

        # 2. 加载事件
        events = load_events(events_file)
        print(f"📊 原始事件: {len(events)} 条")

        # 3. 过滤 10 家公司
        tracked = [e for e in events if e.get("company", "").lower() in TRACKED_COMPANIES]

    print(f"📅 报告日期: {report_date}")
    print(f"🎯 目标公司事件: {len(tracked)} 条")

    if not tracked:
        print("⚠️  今日无目标公司事件。将使用全部事件生成报告。")
        if not args.radar:
            # 仅在 CI Engine 模式下的回退
            pass
        else:
            print("   但仍无可用事件。")
            sys.exit(0)

    # 4. 事件概览
    by_company = {}
    for e in tracked:
        c = e.get("company", "unknown")
        by_company[c] = by_company.get(c, 0) + 1
    print(f"   覆盖公司: {len(by_company)}/{len(TRACKED_COMPANIES)}")
    for c, count in sorted(by_company.items(), key=lambda x: -x[1]):
        print(f"     {COMPANY_NAMES.get(c, c):20s} {count} 条")

    # 5. 生成报告
    print(f"\n📝 生成报告中...")
    report = build_daily_report(tracked, report_date)

    # 6. 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{report_date}.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 日报已生成: {output_path}")
    print(f"   字符数: {len(report):,}")
    print(f"   行数: {report.count(chr(10))}")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    main()
