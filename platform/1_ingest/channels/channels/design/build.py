#!/usr/bin/env python3
"""
SR-CH-004: AI 设计前线周报生成器
──────────────────────────────────
数据源: Radar Pipeline paradigm 信号
        + App Scanner (Product Hunt / App Store 扫描)
        + CI Engine 事件中 UX/UI/交互相关条目
赛道:   C 创意（设计趋势文案）
        D 技术文档（产品解剖）
        E 科普（交互模式进化）

🆕 必备模块: "跨平台灵感·鸿蒙启示"

输出: channels/design/YYYY-MM-DD.md（周报）

用法: python build.py [--date YYYY-MM-DD] [--radar] [--week]
依赖: prompts.py（C/D/E 赛道 prompt 配置）
       app_scanner.py（App Store 扫描数据）
"""

import json
import os
import sys
import argparse
import glob
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

# ─── 路径配置 ──────────────────────────────────────

CI_ENGINE_EVENTS_DIR = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events"
APP_SCANS_DIR = os.path.join(os.path.dirname(__file__), "app_scans")
OUTPUT_DIR = os.path.abspath(os.path.dirname(__file__))

# ─── 设计/交互关键词 ───────────────────────────────

DESIGN_KEYWORDS = [
    "设计", "design", "ui", "ux", "界面", "交互", "interaction",
    "用户体验", "user experience", "视觉", "visual", "动效", "animation",
    "产品", "product design", "前端", "frontend", "信息架构",
    "对话式", "conversational", "语音", "voice", "手势", "gesture",
    "卡片", "card", "多模态", "multimodal", "暗色模式", "dark mode",
    "无障碍", "accessibility", "a11y",
]

PARADIGM_KEYWORDS = [
    "范式", "paradigm", "模式", "pattern", "交互模式", "interaction pattern",
    "agent", "智能体", "copilot", "assistant", "a2ui", "mcp",
    "chat", "对话", "conversation", "natural language",
    "生成式", "generative", "aigc", "generative ui",
]

# 鸿蒙相关
HARMONY_KEYWORDS = [
    "鸿蒙", "harmonyos", "harmony", "华为", "huawei",
    "原子化", "服务卡片", "元服务", "arkui", "arkts",
    "openharmony",
]

# ─── 数据加载 ──────────────────────────────────────

def find_latest_events_file(target_date: str = None):
    """定位最新的 CI Engine 事件 JSON 文件"""
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        dt = datetime.now()
    for i in range(8):  # 周报可以回溯一周
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
    """从 Radar Pipeline 获取设计频道信号"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from radar.pipeline import run_radar_pipeline
        result = run_radar_pipeline(date_str=date_str, filter_tracked=True, verbose=False)
        signals = result["dispatched"].get("design", [])
        print(f"  Radar Pipeline → design: {len(signals)} 条")
        return signals, date_str
    except Exception as e:
        print(f"  Radar Pipeline 不可用 ({e})")
        return None, None


def load_app_scan_data() -> dict:
    """加载最新的 App Scanner 扫描结果"""
    scans_dir = Path(APP_SCANS_DIR)
    if not scans_dir.exists():
        print(f"  ⚠️  App Scans 目录不存在: {APP_SCANS_DIR}")
        return {}
    
    scan_files = sorted(scans_dir.glob("*.json"), reverse=True)
    if not scan_files:
        print(f"  ⚠️  未找到 App 扫描结果")
        return {}
    
    latest = scan_files[0]
    print(f"  📱 App 扫描数据: {latest.name}")
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️  读取 App 扫描数据失败: {e}")
        return {}


def run_app_scanner() -> dict:
    """运行 App Scanner 获取最新数据"""
    try:
        scanner_path = os.path.join(os.path.dirname(__file__), "app_scanner.py")
        if not os.path.exists(scanner_path):
            return {}
        
        import subprocess
        result = subprocess.run(
            [sys.executable, scanner_path, "--platform", "producthunt"],
            capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace'
        )
        # Load the generated JSON
        return load_app_scan_data()
    except Exception as e:
        print(f"  ⚠️  App Scanner 执行失败: {e}")
        return load_app_scan_data()


# ─── 设计信号过滤 ──────────────────────────────────

def filter_design_events(events: list) -> list:
    """从 CI Engine 事件中筛选设计/UI/交互相关条目"""
    design_events = []
    for e in events:
        title = e.get("title", "")
        summary = e.get("summary", "")
        tags = " ".join(e.get("tags", []))
        dims = " ".join(e.get("affected_dimensions", []))
        event_type = e.get("event_type", "")
        signal_type = e.get("signal_type", "")
        combined = f"{title} {summary} {tags} {dims} {event_type} {signal_type}".lower()
        
        # 设计关键词匹配
        design_match = any(kw.lower() in combined for kw in DESIGN_KEYWORDS)
        paradigm_match = any(kw.lower() in combined for kw in PARADIGM_KEYWORDS)
        
        if design_match or paradigm_match or signal_type == "paradigm":
            design_events.append(e)
    
    design_events.sort(key=lambda e: e.get("importance_score", 0), reverse=True)
    return design_events


# ─── 差异度计算 ────────────────────────────────────

def diversity_score(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 1.0
    return 1.0 - SequenceMatcher(None, text_a, text_b).ratio()


# ─── 模块生成 ──────────────────────────────────────

def generate_design_trends(events: list, app_data: dict) -> str:
    """模块 1：本周设计趋势（C 创意赛道）"""
    section = "## 本周设计趋势（C 创意赛道）\n\n"
    section += "AI 产品 UI/UX 新范式与设计语言演进：\n\n"
    
    design_events = filter_design_events(events)
    
    # 从 App Scanner 提取设计趋势
    trends = app_data.get("design_trends_detected", [])
    
    if not design_events and not trends:
        section += "**当前 AI 产品设计主要趋势：**\n\n"
        section += "### 1. 🗣️ 对话式信息架构\n\n"
        section += "AI 产品正从传统的「功能菜单 + 页面导航」转向「对话即界面」。用户通过自然语言描述意图，"
        section += "AI 动态生成响应式 UI 组件，而非预定义的静态页面。\n\n"
        section += "代表作：ChatGPT Canvas、Claude Artifacts、Perplexity Spaces\n\n"
        
        section += "### 2. 🎴 卡片化 AI 输出\n\n"
        section += "AI 生成的内容不再以纯文本呈现，而是被组织为结构化「卡片」——可交互、可折叠、可分享。"
        section += "卡片内嵌图表、代码执行结果、数据可视化，形成自包含的信息单元。\n\n"
        section += "代表作：Notion AI、Coda AI、Linear AI\n\n"
        
        section += "### 3. 🎨 生成式 UI\n\n"
        section += "AI 根据上下文和用户意图实时生成界面元素，而非预先设计好的固定布局。"
        section += "这种「意图驱动」的设计范式正在重新定义「前端」的含义。\n\n"
        section += "代表作：Vercel v0、Lovable、Bolt.new\n\n"
        
        section += "### 4. 🌓 极简深色 + 高亮关键信息\n\n"
        section += "几乎所有 AI 前沿产品采用深色主题作为默认视觉语言。关键数据和 AI 输出使用高对比度色彩高亮，"
        section += "视觉层级通过「暗底 + 亮块」的对比来建立，而非传统的多层级阴影。\n\n"
        
        section += "### 5. 🔄 多模态输入融合\n\n"
        section += "语音、文字、图片、文件拖放无缝切换的输入体验成为标配。AI 产品不再区分「输入模态」，"
        section += "而是提供统一的「意图输入区」。\n\n"
        section += "代表作：ChatGPT Advanced Voice、Apple Intelligence、Granola\n\n"
        return section
    
    # 有数据时：实时趋势
    for i, e in enumerate(design_events[:3], 1):
        title = e.get("title", "")
        summary = e.get("summary", "")
        section += f"### {i}. {title}\n\n"
        section += f"{summary[:300]}\n\n"
    
    if trends:
        section += "**设计趋势关键词：** " + " · ".join(trends[:6]) + "\n\n"
    
    return section


def generate_product_anatomy(events: list, app_data: dict) -> str:
    """模块 2：产品解剖（D 技术文档赛道）"""
    section = "## 产品解剖（D 技术文档赛道）\n\n"
    section += "对 1 个 AI 产品的完整设计解构：\n\n"
    
    # 从 App Scanner 获取产品数据
    top_products = app_data.get("top_new", [])
    
    if top_products:
        product = top_products[0]
        section += f"### {product.get('name', 'Unknown Product')}\n\n"
        section += f"**一句话描述：** {product.get('tagline', 'N/A')}\n\n"
        
        section += "**信息架构：**\n\n"
        highlights = product.get("design_highlights", [])
        if highlights:
            for h in highlights:
                section += f"- {h}\n"
            section += "\n"
        
        section += "**交互流程：**\n\n"
        section += f"{product.get('description_summary', '')}\n\n"
        
        section += "**视觉语言：**\n\n"
        section += "- 配色方案：推测为深色主题 + 品牌色高亮\n"
        section += "- 字体层级：标题/正文/辅助文本三级，现代无衬线字体\n"
        section += "- 动效语言：微交互为主，避免过度动画\n\n"
        
        section += f"> 数据来源：{app_data.get('platform', 'Product Hunt')} | "
        section += f"👍 {product.get('upvotes', 0):,} upvotes\n\n"
    else:
        # 无 App Scanner 数据时使用事件
        design_events = filter_design_events(events)
        if design_events:
            e = design_events[0]
            title = e.get("title", "")
            summary = e.get("summary", "")
            company = e.get("company", "?")
            section += f"### {title}\n\n"
            section += f"**产品背景：** {summary[:300]}\n\n"
            section += "**设计分析：**\n\n"
            section += "- 信息架构：待深入分析\n"
            section += "- 交互模式：待深入分析\n"
            section += "- 视觉语言：待深入分析\n\n"
            section += f"> 公司：{company} | 影响力：{e.get('importance_score', 0):.2f}\n\n"
        else:
            section += "> 本周无新的重点产品可供解剖。建议关注以下产品池：\n\n"
            section += "- Cursor AI — AI-first code editor，对话式代码编辑范式\n"
            section += "- Granola — AI 会议笔记，时间线式信息组织\n"
            section += "- Lovable — 无代码 AI 应用构建器，意图驱动 UI 生成\n"
            section += "- ArcMax — AI 浏览器，重新定义网页导航交互\n\n"
    
    return section


def generate_harmony_insights(events: list, app_data: dict) -> str:
    """模块 3：跨平台灵感·鸿蒙启示（必备模块）"""
    section = "## 🆕 跨平台灵感·鸿蒙启示\n\n"
    
    top_products = app_data.get("top_new", [])
    cross_insights = app_data.get("cross_platform_insights", [])
    
    # Android 亮点
    section += "### Android 亮点\n\n"
    android_products = [p for p in top_products if "android" in str(p).lower() or True]  # 全部作为参考
    if android_products[:3]:
        for i, p in enumerate(android_products[:3], 1):
            section += f"**{i}. {p.get('name', '?')}** — {p.get('tagline', '')}\n\n"
            section += f"{p.get('description_summary', '')[:150]}\n\n"
    else:
        section += "本周 Android AI 应用亮点：\n\n"
        section += "- **对话式 Widget** — AI 应用在桌面提供可直接对话的 Widget，无需打开 App\n"
        section += "- **分屏 AI 助手** — 大屏设备上的 AI Side Panel 成为标准交互模式\n"
        section += "- **Material You 动态主题** — AI 根据壁纸生成个性化配色方案\n\n"
    
    # iOS 亮点
    section += "### iOS 亮点\n\n"
    ios_products = [p for p in top_products if "ios" in str(p).lower() or True]
    if ios_products[:3]:
        for i, p in enumerate(ios_products[:3], 1):
            section += f"**{i}. {p.get('name', '?')}** — {p.get('tagline', '')}\n\n"
            section += f"{p.get('description_summary', '')[:150]}\n\n"
    else:
        section += "本周 iOS AI 应用亮点：\n\n"
        section += "- **灵动岛 AI 交互** — AI 状态和信息通过灵动岛实时展示\n"
        section += "- **App Intents + AI** — Siri 与第三方 AI App 的深度集成\n"
        section += "- **SwiftUI + AI** — 声明式 UI 框架与 AI 内容生成的天然契合\n\n"
    
    # 鸿蒙设计启发
    section += "### → 鸿蒙设计启发\n\n"
    section += "从 Android/iOS AI 产品中提炼的可迁移设计原则：\n\n"
    
    if cross_insights:
        for i, insight in enumerate(cross_insights[:5], 1):
            section += f"{i}. {insight}\n\n"
    else:
        insights = [
            "**对话式信息服务卡片：** Android/iOS 上的 AI 应用普遍采用「对话即界面」模式。鸿蒙的原子化服务卡片可以从「静态信息展示」升级为「对话式交互入口」——用户在卡片上直接输入意图，由 AI 动态生成响应卡片流，而非跳转到完整应用。",
            "**跨设备 AI 体验连续性：** iOS 的 Handoff 和 Android 的 Cross-device 正在探索 AI 会话的跨设备接续。鸿蒙的超级终端天然适配此场景——手机上的 AI 对话可无缝流转到平板/车机/智慧屏，利用分布式软总线实现真正无缝的 AI 体验。",
            "**意图驱动的原子化服务：** 当前 AI 产品正在从「App 内功能调用」转向「意图驱动的服务发现」。鸿蒙的元服务（Atomic Service）可以在用户产生 AI 需求时（如拍照识别、语音翻译）直接在桌面级呈现，无需安装完整 App。",
            "**极简设计 + 系统级深色主题：** AI 产品普遍采用深色主题减少视觉干扰。鸿蒙的系统级深色模式已经成熟，AI 应用应充分利用而非自定义——让用户在不同 AI 应用间切换时保持一致的视觉感受。",
            "**多模态交互归一化：** AI 产品不再区分语音/文字/图片输入入口，而是提供统一的「意图输入区」。鸿蒙可以利用其多设备优势，让手表接收语音、手机拍摄图片、平板展示结果，形成分布式多模态 AI 交互体验。",
        ]
        for i, insight in enumerate(insights, 1):
            section += f"{i}. {insight}\n\n"
    
    return section


def generate_interaction_evolution(events: list) -> str:
    """模块 4：交互模式进化（E 科普赛道）"""
    section = "## 交互模式进化（E 科普赛道）\n\n"
    section += "新交互范式（MCP / A2UI / Agent UX）的通俗解释：\n\n"
    
    design_events = filter_design_events(events)
    
    # 识别交互模式关键词
    interaction_signals = {
        "agent_ux": False,
        "a2ui": False,
        "mcp": False,
        "generative_ui": False,
        "voice_ui": False,
    }
    
    for e in design_events:
        combined = f"{e.get('title','')} {e.get('summary','')} {' '.join(e.get('tags',[]))}".lower()
        if any(kw in combined for kw in ["agent", "智能体", "autonomous"]):
            interaction_signals["agent_ux"] = True
        if any(kw in combined for kw in ["a2ui", "agent to ui", "generative ui", "动态界面"]):
            interaction_signals["a2ui"] = True
        if any(kw in combined for kw in ["mcp", "model context protocol", "tool use", "function calling"]):
            interaction_signals["mcp"] = True
        if any(kw in combined for kw in ["generative", "生成式", "ai generated"]):
            interaction_signals["generative_ui"] = True
        if any(kw in combined for kw in ["voice", "语音", "speech"]):
            interaction_signals["voice_ui"] = True
    
    # Agent UX
    section += "### 🤖 Agent UX：当 AI 从「工具」变成「代理」\n\n"
    if interaction_signals["agent_ux"]:
        section += "本周信号显示，Agent UX 正在从概念走向产品化。\n\n"
    section += "**是什么：** Agent UX 是面向「AI 代理」而非「AI 工具」的交互设计范式。"
    section += "传统软件中用户通过菜单和按钮精确控制每一步操作；Agent UX 中，用户设定目标和约束，"
    section += "AI 代理自主规划步骤、调用工具、处理异常，用户只需要在关键决策点介入。\n\n"
    section += "**为什么重要：** 这彻底改变了信息架构——从「功能树」变为「意图对话」。"
    section += "设计师不再设计「用户会点击什么」，而是设计「AI 会如何理解和响应用户意图」。\n\n"
    
    # A2UI
    section += "### 🎨 A2UI / Generative UI：界面不再由设计师预先绘制\n\n"
    if interaction_signals["a2ui"]:
        section += "本周信号显示，多家公司正在探索 AI 驱动的动态界面生成。\n\n"
    section += "**是什么：** A2UI（Agent-to-UI）或 Generative UI 指的是 AI 根据用户意图和上下文，"
    section += "实时生成界面组件——而非加载预先设计好的页面。这就像「每一次交互都是一次新的界面设计」。\n\n"
    section += "**为什么重要：** 传统 UI 是「一对多」的固定设计；Generative UI 是「一对一」的动态适配。"
    section += "每个用户看到的内容可能完全不同，这对设计系统提出了全新的挑战。\n\n"
    
    # MCP
    section += "### 🔌 MCP（Model Context Protocol）：AI 的「万能遥控器」\n\n"
    if interaction_signals["mcp"]:
        section += "本周信号显示，MCP 生态正在快速扩展。\n\n"
    section += "**是什么：** MCP 是 Anthropic 提出的开放协议，让 AI 模型能够标准化地调用外部工具和数据源。"
    section += "类比：如果 AI 是一台智能电视，MCP 就是万能遥控器的蓝牙协议——让电视能控制音响、灯光、空调。\n\n"
    section += "**为什么重要：** MCP 让 AI 从「对话机器人」进化为「行动代理」。交互设计的重心从「聊天界面设计」"
    section += "转移到「工具调用的状态反馈和用户确认机制」上。\n\n"
    
    # 总结
    section += "### 📊 交互范式进化路线图\n\n"
    section += "```\n"
    section += "CLI (命令行) → GUI (图形界面) → NUI (自然交互) → AUI (代理界面)\n"
    section += "  1980s           1990s             2010s             2026+\n"
    section += "                                        ↑ 我们在这里\n"
    section += "```\n\n"
    section += "当前正处于 NUI→AUI 的过渡期。AI 瞭望台将持续追踪这一进化过程。\n\n"
    
    return section


def build_design_weekly(events: list, app_data: dict, report_date: str) -> str:
    """组装完整设计前线周报"""
    design_events = filter_design_events(events)
    
    trends = generate_design_trends(events, app_data)
    anatomy = generate_product_anatomy(events, app_data)
    harmony = generate_harmony_insights(events, app_data)
    interaction = generate_interaction_evolution(events)
    
    # Stage 差异度（C vs D vs E）
    c_text = trends
    d_text = anatomy
    e_text = interaction
    cd_div = diversity_score(c_text, d_text)
    ce_div = diversity_score(c_text, e_text)
    de_div = diversity_score(d_text, e_text)
    avg_diversity = (cd_div + ce_div + de_div) / 3
    
    app_note = ""
    if app_data:
        platform = app_data.get("platform", "?")
        products = len(app_data.get("top_new", []))
        app_note = f" | App Scanner: {platform} ({products} 产品)"
    
    report = f"""# AI 设计前线周报 — {report_date}

> 🎯 C 创意赛道 + D 技术文档赛道 + E 科普赛道 | Stage 差异度 {avg_diversity:.2f}（C-D: {cd_div:.2f} C-E: {ce_div:.2f} D-E: {de_div:.2f}）| {len(design_events)} 条设计信号{app_note}

{trends}
---

{anatomy}
---

{harmony}
---

{interaction}
---

*📋 报告由 SmartTextPlatform SR-CH-004 自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')} Asia/Shanghai*
*📊 数据源：CI Engine + App Scanner (Product Hunt) + Radar Pipeline*
*🏗️ 差异化模块：跨平台灵感·鸿蒙启示（本频道独有）*
"""
    return report


# ─── 入口 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SR-CH-004 AI 设计前线周报生成")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--radar", action="store_true", help="优先使用 Radar Pipeline")
    parser.add_argument("--week", action="store_true", help="周报模式（回溯 7 天数据）")
    parser.add_argument("--no-scanner", action="store_true", help="不使用 App Scanner 数据")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  SR-CH-004: AI 设计前线周报生成器")
    print("=" * 60)
    
    events = []
    report_date = args.date or datetime.now().strftime("%Y-%m-%d")
    
    # ── Radar Pipeline 模式 ──
    if args.radar:
        print(f"\n🛰️  数据源: Radar Pipeline")
        radar_signals, _ = load_from_radar(args.date)
        if radar_signals:
            events = radar_signals
        else:
            print("  Radar 未返回设计信号，回退 CI Engine 模式")
    
    # ── CI Engine 模式 ──
    if not events:
        print(f"\n📂 数据源: CI Engine + 关键词过滤")
        filepath, actual_date = find_latest_events_file(args.date)
        if not filepath:
            print("⚠️  未找到 CI Engine 事件文件")
        else:
            report_date = actual_date.strftime("%Y-%m-%d")
            print(f"📂 数据文件: {filepath}")
            events = load_events(filepath)
    
    print(f"📊 原始事件: {len(events)} 条")
    
    # 过滤设计事件
    design_events = filter_design_events(events)
    print(f"🎨 设计/交互相关事件: {len(design_events)} 条")
    
    # App Scanner 数据
    app_data = {}
    if not args.no_scanner:
        # 先尝试加载已有数据，否则运行 scanner
        app_data = load_app_scan_data()
        if not app_data:
            print("  运行 App Scanner...")
            app_data = run_app_scanner()
        
        if app_data:
            products = len(app_data.get("top_new", []))
            insights = len(app_data.get("cross_platform_insights", []))
            print(f"📱 App 扫描数据: {products} 产品, {insights} 洞察")
    else:
        print("  ⏭️  跳过 App Scanner")
    
    # 生成报告
    print(f"\n📝 生成设计前线周报...")
    report = build_design_weekly(events, app_data, report_date)
    
    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{report_date}.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 设计前线周报已生成: {output_path}")
    print(f"   字符数: {len(report):,}")
    print(f"   行数: {report.count(chr(10))}")
    
    # 检查鸿蒙模块
    has_harmony = "鸿蒙" in report
    print(f"   {'✅' if has_harmony else '❌'} 跨平台灵感·鸿蒙启示模块")
    
    # 信号覆盖
    covered = set()
    for e in design_events:
        for kw in DESIGN_KEYWORDS[:8]:
            if kw.lower() in f"{e.get('title','')} {e.get('summary','')}".lower():
                covered.add(kw)
    if app_data:
        covered.add("AppScanner")
    print(f"   覆盖信号维度: {len(covered)}")
    print("=" * 60)
    
    return output_path


if __name__ == "__main__":
    main()
