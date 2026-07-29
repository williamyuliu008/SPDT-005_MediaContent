# -*- coding: utf-8 -*-
"""
product_formatter.py — 内容产品化：排版与视觉元素
==================================================

核心功能：
  1. 将 article_v2 JSON 渲染为面向受众的排版格式
  2. 生成视觉元素（引言框、图表、术语表、代码块等）
  3. 根据 content_type 和 target_channel 选择排版模板
  4. 生成 ContentProduct 的 formatting 字段

规范参考：
  - governance/SPDT-005_SOP.md §6
  - platform/kb/content_type_registry.yaml

输入：
  - article_v2 JSON（来自阶段3 Render）
  - content_type / literary / professional_depth 维度标签
  - target_channel（web / wechat_mp / feishu / ...）

输出：
  - formatting dict（typography / layout / visual_elements）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[4]
FORMAT_TEMPLATES_DIR = REPO_ROOT / "platform" / "5_deliver" / "product" / "templates"


# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

@dataclass
class FormattingRequest:
    """格式化请求"""
    article_v2: dict                    # 阶段3输出的文章JSON
    content_type: str                    # 内容类型
    literary: int                        # 文学性维度（1-5）
    professional_depth: int              # 专业性维度（1-5）
    target_channel: str                  # 目标渠道
    word_count: int = 0
    reading_time_minutes: float = 0.0


@dataclass
class VisualElement:
    """视觉元素"""
    type: str                            # "image" | "pullquote" | "infobox" | "chart" | "code_block"
    content: Any
    position: str = "inline"             # "inline" | "full_width" | "float_left" | "float_right"
    caption: str = ""
    attribution: str = ""


@dataclass
class FormattingResult:
    """格式化结果"""
    typography: dict
    layout: dict
    visual_elements: list[VisualElement] = field(default_factory=list)
    special_sections: dict = field(default_factory=dict)
    channel_specific: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# 排版配置（按文学性 × 专业性）
# ─────────────────────────────────────────────────────────────────

TYPOGRAPHY_PRESETS = {
    # literary × professional_depth → typography config
    (1, 1): {  # 低文学性 × 低专业性 = 极简快讯
        "font_family": "system-ui, -apple-system, sans-serif",
        "font_size": "16px",
        "line_height": 1.6,
        "paragraph_spacing": "0.8em",
    },
    (2, 3): {  # breakdown_news 类
        "font_family": "system-ui, -apple-system, sans-serif",
        "font_size": "16px",
        "line_height": 1.7,
        "paragraph_spacing": "1em",
    },
    (3, 3): {  # science_fact 类
        "font_family": "Georgia, serif",
        "font_size": "17px",
        "line_height": 1.8,
        "paragraph_spacing": "1.2em",
    },
    (3, 4): {  # product_review 类
        "font_family": "PingFang SC, Microsoft YaHei, sans-serif",
        "font_size": "16px",
        "line_height": 1.8,
        "paragraph_spacing": "1em",
    },
    (3, 5): {  # deep_report 类
        "font_family": "PingFang SC, Microsoft YaHei, sans-serif",
        "font_size": "16px",
        "line_height": 1.9,
        "paragraph_spacing": "1.5em",
    },
    (5, 4): {  # oped_argument 类
        "font_family": "Georgia, serif",
        "font_size": "18px",
        "line_height": 2.0,
        "paragraph_spacing": "1.8em",
    },
    (5, 2): {  # creative 类
        "font_family": "Georgia, serif",
        "font_size": "18px",
        "line_height": 2.2,
        "paragraph_spacing": "2em",
    },
}

LAYOUT_PRESETS = {
    "breakdown_news": {
        "type": "single_column",
        "max_width": "720px",
        "has_toc": False,
        "compact": True,           # 紧凑排版，无多余空白
    },
    "science_fact": {
        "type": "mixed",
        "max_width": "800px",
        "has_toc": True,
        "compact": False,
    },
    "deep_industry_report": {
        "type": "single_column",
        "max_width": "900px",
        "has_toc": True,
        "compact": False,
        "print_friendly": True,     # 支持打印/PDF
    },
    "oped_argument": {
        "type": "single_column",
        "max_width": "680px",      # 最佳阅读宽度
        "has_toc": False,
        "compact": False,
        "emphasized_first_para": True,  # 首段引言样式
    },
    "product_review": {
        "type": "mixed",
        "max_width": "800px",
        "has_toc": True,
        "compact": False,
    },
    "creative": {
        "type": "single_column",
        "max_width": "600px",      # 文学性内容宽度更窄
        "has_toc": False,
        "compact": False,
        "scene_breaks": True,       # 场景分隔符（* * *）
        "dialogue_indent": True,    # 对话缩进
    },
}


# ─────────────────────────────────────────────────────────────────
# 核心引擎
# ─────────────────────────────────────────────────────────────────

class ProductFormatter:
    """
    内容产品化 — 排版与视觉元素生成器

    使用方式：
      formatter = ProductFormatter()
      result = formatter.format(FormattingRequest(...))
    """

    def format(self, request: FormattingRequest) -> FormattingResult:
        """
        执行排版格式化。

        流程：
          1. 加载排版预设（typography + layout）
          2. 提取视觉元素（引言/图表/术语）
          3. 生成特殊章节（摘要/参考文献/附录）
          4. 渠道适配调整
        """
        # ── 1. 排版预设 ────────────────────────────────
        typography = self._get_typography(request.literary, request.professional_depth)
        layout = self._get_layout(request.content_type)

        # ── 2. 视觉元素提取 ────────────────────────────
        visual_elements = self._extract_visual_elements(request.article_v2, request.content_type)

        # ── 3. 特殊章节生成 ────────────────────────────
        special_sections = self._generate_special_sections(
            request.article_v2,
            request.content_type,
            request.professional_depth
        )

        # ── 4. 渠道适配 ────────────────────────────────
        channel_specific = self._apply_channel_format(
            typography, layout, request.target_channel
        )

        return FormattingResult(
            typography=channel_specific.get("typography", typography),
            layout=channel_specific.get("layout", layout),
            visual_elements=visual_elements,
            special_sections=special_sections,
            channel_specific=channel_specific,
        )

    # ── 内部方法 ────────────────────────────────────────

    def _get_typography(self, literary: int, professional_depth: int) -> dict:
        """根据文学性和专业性选取排版预设"""
        key = (literary, professional_depth)
        if key in TYPOGRAPHY_PRESETS:
            return TYPOGRAPHY_PRESETS[key].copy()

        # 线性插值近似（未精确匹配时）
        base = TYPOGRAPHY_PRESETS[(3, 3)]
        return base.copy()

    def _get_layout(self, content_type: str) -> dict:
        """根据内容类型选取布局预设"""
        return LAYOUT_PRESETS.get(content_type, LAYOUT_PRESETS["science_fact"]).copy()

    def _extract_visual_elements(
        self, article_v2: dict, content_type: str
    ) -> list[VisualElement]:
        """从 article_v2 中提取并生成视觉元素"""
        elements: list[VisualElement] = []

        # 从文章结构中提取引言
        for block in article_v2.get("blocks", []):
            if block.get("type") == "pullquote":
                elements.append(VisualElement(
                    type="pullquote",
                    content=block.get("text"),
                    position="full_width",
                    attribution=block.get("attribution", ""),
                ))
            elif block.get("type") == "infobox":
                elements.append(VisualElement(
                    type="infobox",
                    content=block.get("content"),
                    position="float_right",
                    caption=block.get("title", ""),
                ))

        # 根据内容类型自动生成术语表（高专业性）
        if content_type in ("deep_industry_report", "product_review"):
            terms = article_v2.get("metadata", {}).get("terms", [])
            if terms:
                elements.append(VisualElement(
                    type="infobox",
                    content={"术语表": terms},
                    position="float_right",
                    caption="专业术语",
                ))

        return elements

    def _generate_special_sections(
        self, article_v2: dict, content_type: str, professional_depth: int
    ) -> dict:
        """生成特殊章节（摘要/参考文献/附录）"""
        sections = {}

        # 深度报告和专业内容 → 摘要章节
        if content_type in ("deep_industry_report", "science_fact") or professional_depth >= 4:
            sections["abstract"] = article_v2.get("abstract", "")

        # 高专业性内容 → 参考文献章节
        if professional_depth >= 4:
            refs = article_v2.get("references", [])
            if refs:
                sections["references"] = refs

        # 附录（可选）
        appendix = article_v2.get("appendix")
        if appendix:
            sections["appendix"] = appendix

        return sections

    def _apply_channel_format(
        self, typography: dict, layout: dict, target_channel: str
    ) -> dict:
        """根据目标渠道调整排版"""
        channel_overrides = {
            "wechat_mp": {
                "typography": {
                    "font_family": "Microsoft YaHei, PingFang SC, sans-serif",
                    "font_size": "15px",
                },
                "layout": {
                    "max_width": "100%",
                    "compact": True,
                },
            },
            "feishu": {
                "typography": {
                    "font_family": "Lark_Emoji, Noto Sans SC, sans-serif",
                },
                "layout": {
                    "max_width": "100%",
                },
            },
            "mobile": {
                "typography": {
                    "font_size": "15px",
                    "line_height": 1.7,
                },
                "layout": {
                    "max_width": "100%",
                    "compact": True,
                },
            },
        }

        override = channel_overrides.get(target_channel, {})
        result_typography = {**typography, **override.get("typography", {})}
        result_layout = {**layout, **override.get("layout", {})}

        return {"typography": result_typography, "layout": result_layout}


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse, json

    parser = argparse.ArgumentParser(description="内容产品化 — 排版格式化")
    parser.add_argument("--content-type", default="deep_industry_report")
    parser.add_argument("--literary", type=int, default=3)
    parser.add_argument("--professional-depth", type=int, default=5)
    parser.add_argument("--channel", default="web")
    args = parser.parse_args()

    formatter = ProductFormatter()

    # 模拟 article_v2 输入
    mock_article = {
        "title": "测试文章",
        "blocks": [
            {"type": "paragraph", "text": "正文内容..."},
            {"type": "pullquote", "text": "核心观点引用", "attribution": "编辑按"},
        ],
        "metadata": {"terms": [{"term": "AI", "definition": "人工智能"}]},
        "references": [{"title": "来源1", "url": "https://example.com"}],
    }

    request = FormattingRequest(
        article_v2=mock_article,
        content_type=args.content_type,
        literary=args.literary,
        professional_depth=args.professional_depth,
        target_channel=args.channel,
    )

    result = formatter.format(request)
    print(json.dumps({
        "typography": result.typography,
        "layout": result.layout,
        "visual_elements_count": len(result.visual_elements),
        "special_sections": result.special_sections,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
