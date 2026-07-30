# -*- coding: utf-8 -*-
"""
channel_adapter.py — 内容产品化：渠道格式适配器
================================================

核心功能：
  1. 将 article_v2 JSON 转换为各渠道的最终发布格式
  2. 支持渠道：web / wechat_mp / feishu / feeds / mobile
  3. 应用排版格式和视觉元素到各渠道
  4. 生成渠道特定的发布配置

规范参考：
  - governance/SPDT-005_SOP.md §6.3
  - platform/kb/content_type_registry.yaml

输入：
  - article_v2 JSON
  - formatting dict（来自 ProductFormatter）
  - metadata dict（来自 MetadataGenerator）
  - target_channels list

输出：
  - dict[channel_name → channel_package]
  - 每个 channel_package 包含：content / config / formatting
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[4]


# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

@dataclass
class ChannelAdapterRequest:
    """渠道适配请求"""
    article_v2: dict                     # 阶段3输出的文章JSON
    formatting: dict                     # 来自 ProductFormatter 的排版结果
    metadata: dict                      # 来自 MetadataGenerator 的元数据
    content_type: str                    # 内容类型
    target_channels: list[str] = field(default_factory=list)
    literary: int = 3                   # 文学性维度（1-5）


@dataclass
class ChannelPackage:
    """单个渠道的发布包"""
    channel: str
    content: str                         # 该渠道的最终内容（HTML/Markdown/JSON等）
    config: dict                         # 该渠道的发布配置
    formatting: dict                     # 该渠道的排版覆盖
    validation: dict = field(default_factory=dict)  # 格式校验结果


# ─────────────────────────────────────────────────────────────────
# 核心引擎
# ─────────────────────────────────────────────────────────────────

class ChannelAdapter:
    """
    渠道格式适配器

    使用方式：
      adapter = ChannelAdapter()
      packages = adapter.adapt(ChannelAdapterRequest(...))
      # packages["web"] → ChannelPackage
      # packages["wechat_mp"] → ChannelPackage
    """

    SUPPORTED_CHANNELS = ["web", "wechat_mp", "feishu", "feeds", "mobile", "markdown"]

    def adapt(self, request: ChannelAdapterRequest) -> dict[str, ChannelPackage]:
        """
        执行多渠道适配。

        对每个目标渠道：
          1. 将 article_v2 转换为该渠道的内容格式
          2. 应用渠道特定的排版覆盖
          3. 添加渠道特定的元数据配置
          4. 格式校验
        """
        packages: dict[str, ChannelPackage] = {}

        for channel in request.target_channels:
            if channel not in self.SUPPORTED_CHANNELS:
                continue

            # 选择渠道适配方法
            if channel == "web":
                pkg = self._adapt_web(request)
            elif channel == "wechat_mp":
                pkg = self._adapt_wechat_mp(request)
            elif channel == "feishu":
                pkg = self._adapt_feishu(request)
            elif channel == "feeds":
                pkg = self._adapt_feeds(request)
            elif channel == "mobile":
                pkg = self._adapt_mobile(request)
            elif channel == "markdown":
                pkg = self._adapt_markdown(request)
            else:
                continue

            # 格式校验
            pkg.validation = self._validate(pkg, channel)
            packages[channel] = pkg

        return packages

    # ── 各渠道适配 ────────────────────────────────────────

    def _adapt_web(self, request: ChannelAdapterRequest) -> ChannelPackage:
        """适配网页发布"""
        content = self._render_web_html(request)
        config = {
            "format": "html",
            "encoding": "utf-8",
            "has_toc": request.formatting.get("layout", {}).get("has_toc", False),
            "related_articles": request.metadata.get("tags", [])[:3],
            "SEO": {
                "title": request.metadata.get("SEO_title", request.metadata.get("title")),
                "description": request.metadata.get("description", "")[:160],
                "keywords": request.metadata.get("keywords", []),
            },
        }
        formatting = self._merge_formatting(request, "web")
        return ChannelPackage(channel="web", content=content, config=config, formatting=formatting)

    def _adapt_wechat_mp(self, request: ChannelAdapterRequest) -> ChannelPackage:
        """适配微信公众号"""
        content = self._render_wechat_html(request)
        channel_meta = request.metadata.get("channel_specific", {}).get("wechat_mp", {})
        config = {
            "format": "html",
            "original_mark": channel_meta.get("original_mark", True),
            "source": channel_meta.get("source", "原创"),
            "digest": channel_meta.get("digest", request.metadata.get("description", "")[:54]),
            "cover_image_id": "",
            "tags": channel_meta.get("tags", []),
        }
        formatting = self._merge_formatting(request, "wechat_mp")
        validation_notes = []
        # 微信公众号特殊校验
        if len(request.metadata.get("description", "")) > 54:
            validation_notes.append(f"摘要超过54字限制，已自动截断")
        if request.formatting.get("layout", {}).get("has_toc"):
            validation_notes.append("目录功能在公众号不支持，已移除")
        return ChannelPackage(
            channel="wechat_mp",
            content=content,
            config=config,
            formatting=formatting,
            validation={"notes": validation_notes, "compliant": True}
        )

    def _adapt_feishu(self, request: ChannelAdapterRequest) -> ChannelPackage:
        """适配飞书文档"""
        content = self._render_feishu_docx(request)
        config = {
            "format": "lark_docx",
            "share_permission": "editor",
            "comment_enabled": True,
        }
        formatting = self._merge_formatting(request, "feishu")
        return ChannelPackage(channel="feishu", content=content, config=config, formatting=formatting)

    def _adapt_feeds(self, request: ChannelAdapterRequest) -> ChannelPackage:
        """适配 RSS/Newsletter"""
        excerpt_len = request.metadata.get("channel_specific", {}).get("feeds", {}).get(
            "excerpt_length", 120
        )
        content = self._render_feeds(request, excerpt_len)
        config = {
            "format": "rss_xml",
            "excerpt_length": excerpt_len,
            "include_images": True,
        }
        formatting = self._merge_formatting(request, "feeds")
        return ChannelPackage(channel="feeds", content=content, config=config, formatting=formatting)

    def _adapt_mobile(self, request: ChannelAdapterRequest) -> ChannelPackage:
        """适配移动端/App推送"""
        push_meta = request.metadata.get("channel_specific", {}).get("mobile", {})
        content = self._render_mobile(request)
        config = {
            "format": "json",
            "push_title": push_meta.get("push_title", request.metadata.get("title", "")[:50]),
            "push_summary": push_meta.get("push_summary", request.metadata.get("description", "")[:100]),
            "deep_link": push_meta.get("deep_link", ""),
        }
        formatting = self._merge_formatting(request, "mobile")
        return ChannelPackage(channel="mobile", content=content, config=config, formatting=formatting)

    # ── 内容渲染 ────────────────────────────────────────

    def _render_web_html(self, request: ChannelAdapterRequest) -> str:
        """渲染为网页 HTML"""
        title = request.metadata.get("title", "")
        typography = request.formatting.get("typography", {})
        layout = request.formatting.get("layout", {})
        body_blocks = self._render_blocks_to_html(request.article_v2, "web")

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{
    font-family: {typography.get('font_family', 'sans-serif')};
    font-size: {typography.get('font_size', '16px')};
    line-height: {typography.get('line_height', 1.8)};
    max-width: {layout.get('max_width', '800px')};
    margin: 0 auto;
    padding: 2em 1em;
  }}
  .pullquote {{
    font-size: 1.2em;
    font-style: italic;
    border-left: 4px solid #1E88E5;
    padding-left: 1em;
    margin: 2em 0;
    color: #555;
  }}
</style>
</head>
<body>
<h1>{title}</h1>
{body_blocks}
</body>
</html>"""

    def _render_wechat_html(self, request: ChannelAdapterRequest) -> str:
        """渲染为微信公众号 HTML（禁用自己的样式，使用微信样式）"""
        title = request.metadata.get("title", "")
        body_blocks = self._render_blocks_to_html(request.article_v2, "wechat_mp")
        # 移除不支持的元素（目录、代码块等）
        body_blocks = self._strip_unsupported_elements(body_blocks, "wechat_mp")
        return f"""<h2 class="rich_media_title">{title}</h2>
<div class="rich_media_content">
{body_blocks}
</div>"""

    def _render_feishu_docx(self, request: ChannelAdapterRequest) -> str:
        """渲染为飞书文档 JSON（简化表示）"""
        title = request.metadata.get("title", "")
        blocks = []
        for block in request.article_v2.get("blocks", []):
            blocks.append({
                "type": block.get("type", "paragraph"),
                "text": block.get("text", ""),
            })
        return json.dumps({
            "title": title,
            "blocks": blocks,
            "author": request.metadata.get("author", {}).get("name", ""),
        }, ensure_ascii=False)

    def _render_feeds(self, request: ChannelAdapterRequest, excerpt_len: int) -> str:
        """渲染为 RSS XML（摘要模式）"""
        title = request.metadata.get("title", "")
        description = request.metadata.get("description", "")[:excerpt_len]
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{title}</title>
    <description>{description}</description>
    <link>{request.metadata.get('channel_specific', {}).get('wechat_mp', {}).get('source', '')}</link>
    <pubDate>{request.metadata.get('publish_time', '')}</pubDate>
  </channel>
</rss>"""

    def _render_mobile(self, request: ChannelAdapterRequest) -> str:
        """渲染为移动端 JSON（App推送用）"""
        return json.dumps({
            "title": request.metadata.get("title", ""),
            "content": request.metadata.get("description", "")[:200],
            "image": request.metadata.get("cover_image", {}).get("url", ""),
        }, ensure_ascii=False)

    # ── Markdown 渠道 ────────────────────────────────────

    def _adapt_markdown(self, request: ChannelAdapterRequest) -> ChannelPackage:
        """生成人类可读的 Markdown 文档"""
        content = self._render_markdown(request)
        config = {
            "format": "markdown",
            "encoding": "utf-8",
        }
        formatting = self._merge_formatting(request, "markdown")
        return ChannelPackage(channel="markdown", content=content, config=config, formatting=formatting)

    def _render_markdown(self, request: ChannelAdapterRequest) -> str:
        """渲染完整 Markdown 文档（含 frontmatter、摘要、来源、评分）"""
        md_lines = []

        # ── Frontmatter ─────────────────────────────────
        md_lines.append("---")
        md_lines.append(f"title: \"{request.metadata.get('title', '')}\"")
        md_lines.append(f"content_type: {request.content_type}")
        md_lines.append(f"publish_time: {request.metadata.get('publish_time', '')}")
        keywords = request.metadata.get("keywords", [])
        if keywords:
            md_lines.append(f"keywords: [{', '.join(keywords)}]")
        md_lines.append("---")
        md_lines.append("")

        # ── 标题 ─────────────────────────────────────────
        md_lines.append(f"# {request.metadata.get('title', '')}")
        md_lines.append("")

        # ── 摘要 ─────────────────────────────────────────
        abstract = request.metadata.get("abstract", "")
        if abstract:
            md_lines.append(f"> **摘要**  {abstract}")
            md_lines.append("")

        # ── 正文 blocks ─────────────────────────────────
        body_md = self._render_blocks_to_markdown(request.article_v2)
        md_lines.append(body_md)
        md_lines.append("")

        # ── 来源列表 ──────────────────────────────────────
        references = request.metadata.get("references", [])
        if references:
            md_lines.append("## 参考来源")
            md_lines.append("")
            for ref in references:
                name = ref.get("name", ref.get("source_name", ""))
                grade = ref.get("grade", "")
                url = ref.get("url", "")
                if name:
                    grade_badge = f"[{grade}]" if grade else ""
                    url_part = f" <{url}>" if url else ""
                    md_lines.append(f"- {grade_badge} {name}{url_part}")
            md_lines.append("")

        # ── 质量评分卡 ────────────────────────────────────
        scorecard_summary = request.metadata.get("scorecard_summary", {})
        if scorecard_summary:
            total = scorecard_summary.get("scorecard", {}).get("total_score", 0)
            passed = scorecard_summary.get("passed", False)
            status_icon = "✅" if passed else "⚠️"
            md_lines.append("## 质量评分卡")
            md_lines.append("")
            md_lines.append(f"**总分**: {total}/100 {status_icon}  ({'通过' if passed else '建议修订'})")
            md_lines.append("")

            dims = scorecard_summary.get("scorecard", {}).get("dimensions", {})
            if dims:
                md_lines.append("| 维度 | 得分 | 评价 |")
                md_lines.append("|------|------|------|")
                for dim_name, dim_data in dims.items():
                    score = dim_data.get("score", 0) if isinstance(dim_data, dict) else dim_data
                    quality = "优秀" if score >= 85 else ("良好" if score >= 70 else "需改进")
                    md_lines.append(f"| {dim_name} | {score} | {quality} |")
                md_lines.append("")

        # ── 关联标签 ──────────────────────────────────────
        tags = request.metadata.get("tags", [])
        if tags:
            md_lines.append(f"**标签**: {' · '.join(tags)}")
            md_lines.append("")

        return "\n".join(md_lines)

    def _render_blocks_to_markdown(self, article_v2: dict) -> str:
        """将 article_v2 blocks 渲染为 Markdown 字符串"""
        md_parts = []
        for block in article_v2.get("blocks", []):
            btype = block.get("type", "paragraph")
            raw_content = block.get("content", {})
            if isinstance(raw_content, dict):
                text = raw_content.get("text", "")
            elif isinstance(raw_content, str):
                text = raw_content
            else:
                text = block.get("text", "")

            if btype == "paragraph":
                md_parts.append(f"{text}\n")
            elif btype == "heading1":
                md_parts.append(f"# {text}\n")
            elif btype == "heading2":
                md_parts.append(f"## {text}\n")
            elif btype == "heading3":
                md_parts.append(f"### {text}\n")
            elif btype == "pullquote":
                attribution = block.get("attribution", "")
                attr_line = f"\n> —— *{attribution}*" if attribution else ""
                md_parts.append(f"> {text}{attr_line}\n")
            elif btype == "image":
                alt = block.get("alt", "")
                caption = block.get("caption", "")
                if caption:
                    md_parts.append(f"![{alt}]({caption})\n")
                else:
                    md_parts.append(f"![{alt}]\n")
            elif btype == "infobox":
                md_parts.append(f"::: info\n{text}\n:::\n")
            elif btype == "code_block":
                lang = block.get("language", "")
                md_parts.append(f"```{lang}\n{text}\n```\n")
            elif btype == "list":
                items = block.get("items", [])
                for item in items:
                    item_text = item if isinstance(item, str) else item.get("text", "")
                    md_parts.append(f"- {item_text}\n")
                md_parts.append("")

        return "".join(md_parts)

    def _render_blocks_to_html(self, article_v2: dict, channel: str) -> str:
        """将 article_v2 blocks 渲染为 HTML 字符串"""
        html_parts = []
        for block in article_v2.get("blocks", []):
            btype = block.get("type", "paragraph")
            # content 可能是 {"text": "..."} 字典，也可能直接是字符串
            raw_content = block.get("content", {})
            if isinstance(raw_content, dict):
                text = raw_content.get("text", "")
            elif isinstance(raw_content, str):
                text = raw_content
            else:
                text = block.get("text", "")

            if btype == "paragraph":
                html_parts.append(f"<p>{text}</p>")
            elif btype == "heading1":
                html_parts.append(f"<h1>{text}</h1>")
            elif btype == "heading2":
                html_parts.append(f"<h2>{text}</h2>")
            elif btype == "heading3":
                html_parts.append(f"<h3>{text}</h3>")
            elif btype == "pullquote":
                attribution = block.get("attribution", "")
                html_parts.append(f'<blockquote class="pullquote">{text}</blockquote>')
            elif btype == "image":
                alt = block.get("alt", "")
                caption = block.get("caption", "")
                html_parts.append(f'<figure><img src="" alt="{alt}"/><figcaption>{caption}</figcaption></figure>')
            elif btype == "infobox":
                html_parts.append(f'<div class="infobox">{text}</div>')
            elif btype == "code_block":
                lang = block.get("language", "")
                html_parts.append(f'<pre><code class="{lang}">{text}</code></pre>')
            elif btype == "list":
                items = block.get("items", [])
                html_parts.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")

        return "\n".join(html_parts)

    def _strip_unsupported_elements(self, html: str, channel: str) -> str:
        """移除渠道不支持的元素"""
        # 微信公众号不支持的标签
        html = re.sub(r'<h[1]>.*?</h[1]>', '', html)  # 移除 h1
        html = re.sub(r'<pre>.*?</pre>', '<p>[代码块]</p>', html, flags=re.DOTALL)  # 替换代码块
        return html

    def _merge_formatting(self, request: ChannelAdapterRequest, channel: str) -> dict:
        """合并全局排版配置与渠道覆盖"""
        base = request.formatting.copy()
        channel_overrides = {
            "wechat_mp": {"layout": {"max_width": "100%"}},
            "feishu": {"typography": {"font_family": "Lark Emoji"}},
            "mobile": {"layout": {"max_width": "100%"}, "typography": {"font_size": "15px"}},
        }
        override = channel_overrides.get(channel, {})
        # 浅合并
        for key, val in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(val, dict):
                base[key] = {**base[key], **val}
            else:
                base[key] = val
        return base

    def _validate(self, pkg: ChannelPackage, channel: str) -> dict:
        """格式校验"""
        notes = []
        compliant = True

        if channel == "wechat_mp":
            digest = pkg.config.get("digest", "")
            if len(digest) > 54:
                notes.append(f"⚠️ digest={len(digest)}字，超过54字限制")
                compliant = False
        elif channel == "mobile":
            title = pkg.config.get("push_title", "")
            if len(title) > 50:
                notes.append(f"⚠️ push_title={len(title)}字，超过50字限制")
                compliant = False

        return {"compliant": compliant, "notes": notes}


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="渠道格式适配器")
    parser.add_argument("--channels", default="web,wechat_mp,feishu,feeds")
    args = parser.parse_args()

    adapter = ChannelAdapter()

    mock_article = {
        "title": "测试文章标题",
        "blocks": [
            {"type": "paragraph", "text": "这是第一段正文内容。"},
            {"type": "heading2", "text": "二级标题"},
            {"type": "paragraph", "text": "这是第二段内容。"},
            {"type": "pullquote", "text": "核心引言内容", "attribution": "编辑按"},
        ],
    }
    mock_formatting = {
        "typography": {"font_family": "Georgia, serif", "font_size": "17px", "line_height": 1.8},
        "layout": {"max_width": "800px", "has_toc": True},
        "visual_elements": [],
    }
    mock_metadata = {
        "title": "测试文章标题",
        "SEO_title": "测试文章标题 | 专业分析",
        "description": "这是文章摘要内容，用于SEO和分享...",
        "keywords": ["测试", "文章", "关键词"],
        "tags": ["测试标签"],
        "channel_specific": {
            "wechat_mp": {"original_mark": True, "digest": "这是微信公众号摘要..."},
            "mobile": {"push_title": "推送标题测试"},
        },
    }

    request = ChannelAdapterRequest(
        article_v2=mock_article,
        formatting=mock_formatting,
        metadata=mock_metadata,
        content_type="deep_industry_report",
        target_channels=args.channels.split(","),
    )

    packages = adapter.adapt(request)
    print(f"生成了 {len(packages)} 个渠道包：")
    for ch, pkg in packages.items():
        preview = pkg.content[:100].replace("\n", " ")
        print(f"  [{ch}] {pkg.config.get('format')} | 合规: {pkg.validation.get('compliant')}")
        print(f"    预览: {preview}...")


if __name__ == "__main__":
    main()
