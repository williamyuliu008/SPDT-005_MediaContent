# -*- coding: utf-8 -*-
"""
metadata_generator.py — 内容产品化：元数据生成
==================================================

核心功能：
  1. 生成 SEO 元数据（SEO_title / description / keywords）
  2. 生成微信公众号摘要（digest，≤54字）
  3. 生成封面图建议（描述词 + 风格标签）
  4. 生成发布时间策略建议
  5. 生成作者信息

规范参考：
  - governance/SPDT-005_SOP.md §6.2
  - platform/kb/content_type_registry.yaml

输入：
  - article_v2 JSON（来自阶段3 Render）
  - content_type / accuracy / professional_depth 维度标签
  - channels（目标发布渠道列表）

输出：
  - metadata dict（SEO / 摘要 / 封面图建议 / 作者 / 发布时间）
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[4]


# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

@dataclass
class MetadataRequest:
    """元数据生成请求"""
    article_v2: dict
    content_type: str
    accuracy: int                        # 准确性维度（1-5）
    professional_depth: int              # 专业性维度（1-5）
    channels: list[str] = field(default_factory=list)
    author_name: str = "AI 编辑"
    author_bio: str = ""
    author_avatar: str = ""


@dataclass
class MetadataResult:
    """元数据生成结果"""
    title: str
    SEO_title: str
    description: str                     # 摘要（150-300字）
    keywords: list[str]
    tags: list[str]
    author: dict
    publish_time: str
    update_time: str
    language: str
    cover_image: dict
    thumbnail: str
    channel_specific: dict = field(default_factory=dict)  # 各渠道特定元数据


# ─────────────────────────────────────────────────────────────────
# 核心引擎
# ─────────────────────────────────────────────────────────────────

class MetadataGenerator:
    """
    元数据生成器

    使用方式：
      generator = MetadataGenerator()
      metadata = generator.generate(MetadataRequest(...))
    """

    # 摘要长度配置（按渠道）
    DIGEST_LENGTH = 54          # 微信公众号摘要上限
    DESCRIPTION_MIN = 100
    DESCRIPTION_MAX = 300

    # 关键词提取：停用词
    STOP_WORDS = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要",
        "去", "你", "会", "着", "没有", "看", "好", "自己", "这",
    }

    def generate(self, request: MetadataRequest) -> MetadataResult:
        """
        生成完整元数据。

        流程：
          1. 提取标题和正文关键词
          2. 生成 SEO 元数据
          3. 生成各渠道特定元数据
          4. 生成封面图建议
          5. 确定发布时间
        """
        # ── 1. 标题 ────────────────────────────────────
        title = request.article_v2.get("title", "未命名文章")
        SEO_title = self._generate_SEO_title(title, request.content_type)

        # ── 2. 关键词和标签 ────────────────────────────
        keywords, tags = self._extract_keywords_and_tags(
            request.article_v2, request.content_type, request.professional_depth
        )

        # ── 3. 摘要 ────────────────────────────────────
        description = self._generate_description(
            request.article_v2, request.content_type
        )

        # ── 4. 渠道特定元数据 ─────────────────────────
        channel_specific = self._generate_channel_metadata(
            description, request.channels, request.content_type
        )

        # ── 5. 封面图建议 ──────────────────────────────
        cover_image = self._generate_cover_image_suggestion(
            title, request.content_type, request.professional_depth
        )

        # ── 6. 时间 ────────────────────────────────────
        now = datetime.now(timezone.utc).isoformat()
        publish_time = self._suggest_publish_time(request.content_type, request.channels)

        return MetadataResult(
            title=title,
            SEO_title=SEO_title,
            description=description,
            keywords=keywords,
            tags=tags,
            author={
                "name": request.author_name,
                "bio": request.author_bio or self._default_author_bio(request.content_type),
                "avatar": request.author_avatar,
            },
            publish_time=publish_time or now,
            update_time=now,
            language="zh-CN",
            cover_image=cover_image,
            thumbnail=cover_image.get("url", ""),
            channel_specific=channel_specific,
        )

    # ── 内部方法 ────────────────────────────────────────

    def _generate_SEO_title(self, title: str, content_type: str) -> str:
        """生成 SEO 优化标题"""
        # 深度报告和专业内容 → 在标题后加站点名
        if content_type in ("deep_industry_report", "product_review", "oped_argument"):
            return f"{title} | 专业分析"
        return title

    def _extract_keywords_and_tags(
        self, article_v2: dict, content_type: str, professional_depth: int
    ) -> tuple[list[str], list[str]]:
        """从文章中提取关键词和标签"""
        text = self._extract_text(article_v2)
        words = [w for w in re.findall(r'[\u4e00-\u9fff]+', text) if len(w) >= 2]
        # 去除停用词并统计频率
        filtered = [w for w in words if w not in self.STOP_WORDS]

        # 简单词频统计（实际可用 TF-IDF）
        freq: dict = {}
        for w in filtered:
            freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        top_words = [w for w, _ in sorted_words[:10]]

        # 标签 = 高频词 + 内容类型标签 + 专业领域标签
        type_tags = {
            "deep_industry_report": ["行业分析", "深度报告"],
            "science_fact": ["科普", "知识"],
            "oped_argument": ["观点", "评论"],
            "product_review": ["评测", "产品"],
            "breakdown_news": ["快讯", "新闻"],
            "creative": ["故事", "人物"],
        }

        tags = top_words[:5] + type_tags.get(content_type, [])

        return top_words[:8], list(set(tags))[:8]

    def _extract_text(self, article_v2: dict) -> str:
        """从 article_v2 中提取纯文本"""
        parts = []
        for block in article_v2.get("blocks", []):
            if "text" in block:
                parts.append(block["text"])
            elif "content" in block:
                if isinstance(block["content"], str):
                    parts.append(block["content"])
                elif isinstance(block["content"], dict):
                    parts.append(str(block["content"]))
        return " ".join(parts)

    def _generate_description(
        self, article_v2: dict, content_type: str
    ) -> str:
        """生成摘要描述"""
        text = self._extract_text(article_v2)

        # 尝试从 article_v2 中提取摘要
        abstract = article_v2.get("abstract", "")
        if abstract and len(abstract) >= self.DESCRIPTION_MIN:
            return abstract[:self.DESCRIPTION_MAX]

        # 从正文第一段提取
        first_para = ""
        for block in article_v2.get("blocks", []):
            if block.get("type") == "paragraph":
                first_para = block.get("text", "")
                break

        if first_para:
            desc = re.sub(r'\s+', ' ', first_para).strip()
            if len(desc) > self.DESCRIPTION_MAX:
                desc = desc[:self.DESCRIPTION_MAX].rsplit(' ', 1)[0] + "..."
            return desc

        # 默认摘要
        return f"本文深入分析了{article_v2.get('title', '相关内容')}。"[:self.DESCRIPTION_MAX]

    def _generate_channel_metadata(
        self, description: str, channels: list[str], content_type: str
    ) -> dict:
        """生成各渠道特定元数据"""
        result = {}

        if "wechat_mp" in channels:
            # 微信公众号摘要 ≤54字
            digest = description[:self.DIGEST_LENGTH]
            result["wechat_mp"] = {
                "digest": digest if len(description) <= self.DIGEST_LENGTH else digest + "...",
                "original_mark": True,
                "source": "原创",
                "tags": [],
            }
            # 利益披露（产品评测类）
            if content_type == "product_review":
                result["wechat_mp"]["disclosure"] = "本文含联盟链接，购买后可能获得佣金。"

        if "mobile" in channels:
            # APP推送标题 ≤50字
            result["mobile"] = {
                "push_title": description[:50],
                "push_summary": description[:100],
                "deep_link": "",
            }

        if "feeds" in channels:
            # feeds 摘要通常120字
            result["feeds"] = {
                "excerpt_length": 120,
                "include_images": True,
            }

        return result

    def _generate_cover_image_suggestion(
        self, title: str, content_type: str, professional_depth: int
    ) -> dict:
        """生成封面图建议（描述词 + 风格标签）"""
        style_tags = {
            "breakdown_news": ["突发", "新闻", "红色系", "快讯"],
            "science_fact": ["科普", "蓝色系", "知识图", "清晰"],
            "deep_industry_report": ["专业", "深色系", "数据", "商务"],
            "oped_argument": ["观点", "对比", "引用", "深刻"],
            "product_review": ["产品", "评测", "实物图", "对比"],
            "creative": ["故事", "人文", "暖色系", "情感"],
        }

        tags = style_tags.get(content_type, ["通用", "蓝色系"])

        return {
            "url": "",
            "suggestion": {
                "subject": title[:10],      # 标题提取作为主体建议
                "style": tags,
                "colors": self._suggest_colors(content_type, professional_depth),
            },
            "alt": title,
            "credit": "",
        }

    def _suggest_colors(self, content_type: str, professional_depth: int) -> list[str]:
        """建议配色方案"""
        if content_type == "breakdown_news":
            return ["#E53935", "#FFCDD2", "#FFFFFF"]   # 红色系（紧急感）
        elif content_type == "creative":
            return ["#8D6E63", "#FFF3E0", "#3E2723"]   # 暖棕系（文学感）
        elif content_type == "science_fact":
            return ["#1E88E5", "#E3F2FD", "#0D47A1"]  # 蓝色系（科技感）
        elif professional_depth >= 4:
            return ["#37474F", "#ECEFF1", "#263238"]   # 深灰系（专业感）
        else:
            return ["#43A047", "#E8F5E9", "#1B5E20"]   # 绿色系（中立）

    def _suggest_publish_time(self, content_type: str, channels: list[str]) -> str:
        """建议发布时间（用于 schedule 建议，非强制）"""
        # 快讯类 → 立即发布（返回空，由调用方决定）
        if content_type == "breakdown_news":
            return ""
        # 公众号优先 → 工作日早8点或晚8点
        if "wechat_mp" in channels:
            return ""   # TODO: 实现具体时间推荐逻辑
        return ""

    def _default_author_bio(self, content_type: str) -> str:
        """默认作者简介（按内容类型）"""
        bios = {
            "deep_industry_report": "专注行业研究与数据分析",
            "science_fact": "科学传播与知识普及",
            "oped_argument": "独立观察与深度评论",
            "product_review": "客观产品评测与购买指南",
            "breakdown_news": "实时新闻速报",
            "creative": "非虚构故事与人文记录",
        }
        return bios.get(content_type, "内容创作者")


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="元数据生成器")
    parser.add_argument("--content-type", default="deep_industry_report")
    parser.add_argument("--accuracy", type=int, default=4)
    parser.add_argument("--professional-depth", type=int, default=5)
    parser.add_argument("--channels", default="web,wechat_mp,feeds")
    args = parser.parse_args()

    generator = MetadataGenerator()

    mock_article = {
        "title": "半导体行业2026年深度分析报告",
        "abstract": "本文深入分析了全球半导体产业的发展趋势...",
        "blocks": [
            {"type": "paragraph", "text": "2026年全球半导体市场持续波动..."},
            {"type": "paragraph", "text": "从供应链角度看，上游材料供应紧张..."},
        ],
    }

    request = MetadataRequest(
        article_v2=mock_article,
        content_type=args.content_type,
        accuracy=args.accuracy,
        professional_depth=args.professional_depth,
        channels=args.channels.split(","),
    )

    result = generator.generate(request)
    print(json.dumps({
        "title": result.title,
        "SEO_title": result.SEO_title,
        "description": result.description[:80] + "...",
        "keywords": result.keywords,
        "tags": result.tags,
        "author": result.author,
        "channel_specific": result.channel_specific,
        "cover_image_suggestion": result.cover_image.get("suggestion"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
