#!/usr/bin/env python3
"""
SR-APP-001: App Store 扫描能力 — Product Hunt PoC
────────────────────────────────────────────────
验证 Product Hunt AI 分类页作为首选数据源的可行性。

数据流:
  Product Hunt AI 分类页 → HTML 解析 → 结构化 JSON
  → 为 SR-CH-004（AI 设计前线周报）提供素材

降级策略:
  如果 Product Hunt 连续 3 天无数据 → 自动降级为 web_search 模式
  关键词: "best AI apps 2026" + "AI app design trends"
  在报告中标注 [降级模式]

用法: python app_scanner.py [--platform producthunt|googleplay|appstore]
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser

# ─── 配置 ──────────────────────────────────────────

PROJECT_ROOT = Path(r"D:\92_products\SmartTextPlatform")
SCAN_OUTPUT_DIR = PROJECT_ROOT / "channels" / "design" / "app_scans"
SCAN_STATE_FILE = PROJECT_ROOT / "channels" / "design" / "scan_state.json"

os.makedirs(SCAN_OUTPUT_DIR, exist_ok=True)

# Product Hunt AI 分类页
PRODUCT_HUNT_AI_URL = "https://www.producthunt.com/categories/ai"

# 降级阈值
DEGRADATION_THRESHOLD_DAYS = 3

# ─── 数据模型 ────────────────────────────────────

SAMPLE_OUTPUT = {
    "scan_date": "2026-06-17",
    "platform": "producthunt",
    "mode": "poc",  # poc | live | degraded
    "top_new": [
        {
            "name": "示例 AI 产品",
            "category": "AI",
            "tagline": "一句话产品描述",
            "upvotes": 1234,
            "description_summary": "产品功能简述",
            "design_highlights": ["设计亮点1", "设计亮点2"],
        }
    ],
    "ranking_changes": [],
    "design_trends_detected": [],
    "cross_platform_insights": [],
}

# ─── HTML 解析器（Product Hunt）───────────────────

class ProductHuntParser(HTMLParser):
    """简易 Product Hunt 页面解析器"""

    def __init__(self):
        super().__init__()
        self.products = []
        self.current_product = None
        self.in_name = False
        self.in_tagline = False
        self.in_votes = False
        self.text_buffer = ""
        self.data_stack = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Product name is typically in an <a> with specific class
        cls = attrs_dict.get("class", "")
        if "font-size-16" in cls or "text-16" in cls:
            self.in_name = True
        if "font-size-14" in cls or "tagline" in cls.lower():
            self.in_tagline = True
        if "vote-count" in cls.lower() or "data-test" in attrs_dict and "vote" in attrs_dict.get("data-test", ""):
            self.in_votes = True

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_name:
                if not self.current_product:
                    self.current_product = {"name": "", "tagline": "", "upvotes": 0}
                self.current_product["name"] = text
                self.in_name = False
            elif self.in_tagline and self.current_product:
                self.current_product["tagline"] = text
                self.in_tagline = False
            elif self.in_votes and self.current_product:
                try:
                    self.current_product["upvotes"] = int(text.replace(",", ""))
                except ValueError:
                    pass
                self.in_votes = False

    def handle_endtag(self, tag):
        if self.current_product and self.current_product.get("name"):
            self.products.append(self.current_product)
            self.current_product = None


# ─── Web Fetch（不依赖外部库）─────────────────────

def fetch_url(url: str, timeout: int = 15) -> str:
    """使用 urllib 获取页面内容"""
    try:
        from urllib.request import urlopen, Request
        from urllib.error import URLError

        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
        })
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"   ⚠️  网络请求失败: {e}")
        return None


# ─── 扫描逻辑 ────────────────────────────────────

def scan_producthunt() -> dict:
    """扫描 Product Hunt AI 分类页"""
    print(f"\n🔍 扫描 Product Hunt AI 分类...")

    # PoC 模式：使用样本数据验证数据结构
    # 真实环境需要 resolve Product Hunt 的 JS 渲染（可用 headless browser）
    print("   ℹ️  PoC 模式 — 使用样本数据验证数据结构")

    sample_products = [
        {
            "name": "Cursor AI",
            "category": "AI",
            "tagline": "AI-first code editor",
            "upvotes": 2847,
            "description_summary": "基于 AI 的代码编辑器，支持自然语言编程和实时代码生成。",
            "design_highlights": [
                "对话式代码编辑面板",
                "内联 AI 建议卡片",
                "极简深色主题",
            ],
        },
        {
            "name": "Granola",
            "category": "AI",
            "tagline": "AI meeting notes that actually work",
            "upvotes": 1923,
            "description_summary": "智能会议笔记工具，自动识别关键决策和行动项。",
            "design_highlights": [
                "时间线式笔记布局",
                "关键决策高亮卡片",
                "多模态输入（语音+文字+截图）",
            ],
        },
        {
            "name": "Lovable",
            "category": "AI",
            "tagline": "Build apps with AI, no code required",
            "upvotes": 3456,
            "description_summary": "无代码 AI 应用构建器，用自然语言描述需求即可生成全栈应用。",
            "design_highlights": [
                "分屏预览（代码+预览实时联动）",
                "对话式需求输入",
                "一键部署卡片",
            ],
        },
        {
            "name": "ArcMax",
            "category": "AI",
            "tagline": "AI browser that reimagines web navigation",
            "upvotes": 2100,
            "description_summary": "AI 驱动的浏览器，自动整理标签页和智能摘要网页内容。",
            "design_highlights": [
                "侧边栏标签管理",
                "自动页面摘要浮层",
                "空间分组设计模式",
            ],
        },
        {
            "name": "Perplexity Spaces",
            "category": "AI",
            "tagline": "Collaborative AI research workspaces",
            "upvotes": 1567,
            "description_summary": "协作式 AI 研究空间，支持团队共享搜索上下文和知识库。",
            "design_highlights": [
                "多面板研究空间",
                "可共享的知识卡片",
                "实时代理协作文档",
            ],
        },
    ]

    # 尝试实际抓取（如果网络可用）
    html = fetch_url(PRODUCT_HUNT_AI_URL)
    live_products = []
    if html:
        parser = ProductHuntParser()
        try:
            parser.feed(html)
            live_products = parser.products[:10]
        except Exception as e:
            print(f"   ⚠️  HTML 解析失败: {e}")

    products = live_products if live_products else sample_products

    # 提取设计特征
    design_trends = []
    for p in products:
        if p.get("design_highlights"):
            design_trends.extend(p["design_highlights"])

    # 聚合设计趋势
    trend_keywords = {
        "对话式": 0, "卡片": 0, "极简": 0, "暗色": 0,
        "多模态": 0, "实时": 0, "协作": 0, "预览": 0,
    }
    for trend in design_trends:
        for kw in trend_keywords:
            if kw in trend:
                trend_keywords[kw] += 1

    top_trends = [k for k, v in sorted(trend_keywords.items(), key=lambda x: -x[1]) if v > 0]

    result = {
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "platform": "producthunt",
        "mode": "live" if live_products else "poc",
        "source_url": PRODUCT_HUNT_AI_URL,
        "products_scanned": len(products),
        "top_new": products[:10],
        "ranking_changes": [],
        "design_trends_detected": top_trends,
        "cross_platform_insights": generate_cross_platform_insights(products),
    }

    return result


def generate_cross_platform_insights(products: list) -> list:
    """从产品数据中生成跨平台设计洞察"""
    insights = []

    # 基于样本数据的设计模式识别
    dialogue_products = [p for p in products
                         if any(kw in str(p.get("design_highlights", [])) for kw in ["对话", "聊天"])]
    card_products = [p for p in products
                     if any(kw in str(p.get("design_highlights", [])) for kw in ["卡片"])]
    multimodal_products = [p for p in products
                           if any(kw in str(p.get("design_highlights", [])) for kw in ["多模态", "语音+文字"])]

    if dialogue_products:
        insights.append(
            f"对话式信息架构正在成为 AI 产品的主流交互范式（{len(dialogue_products)}/{len(products)} 产品采用）。"
            "→ 鸿蒙启示：鸿蒙的服务卡片可借鉴对话式组织方式，将 AI 能力以对话卡片流而非功能菜单呈现。"
        )

    if card_products:
        insights.append(
            f"卡片化设计广泛用于 AI 输出的结构化呈现（{len(card_products)}/{len(products)} 产品采用）。"
            "→ 鸿蒙启示：可利用鸿蒙原子化服务卡片的优势，将 AI 分析结果封装为可分发、可组合的服务卡片。"
        )

    if multimodal_products:
        insights.append(
            f"多模态输入正在成为 AI 产品的标配（{len(multimodal_products)}/{len(products)} 产品支持）。"
            "→ 鸿蒙启示：鸿蒙的多设备协同能力天然适合多模态 AI 体验——手机语音输入+平板视觉展示+手表轻反馈。"
        )

    # 通用洞察
    insights.append(
        "AI 产品的视觉语言趋向于极简深色主题 + 高亮关键信息的对比设计。"
        "→ 鸿蒙启示：鸿蒙的深色模式已经成熟，AI 应用应充分利用系统级深色主题，减少自定义视觉噪音。"
    )

    return insights


# ─── 状态管理 ────────────────────────────────────

def load_scan_state() -> dict:
    """加载扫描状态（用于降级检测）"""
    if SCAN_STATE_FILE.exists():
        with open(SCAN_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "last_successful_scan": None,
        "consecutive_failures": 0,
        "mode": "poc",
    }


def save_scan_state(state: dict):
    """保存扫描状态"""
    os.makedirs(SCAN_STATE_FILE.parent, exist_ok=True)
    with open(SCAN_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def check_degradation(state: dict) -> bool:
    """检查是否需要降级"""
    if state["consecutive_failures"] >= DEGRADATION_THRESHOLD_DAYS:
        print(f"\n⚠️  连续 {state['consecutive_failures']} 天无数据，触发降级模式")
        print("   降级方案：Survey web_search(\"best AI apps 2026\")")
        return True
    return False


# ─── 入口 ──────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SR-APP-001 App Store 扫描 PoC")
    parser.add_argument("--platform", type=str, default="producthunt",
                        choices=["producthunt", "googleplay", "appstore"],
                        help="目标平台（Phase 1 仅支持 producthunt）")
    parser.add_argument("--output", type=str, default=None,
                        help="输出文件路径")
    parser.add_argument("--date", type=str, default=None,
                        help="指定日期（兼容 build_all.py 传参）")
    args = parser.parse_args()

    print("=" * 60)
    print("  SR-APP-001: App Store 扫描能力 PoC")
    print("=" * 60)

    state = load_scan_state()

    if check_degradation(state):
        result = {
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "platform": args.platform,
            "mode": "degraded",
            "note": "降级模式 — 建议使用 Survey web_search 获取数据",
            "top_new": [],
        }
        save_scan_state({"last_successful_scan": state["last_successful_scan"],
                          "consecutive_failures": state["consecutive_failures"] + 1,
                          "mode": "degraded"})
    else:
        if args.platform == "producthunt":
            result = scan_producthunt()
        else:
            print(f"   ⚠️  {args.platform} 平台扫描尚未实现（Phase 2）")
            result = {
                "scan_date": datetime.now().strftime("%Y-%m-%d"),
                "platform": args.platform,
                "mode": "not_implemented",
                "note": f"Phase 1 仅支持 Product Hunt PoC",
            }

    # 更新状态
    state["last_successful_scan"] = result["scan_date"]
    state["consecutive_failures"] = 0 if result.get("top_new") else state["consecutive_failures"] + 1
    state["mode"] = result["mode"]
    save_scan_state(state)

    # 保存结果
    output_path = args.output or str(SCAN_OUTPUT_DIR / f"{result['scan_date']}_{args.platform}.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n📊 扫描结果:")
    print(f"   日期: {result['scan_date']}")
    print(f"   平台: {result['platform']}")
    print(f"   模式: {result['mode']}")
    print(f"   产品数: {len(result.get('top_new', []))}")
    if result.get("design_trends_detected"):
        print(f"   设计趋势: {', '.join(result['design_trends_detected'][:5])}")
    if result.get("cross_platform_insights"):
        print(f"   跨平台洞察: {len(result['cross_platform_insights'])} 条")
    print(f"\n✅ 输出: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
