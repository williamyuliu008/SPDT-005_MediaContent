"""
formatter.py — 格式转换器
==========================
将 Content Bundle（SmartText 引擎输出的标准格式）转换为渠道特定格式。

Content Bundle 结构:
{
    "date": "2026-06-22",
    "formats": {
        "daily_report": {
            "markdown": "...",
            "sections": {...},
            "word_count": 2500,
            ...
        }
    },
    "signals": [...]
}

渠道配置 (channel.yaml) 中的 content.primary 指定取哪个 format。
渠道配置中的 content.format 指定输出形态（html / markdown / plain）。
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Markdown → HTML 简易转换器 ──────────────────────────────

def md_to_html(md_text: str) -> str:
    """简易 Markdown → HTML 转换。"""
    import re

    lines = md_text.split('\n')
    html: list[str] = []
    in_table = False
    in_code = False
    code_lines: list[str] = []

    for line in lines:
        # Code blocks
        if line.startswith('```'):
            if in_code:
                html.append(f'<pre><code>{"".join(code_lines)}</code></pre>')
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line + '\n')
            continue

        # Tables
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                html.append('<table>')
            cells = [c.strip() for c in line.split('|')[1:-1]]
            tag = 'th' if all(c.startswith(':') or c.startswith('-') for c in cells if c) else 'td'
            if tag == 'th' and all(c.startswith('-') or c.startswith(':') for c in cells if c):
                continue  # skip separator row
            html.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
            continue
        elif in_table:
            html.append('</table>')
            in_table = False

        # Blockquotes
        if line.startswith('>'):
            content = line[1:].strip()
            if content.startswith('**'):
                content = content.replace('**', '')
                html.append(f'<blockquote class="signal-meta">{content}</blockquote>')
            else:
                html.append(f'<blockquote>{content}</blockquote>')
            continue

        # Headers
        if line.startswith('# '):
            html.append(f'<h1 class="report-title">{line[2:]}</h1>')
        elif line.startswith('## '):
            html.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('### '):
            html.append(f'<h3>{line[4:]}</h3>')
        # Horizontal rules
        elif line.strip() == '---':
            html.append('<hr>')
        # Bold
        elif '**' in line:
            html.append('<p>' + re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line) + '</p>')
        # Inline code
        elif '`' in line and not line.startswith('`'):
            html.append('<p>' + re.sub(r'`(.+?)`', r'<code>\1</code>', line) + '</p>')
        # Italic
        elif line.startswith('*') and line.endswith('*'):
            html.append(f'<p class="footer-note">{line[1:-1]}</p>')
        # Empty lines
        elif not line.strip():
            html.append('')
        else:
            html.append(f'<p>{line}</p>')

    if in_table:
        html.append('</table>')
    return '\n'.join(html)


# ── 格式转换器 ─────────────────────────────────────────────

class ContentFormatter:
    """将 Content Bundle 转换为渠道特定格式。"""

    def __init__(self, channels_dir: Path | None = None):
        if channels_dir is None:
            channels_dir = Path(__file__).parent.parent / "channels"
        self.channels_dir = Path(channels_dir)

    def format(self, content_bundle: dict[str, Any], channel_config: dict[str, Any]) -> dict[str, Any]:
        """
        根据渠道配置转换内容。

        Args:
            content_bundle: SmartText 引擎输出的 Content Bundle
            channel_config: 渠道配置（从 channel.yaml 加载）

        Returns:
            {
                "channel": "website",
                "format": "html",
                "content": "<html>...</html>",
                "meta": {...}
            }
        """
        channel_id = channel_config.get("channel", {}).get("id", "unknown")
        content_cfg = channel_config.get("content", {})
        primary_format = content_cfg.get("primary", "daily_report")
        output_format = content_cfg.get("output_format", "html")  # html | markdown | plain
        max_chars = content_cfg.get("max_chars", 0)

        # 从 Content Bundle 中提取指定格式的内容
        formats = content_bundle.get("formats", {})
        target_content = formats.get(primary_format)

        if target_content is None:
            logger.warning(f"Content Bundle 中未找到格式 '{primary_format}'，使用第一个可用格式")
            if formats:
                primary_format = next(iter(formats.keys()))
                target_content = formats[primary_format]
            else:
                raise ValueError("Content Bundle 中没有可用的内容格式")

        # 提取 markdown 文本
        md_text = target_content.get("markdown", "")
        if not md_text:
            # 尝试从 sections 重建
            sections = target_content.get("sections", {})
            md_text = self._sections_to_markdown(sections)

        # 按渠道要求截断
        if max_chars and len(md_text) > max_chars:
            md_text = md_text[:max_chars] + "\n\n*（内容已截断以适配渠道限制）*"

        # 按渠道要求转换格式
        if output_format == "html":
            formatted = md_to_html(md_text)
        elif output_format == "markdown":
            formatted = md_text
        elif output_format == "plain":
            formatted = self._strip_markdown(md_text)
        else:
            formatted = md_text

        return {
            "channel": channel_id,
            "format": output_format,
            "content": formatted,
            "raw_markdown": md_text,
            "meta": {
                "primary_format": primary_format,
                "word_count": target_content.get("word_count", len(md_text.split())),
                "sections": list(target_content.get("sections", {}).keys()),
            },
        }

    def _sections_to_markdown(self, sections: dict[str, Any]) -> str:
        """从 sections 结构重建 markdown。"""
        md_parts: list[str] = []
        for section_id, section_data in sections.items():
            label = section_data.get("label", section_id)
            md_parts.append(f"## {label}")
            items = section_data.get("items", [])
            for item in items:
                if isinstance(item, dict):
                    title = item.get("title", "")
                    summary = item.get("summary", "")
                    md_parts.append(f"**{title}**")
                    md_parts.append(f"> {summary}")
                    md_parts.append("")
                else:
                    md_parts.append(f"{item}")
            md_parts.append("")
        return "\n".join(md_parts)

    @staticmethod
    def _strip_markdown(md_text: str) -> str:
        """移除 markdown 标记，产出纯文本。"""
        import re
        text = re.sub(r'#{1,6}\s+', '', md_text)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'>\s?', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
