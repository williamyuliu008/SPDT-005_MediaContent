# -*- coding: utf-8 -*-
"""
magazine_assembler.py — 科学杂志产品组装器
============================================

功能：
  1. 将 MagazineRunResult 组装为完整杂志 Markdown / HTML
  2. 生成封面、目录、正文、封底

使用方式：
  artifact = MagazineAssembler().assemble(run_result, fmt="html")
  artifact.save()
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

ROLE_DISPLAY_NAMES = {
    "cover_story": "封面专题",
    "explain":      "科学解释",
    "industry":     "产业透视",
    "news_brief":   "科技动态",
    "oped":         "观点交锋",
}

ROLE_COLORS = {
    "cover_story": "#f4a261",
    "explain":      "#2a9d8f",
    "industry":     "#264653",
    "news_brief":   "#457b9d",
    "oped":         "#9b2335",
}

ROLE_TEXT_COLORS = {
    "cover_story": "#fff5eb",
    "explain":      "#e8f5f3",
    "industry":     "#e8eff1",
    "news_brief":   "#edf4f8",
    "oped":         "#fce8ea",
}

SOURCE_COLORS = {
    "A": "#198754",
    "B": "#0d6efd",
    "C": "#6c757d",
}

ROLE_ORDER = ["cover_story", "explain", "industry", "news_brief", "oped"]


# ─────────────────────────────────────────────────────────────────
# MagazineArtifact
# ─────────────────────────────────────────────────────────────────

def REPO_ROOT() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass
class MagazineArtifact:
    """杂志交付物"""
    title: str
    issue: str
    full_markdown: str
    format: str           # markdown / html
    output_dir: Path
    articles_dir: Path
    metadata: dict
    full_html: str = ""   # v1.3+ HTML 内容

    def save(self, base_dir: Optional[Path] = None) -> Path:
        """保存杂志到指定目录"""
        if base_dir is None:
            base_dir = self.output_dir
        base_dir.mkdir(parents=True, exist_ok=True)
        self.articles_dir = base_dir / "articles"
        self.articles_dir.mkdir(parents=True, exist_ok=True)

        if self.format == "markdown":
            path = base_dir / f"magazine_{self.issue}.md"
            path.write_text(self.full_markdown, encoding="utf-8")
        elif self.format == "html":
            # 保存 HTML 杂志
            html_path = base_dir / f"magazine_{self.issue}.html"
            html_path.write_text(self.full_html, encoding="utf-8")
            # 同时保存 Markdown 版本
            md_path = base_dir / f"magazine_{self.issue}.md"
            md_path.write_text(self.full_markdown, encoding="utf-8")
            return html_path
        else:
            raise ValueError(f"Unknown format: {self.format}")
        return path

    def _to_html(self) -> str:
        """将 Markdown 转换为简单 HTML（已废弃，使用 MagazineAssemblerV2）"""
        return self.full_html


# ─────────────────────────────────────────────────────────────────
# MagazineAssembler
# ─────────────────────────────────────────────────────────────────

class MagazineAssembler:
    """
    杂志产品组装器。

    将 MagazineRunResult 中的各篇文章组装为完整杂志，
    支持 Markdown / HTML 输出。
    """

    def assemble(
        self,
        run_result: "MagazineRunResult",
        fmt: str = "html",
    ) -> MagazineArtifact:
        """
        组装杂志。

        参数：
          run_result：MagazineRunResult（Orchestrator 输出）
          fmt：输出格式，markdown / html

        返回：
          MagazineArtifact
        """
        spec = run_result.spec
        articles = run_result.articles
        issue = spec.get("issue", "unknown")
        title_slug = spec.get("title", "科学前沿").replace("/", "_")

        # ── Markdown 部分 ──────────────────────────────────────
        cover_md = self._render_cover(spec, run_result)
        toc_md = self._render_toc(articles)
        articles_md = []
        for role in ROLE_ORDER:
            if role in articles:
                md = self._render_article(role, articles[role])
                articles_md.append(md)
        backcover_md = self._render_backcover(spec, run_result)
        parts = [cover_md, toc_md] + articles_md + [backcover_md]
        full_md = "\n\n---\n\n".join(parts)

        # ── HTML 部分 ────────────────────────────────────────────
        full_html = self._render_full_html(run_result)

        # ── 元数据 ────────────────────────────────────────────
        metadata = {
            "run_id": run_result.run_id,
            "blueprint_id": run_result.blueprint_id,
            "run_at": run_result.run_at,
            "title": spec.get("title", ""),
            "domain_topic": spec.get("domain_topic", ""),
            "issue": issue,
            "audience": spec.get("audience", ""),
            "publication_date": spec.get("publication_date", ""),
            "description": spec.get("description", ""),
            "all_passed": run_result.all_passed,
            "articles": {
                role: {
                    "topic": art.topic,
                    "score": art.total_score,
                    "action": art.action,
                    "passed": art.passed,
                }
                for role, art in articles.items()
            },
        }

        output_dir = REPO_ROOT() / "platform/5_deliver/results/magazine" / f"{title_slug}_{issue}"
        output_dir.mkdir(parents=True, exist_ok=True)

        artifact = MagazineArtifact(
            title=spec.get("title", ""),
            issue=issue,
            full_markdown=full_md,
            format=fmt,
            output_dir=output_dir,
            articles_dir=output_dir / "articles",
            metadata=metadata,
            full_html=full_html,
        )

        # 保存杂志
        artifact.save()

        # 保存各篇文章 Markdown
        artifact.articles_dir.mkdir(parents=True, exist_ok=True)
        for i, role in enumerate(ROLE_ORDER):
            if role in articles:
                art = articles[role]
                md = art.article.get("markdown", "") if isinstance(art.article, dict) else str(art.article.get("markdown", ""))
                safe_name = re.sub(r'[\\/:*?"<>|]', '_', art.topic)[:30]
                art_path = artifact.articles_dir / f"{i+1:02d}_{role}_{safe_name}.md"
                art_path.write_text(md, encoding="utf-8")

        # 保存元数据
        meta_path = output_dir / "magazine_metadata.json"
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        return artifact

    # ── Markdown 渲染（保持向后兼容）────────────────────────────

    def _render_cover(self, spec: dict, run_result: "MagazineRunResult") -> str:
        title = spec.get("title", "科学前沿")
        issue = spec.get("issue", "")
        domain_topic = spec.get("domain_topic", "")
        audience = spec.get("audience", "")
        publication_date = spec.get("publication_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        passed = run_result.get_passed_count()
        total = len(run_result.articles)
        status = "全部通过" if run_result.all_passed else f"{passed}/{total} 通过"

        return f"""# {title}

**{issue}**

---

**主题**：{domain_topic}

**目标读者**：{audience}

**发布日期**：{publication_date}

**质量状态**：{status}

---

*本杂志由 SPDT-005 AI 内容生成系统自动生产 · {publication_date}*
"""

    def _render_toc(self, articles: dict) -> str:
        lines = ["## 目录\n"]
        for i, role in enumerate(ROLE_ORDER):
            if role not in articles:
                continue
            art = articles[role]
            role_name = ROLE_DISPLAY_NAMES.get(role, role)
            score = art.total_score
            status_icon = "[OK]" if art.passed else "[REVISE]"
            lines.append(
                f"{i+1}. **{role_name}** — {art.topic[:40]}"
                f" {status_icon} [{score:.0f}分]"
            )
        return "\n".join(lines)

    def _render_article(self, role: str, article_result: "ArticleRunResult") -> str:
        role_name = ROLE_DISPLAY_NAMES.get(role, role)
        topic = article_result.topic
        total_score = article_result.total_score
        action = article_result.action
        dims = article_result.scorecard.get("dimensions", {}) if isinstance(article_result.scorecard, dict) else {}
        gray_zones = article_result.gray_zones or []

        if isinstance(article_result.article, dict):
            md = article_result.article.get("markdown", "")
        else:
            md = str(article_result.article)

        dims_str = " | ".join([
            f"{k}: {v.get('score', v) if isinstance(v, dict) else v}"
            for k, v in list(dims.items())[:5]
        ])

        header = [
            f"## {role_name}：{topic}",
            f"**评分**：{total_score:.1f}/100 | **动作**：{action}",
            f"**维度**：{dims_str}",
        ]
        if gray_zones:
            header.append(f"**注意**：{'；'.join(str(g) for g in gray_zones[:3])}")
        header.append("\n---")
        return "\n".join(header) + "\n\n" + md

    def _render_backcover(self, spec: dict, run_result: "MagazineRunResult") -> str:
        title = spec.get("title", "科学前沿")
        article_lines = []
        for role in ROLE_ORDER:
            if role not in run_result.articles:
                continue
            art = run_result.articles[role]
            role_name = ROLE_DISPLAY_NAMES.get(role, role)
            status = "[OK]" if art.passed else "[REVISE]"
            article_lines.append(f"- {role_name} [{art.total_score:.0f}分] {status}")

        return f"""---

## 杂志信息

**杂志**：{title}
**质量**：{'全部通过，可发布' if run_result.all_passed else '部分文章需修订'}

### 质量报告

{chr(10).join(article_lines)}

---

*© {datetime.now(timezone.utc).year} {title} · SPDT-005 AI 内容生成系统*
*编辑手记：本杂志由 AI 自动生成，内容仅供参考，不构成投资或政策建议。*
"""

    # ── HTML 渲染 ─────────────────────────────────────────────

    def _render_full_html(self, run_result: "MagazineRunResult") -> str:
        """渲染完整 HTML 杂志"""
        spec = run_result.spec
        articles = run_result.articles

        cover_html = self._render_html_cover(spec, run_result)
        toc_html = self._render_html_toc(articles)
        article_parts = []
        for role in ROLE_ORDER:
            if role in articles:
                article_parts.append(self._render_html_article(role, articles[role]))
        backcover_html = self._render_html_backcover(spec, run_result)

        articles_html = "\n".join(article_parts)

        return HTML_TEMPLATE.format(
            title=spec.get("title", "科学前沿"),
            issue=spec.get("issue", ""),
            domain_topic=spec.get("domain_topic", ""),
            publication_date=spec.get("publication_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            audience=spec.get("audience", ""),
            description=spec.get("description", ""),
            cover_html=cover_html,
            toc_html=toc_html,
            articles_html=articles_html,
            backcover_html=backcover_html,
        )

    def _render_html_cover(self, spec: dict, run_result: "MagazineRunResult") -> str:
        """渲染 HTML 封面（v1.5 简化版）

        数据结构（输入 spec）：
            {
                "title": str,           # 杂志名，如"科学前沿"
                "issue": str,           # 期号，如"2026-Q3"
                "domain_topic": str,    # 本期主题，如"人工智能与科学研究的交叉突破"
                "publication_date": str, # 发布日期，如"2026-08-01"
                "description": str,     # 【可选】编辑手记正文；为空时使用默认语
            }

        渲染结构（输出 HTML）：
            <div class="cover">
                <div class="cover-inner">
                    .cover-issue        → 期号
                    h1.cover-title      → 杂志名
                    p.cover-topic       → 本期主题
                    div.cover-editor-note → 编辑手记
                    div.cover-date      → 发布日期
                </div>
            </div>

        【v1.5 变更】已移除：目标读者、质量状态、2条横线、系统页脚
        """
        title = spec.get("title", "科学前沿")
        issue = spec.get("issue", "")
        domain_topic = spec.get("domain_topic", "")
        publication_date = spec.get("publication_date", "")
        description = spec.get("description", "")

        # 编辑手记（可自定义，默认根据主题生成）
        editor_note = description if description else "聚焦科技前沿，呈现领域的最新突破与深度思考。"

        return f"""
    <div class="cover">
        <div class="cover-inner">
            <div class="cover-issue">{issue}</div>
            <h1 class="cover-title">{title}</h1>
            <p class="cover-topic">{domain_topic}</p>
            <div class="cover-editor-note">
                <span class="cover-editor-label">编辑手记</span>
                <p>{editor_note}</p>
            </div>
            <div class="cover-date">{publication_date}</div>
        </div>
    </div>"""

    def _render_html_toc(self, articles: dict) -> str:
        """渲染 HTML 目录（v1.5 简化版：无评分显示）

        数据结构（从 articles dict 推导）：
            ROLE_ORDER 定义目录文章顺序（5个角色槽位）
            每篇article_result 应包含：
                .topic          → 文章标题
                .total_score    → 总分（不显示）
            ROLE_DISPLAY_NAMES[role] → 角色显示名
            ROLE_COLORS[role]        → 角色颜色（badge背景）
            ROLE_TEXT_COLORS[role]   → 角色文字色（badge前景）

        渲染结构（输出 HTML）：
            <div class="toc">
                div.toc-header     → "目录" + "Contents"
                div.toc-list >
                    div.toc-item × N（按 ROLE_ORDER 顺序）
                        div.toc-item-num   → 序号
                        div.toc-item-badge → 角色名（带颜色）
                        div.toc-item-content >
                            span.toc-item-title → 文章标题
            </div>

        【v1.5 变更】已移除：toc-item-score 列（分数/OK 状态）
        """
        items = []
        for i, role in enumerate(ROLE_ORDER):
            if role not in articles:
                continue
            art = articles[role]
            role_name = ROLE_DISPLAY_NAMES.get(role, role)
            role_color = ROLE_COLORS.get(role, "#666")
            role_text_color = ROLE_TEXT_COLORS.get(role, "#fff")

            items.append(f"""
            <div class="toc-item">
                <div class="toc-item-num">{i+1}</div>
                <div class="toc-item-badge" style="background:{role_color};color:{role_text_color}">{role_name}</div>
                <div class="toc-item-content">
                    <span class="toc-item-title">{art.topic}</span>
                </div>
            </div>""")

        return f"""
    <div class="toc">
        <div class="toc-header">
            <h2>目录</h2>
            <div class="toc-issue">Contents</div>
        </div>
        <div class="toc-list">
            {''.join(items)}
        </div>
    </div>"""

    def _render_html_article(self, role: str, article_result: "ArticleRunResult") -> str:
        """渲染单篇 HTML 文章

        【v1.5 变更】已移除：
        - article-meta（总分 88.8/100 + readability/depth 等维度标签）
        - article-notice（KnownLimitation 灰区提示）
        内部质量元数据不对读者展示。
        """
        role_name = ROLE_DISPLAY_NAMES.get(role, role)
        role_color = ROLE_COLORS.get(role, "#666")
        role_text_color = ROLE_TEXT_COLORS.get(role, "#fff")
        topic = article_result.topic

        # 提取 Markdown
        if isinstance(article_result.article, dict):
            md = article_result.article.get("markdown", "")
        else:
            md = str(article_result.article)

        # 解析 Markdown 为 HTML
        body_html = self._parse_markdown_to_html(md, role_color)

        return f"""
    <article class="article role-{role}">
        <header class="article-header" style="--role-color:{role_color}">
            <div class="article-role-badge" style="background:{role_color};color:{role_text_color}">{role_name}</div>
            <h1 class="article-title">{topic}</h1>
        </header>
        <div class="article-body">
            {body_html}
        </div>
        <div class="article-footer">
            <span class="article-word-count">约 {self._count_words(md)} 字</span>
        </div>
    </article>"""

    def _render_html_backcover(self, spec: dict, run_result: "MagazineRunResult") -> str:
        """渲染 HTML 封底"""
        title = spec.get("title", "科学前沿")
        issue = spec.get("issue", "")

        # 下期期号
        try:
            year, q = issue.split("-Q")
            next_q = int(q) % 4 + 1
            next_year = year if int(q) < 4 else str(int(year) + 1)
            next_issue = f"{next_year}-Q{next_q}"
        except Exception:
            next_issue = "下期"

        article_summary = []
        for role in ROLE_ORDER:
            if role not in run_result.articles:
                continue
            art = run_result.articles[role]
            role_name = ROLE_DISPLAY_NAMES.get(role, role)
            role_color = ROLE_COLORS.get(role, "#666")
            article_summary.append(
                f'<div class="summary-item"><span class="summary-badge" style="background:{role_color}">{role_name}</span>'
                f'<span>{art.topic[:36]}</span></div>'
            )

        return f"""
    <div class="backcover">
        <div class="backcover-divider">◆ ◆ ◆</div>
        <h2 class="backcover-heading">本期总结</h2>
        <div class="backcover-summary">
            {''.join(article_summary)}
        </div>
        <div class="backcover-divider">◆ ◆ ◆</div>
        <h2 class="backcover-heading">下期预告</h2>
        <div class="backcover-next">
            <span class="next-badge">敬请期待</span>
            <p>《{title}》{next_issue}：更多前沿科技话题，即将呈现。</p>
        </div>
        <div class="backcover-footer">
            <div class="backcover-copyright">
                © {datetime.now(timezone.utc).year} {title} · SPDT-005 AI Magazine System<br>
                本杂志内容由 AI 自动生成，仅供参考，不构成任何机构立场。
            </div>
        </div>
    </div>"""

    # ── Markdown → HTML 解析 ─────────────────────────────────

    def _parse_markdown_to_html(self, md: str, role_color: str = "#666") -> str:
        """将文章 Markdown 解析为带角色的 HTML"""
        lines = md.split("\n")
        html_parts = []
        i = 0
        in_paragraph = False
        paragraph_buffer = []

        def flush_paragraph():
            nonlocal paragraph_buffer, in_paragraph
            if paragraph_buffer:
                text = " ".join(paragraph_buffer)
                text = self._parse_inline(text)
                html_parts.append(f"<p>{text}</p>")
                paragraph_buffer = []
            in_paragraph = False

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # 标题
            if stripped.startswith("# ") and not stripped.startswith("## "):
                flush_paragraph()
                title_text = stripped[2:].strip()
                html_parts.append(f'<h2 class="section-heading" style="--role-color:{role_color}">{self._parse_inline(title_text)}</h2>')
                i += 1
                continue

            # 二级标题
            if stripped.startswith("## "):
                flush_paragraph()
                title_text = stripped[3:].strip()
                html_parts.append(f'<h3 class="subsection-heading" style="--role-color:{role_color}">{self._parse_inline(title_text)}</h3>')
                i += 1
                continue

            # 引用块（关键术语等）
            if stripped.startswith(">"):
                flush_paragraph()
                block_lines = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    block_lines.append(lines[i].strip()[1:].strip())
                    i += 1
                block_text = " | ".join(block_lines)
                html_parts.append(f'<div class="key-terms" style="--role-color:{role_color}">{self._parse_inline(block_text)}</div>')
                continue

            # 分隔线
            if stripped.startswith("---") or stripped.startswith("***"):
                flush_paragraph()
                html_parts.append('<div class="article-divider"></div>')
                i += 1
                continue

            # 空行
            if not stripped:
                flush_paragraph()
                i += 1
                continue

            # 普通段落
            if stripped:
                # 处理列表
                if stripped.startswith("- ") or re.match(r"^\d+\. ", stripped):
                    flush_paragraph()
                    html_parts.append(f'<div class="list-item">{self._parse_inline(stripped)}</div>')
                    i += 1
                    continue
                paragraph_buffer.append(stripped)
                in_paragraph = True

            i += 1

        flush_paragraph()
        return "\n".join(html_parts)

    def _parse_inline(self, text: str) -> str:
        """解析行内格式：加粗、斜体、来源标注"""
        if not text:
            return ""

        # 来源标注 [A] [A/同行评审] → 上标样式
        def source_replace(m):
            letter = m.group(1)
            color = SOURCE_COLORS.get(letter, "#666")
            label_map = {"A": "同行评审", "B": "arXiv预印本", "C": "科普媒体"}
            label = label_map.get(letter, letter)
            return f'<sup class="source-ref" style="color:{color}" title="{label}">[{letter}]</sup>'

        text = re.sub(r'\[([ABC])\]', source_replace, text)
        text = re.sub(r'\[([ABC])/[^]]+\]', source_replace, text)

        # 加粗 **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # 斜体 *text*
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

        return text

    def _count_words(self, md: str) -> int:
        """估算中文字数"""
        import re
        # 移除 Markdown 语法符号
        cleaned = re.sub(r'[#*>\-\[\]()`]', '', md)
        # 统计汉字和英文单词
        chinese = re.findall(r'[\u4e00-\u9fff]', cleaned)
        english = re.findall(r'[a-zA-Z]+', cleaned)
        return len(chinese) + sum(len(w) for w in english)


# ─────────────────────────────────────────────────────────────────
# HTML 杂志模板
# ─────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} {issue}</title>
<style>
/* ── Reset & Base ─────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
    --font-serif: "Inter", "Noto Serif SC", "Source Han Serif CN", "SimSun", serif;
    --font-sans: "Inter", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    --font-mono: "JetBrains Mono", "Fira Code", monospace;
    --line-height: 1.7;
    --max-width: 900px;
    --color-bg: #fafbfc;
    --color-text: #111;
    --color-text-muted: #666;
    --color-border: #e1e4e8;
    --color-border-light: #f0f0f2;
    --color-quote-bg: #f0f2f5;
    --color-cover-bg: #0f172a;
    --color-cover-text: #f1f5f9;
    --color-cover-accent: #38bdf8;
}}
html {{
    font-size: 16px;
    scroll-behavior: smooth;
}}
body {{
    font-family: var(--font-sans);
    background: var(--color-bg);
    color: var(--color-text);
    line-height: var(--line-height);
    -webkit-font-smoothing: antialiased;
}}
::selection {{
    background: rgba(233, 69, 96, 0.15);
    color: inherit;
}}

/* ── Layout ──────────────────────────────────────────── */
.magazine-container {{
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 0 1.5rem;
}}

/* ── 封面 ────────────────────────────────────────────── */
.cover {{
    background: var(--color-cover-bg);
    color: var(--color-cover-text);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    margin-bottom: 4rem;
    position: relative;
    overflow: hidden;
}}
.cover::before {{
    content: '';
    position: absolute;
    inset: 0;
    background:
        linear-gradient(135deg, rgba(56,189,248,0.08) 0%, transparent 50%),
        linear-gradient(225deg, rgba(139,92,246,0.06) 0%, transparent 50%);
    pointer-events: none;
}}
.cover::after {{
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 300px;
    background: linear-gradient(to top, rgba(15,23,42,0.8), transparent);
    pointer-events: none;
}}
.cover-inner {{
    max-width: 700px;
    width: 100%;
    text-align: center;
    position: relative;
    z-index: 1;
}}
.cover-issue {{
    font-family: var(--font-mono);
    font-size: 0.7rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: rgba(241,245,249,0.5);
    margin-bottom: 1.5rem;
}}
.cover-title {{
    font-family: var(--font-serif);
    font-size: clamp(2.5rem, 7vw, 4.5rem);
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin-bottom: 1.5rem;
}}
.cover-topic {{
    font-family: var(--font-serif);
    font-size: clamp(1.1rem, 3vw, 1.5rem);
    color: var(--color-cover-accent);
    font-weight: 600;
    line-height: 1.5;
    margin-bottom: 2rem;
}}
.cover-editor-note {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: left;
    margin: 2rem 0;
    backdrop-filter: blur(4px);
}}
.cover-editor-label {{
    display: block;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(241,245,249,0.4);
    margin-bottom: 0.5rem;
}}
.cover-editor-note p {{
    font-size: 0.95rem;
    line-height: 1.7;
    color: rgba(241,245,249,0.85);
}}
.cover-date {{
    font-size: 0.8rem;
    color: rgba(241,245,249,0.3);
    letter-spacing: 0.15em;
    margin-top: 2rem;
}}

/* ── 目录 ────────────────────────────────────────────── */
.toc {{
    max-width: var(--max-width);
    margin: 0 auto 3rem;
    padding: 0 1.5rem;
}}
.toc-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--color-border);
}}
.toc-header h2 {{
    font-family: var(--font-serif);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-text);
}}
.toc-issue {{
    font-size: 0.7rem;
    color: var(--color-text-muted);
    font-family: var(--font-mono);
}}
.toc-list {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.75rem;
}}
.toc-item {{
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    background: #fff;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    transition: all 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.toc-item:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}}
.toc-item-num {{
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--color-text-muted);
}}
.toc-item-badge {{
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 0.3rem 0.75rem;
    border-radius: 6px;
    white-space: nowrap;
    width: fit-content;
}}
.toc-item-title {{
    font-family: var(--font-serif);
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--color-text);
    line-height: 1.4;
}}

/* ── 文章 ────────────────────────────────────────────── */
.article {{
    max-width: var(--max-width);
    margin: 0 auto 3rem;
    padding: 0 1.5rem;
}}
.article-header {{
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 2px solid var(--color-border);
    position: relative;
}}
.article-header::before {{
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 60px;
    height: 3px;
    background: var(--role-color, #666);
    border-radius: 2px;
}}
.article-role-badge {{
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    margin-bottom: 0.75rem;
}}
.article-title {{
    font-family: var(--font-serif);
    font-size: clamp(1.4rem, 4vw, 1.9rem);
    font-weight: 700;
    line-height: 1.3;
    color: var(--color-text);
    margin-bottom: 0.75rem;
}}
.article-meta {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
}}
.article-score {{
    font-family: var(--font-mono);
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--color-text);
}}
.article-score small {{
    font-size: 0.8rem;
    color: var(--color-text-muted);
    margin-left: 0.1rem;
}}
.article-dims {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
}}
.dim-chip {{
    font-family: var(--font-mono);
    font-size: 0.7rem;
    background: var(--color-quote-bg);
    color: var(--color-text-muted);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    border: 1px solid var(--color-border);
}}
.article-notice {{
    margin-top: 0.75rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}}
.article-notice span {{
    font-size: 0.72rem;
    color: #b55400;
    background: #fff3e0;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    border: 1px solid #ffcc80;
}}

/* ── 正文 ────────────────────────────────────────────── */
.article-body {{
    font-size: 1rem;
    line-height: var(--line-height);
    color: var(--color-text);
}}
.section-heading {{
    font-family: var(--font-serif);
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--color-text);
    margin: 2.5rem 0 1rem;
    padding-left: 0.75rem;
    border-left: 4px solid var(--role-color, #666);
    line-height: 1.4;
}}
.subsection-heading {{
    font-family: var(--font-serif);
    font-size: 1.1rem;
    font-weight: 600;
    color: #4a4a4a;
    margin: 2rem 0 0.75rem;
    border-bottom: 1px solid var(--color-border-light);
    padding-bottom: 0.4rem;
}}
.article-body p {{
    margin-bottom: 1.2em;
    text-align: justify;
    /* 控制每行字符数，增强可读性 */
    overflow-wrap: break-word;
    /* 首行缩进 */
    text-indent: 2em;
}}
.article-body p:first-of-type {{
    text-indent: 0;
}}
.key-terms {{
    background: var(--color-quote-bg);
    border-left: 4px solid var(--role-color, #666);
    padding: 0.75rem 1.25rem;
    margin: 1.5rem 0;
    border-radius: 0 6px 6px 0;
    font-size: 0.88rem;
    color: #4a4a4a;
    line-height: 1.7;
}}
.article-divider {{
    border: none;
    border-top: 1px solid var(--color-border);
    margin: 2.5rem 0;
}}
.list-item {{
    margin: 0.5rem 0;
    padding-left: 1.5em;
    position: relative;
    font-size: 0.95rem;
}}
.list-item::before {{
    content: '·';
    position: absolute;
    left: 0.5em;
    color: var(--role-color, #666);
    font-weight: 700;
}}
.article-footer {{
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--color-border-light);
    text-align: right;
}}
.article-word-count {{
    font-size: 0.75rem;
    color: var(--color-text-muted);
    font-family: var(--font-mono);
}}

/* ── 来源标注 ──────────────────────────────────────── */
.source-ref {{
    font-family: var(--font-mono);
    font-size: 0.7em;
    font-weight: 700;
    vertical-align: super;
    cursor: help;
    text-decoration: none;
    padding: 0 0.1em;
}}

/* ── 封底 ────────────────────────────────────────────── */
.backcover {{
    max-width: var(--max-width);
    margin: 0 auto 3rem;
    padding: 4rem 2rem;
    background: var(--color-cover-bg);
    color: var(--color-cover-text);
    text-align: center;
    border-radius: 16px;
    margin-left: 1.5rem;
    margin-right: 1.5rem;
}}
.backcover-divider {{
    color: rgba(241,245,249,0.3);
    letter-spacing: 0.5em;
    margin: 2rem 0;
    font-size: 0.9rem;
}}
.backcover-heading {{
    font-family: var(--font-serif);
    font-size: 1.2rem;
    font-weight: 700;
    color: rgba(241,245,249,0.8);
    margin-bottom: 1.5rem;
    letter-spacing: 0.05em;
}}
.backcover-summary {{
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 2rem;
    text-align: left;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
}}
.summary-item {{
    display: grid;
    grid-template-columns: auto 1fr;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.85rem;
    color: rgba(241,245,249,0.7);
}}
.summary-badge {{
    font-size: 0.6rem;
    font-weight: 700;
    padding: 0.2rem 0.5rem;
    border-radius: 6px;
    color: #fff;
    white-space: nowrap;
    text-align: center;
}}
.summary-score {{
    font-family: var(--font-mono);
    font-size: 0.8rem;
    font-weight: 700;
    color: #4ade80;
    white-space: nowrap;
}}
.backcover-next {{
    margin: 1.5rem 0;
}}
.next-badge {{
    display: inline-block;
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    background: linear-gradient(90deg, var(--color-cover-accent), #8b5cf6);
    color: var(--color-cover-bg);
    padding: 0.3rem 1rem;
    border-radius: 20px;
    margin-bottom: 0.75rem;
}}
.backcover-next p {{
    font-size: 0.9rem;
    color: rgba(241,245,249,0.7);
    line-height: 1.6;
}}
.backcover-footer {{
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(241,245,249,0.1);
}}
.backcover-copyright {{
    font-size: 0.72rem;
    color: rgba(241,245,249,0.3);
    line-height: 1.7;
}}

/* ── 响应式 ──────────────────────────────────────────── */
@media (max-width: 600px) {{
    .cover {{ min-height: auto; padding: 3rem 1.5rem; }}
    .cover-title {{ font-size: 2.5rem; }}
    .toc-list {{ grid-template-columns: 1fr; }}
    .toc-item-badge {{ display: none; }}
    .summary-item {{ grid-template-columns: 1fr; gap: 0.25rem; }}
    .summary-item .summary-badge {{ display: none; }}
}}

/* ── 打印优化 ────────────────────────────────────────── */
@media print {{
    body {{ background: #fff; color: #000; }}
    .cover {{ background: #1a1a2e !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .article-role-badge, .toc-item-badge, .dim-chip, .backcover {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .article, .toc, .backcover {{ page-break-inside: avoid; }}
    .cover {{ page-break-after: always; }}
}}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
</head>
<body>

<!-- 封面 -->
{cover_html}

<!-- 目录 -->
{toc_html}

<!-- 文章列表 -->
{articles_html}

<!-- 封底 -->
{backcover_html}

</body>
</html>"""
