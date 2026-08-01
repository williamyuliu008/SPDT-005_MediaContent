# -*- coding: utf-8 -*-
"""
magazine_assembler.py — 科学杂志产品组装器
============================================

功能：
  1. 将 MagazineRunResult 组装为完整杂志 Markdown
  2. 输出 Markdown / DOCX / HTML 格式
  3. 生成封面、目录、封底

使用方式：
  artifact = MagazineAssembler().assemble(run_result, fmt="docx")
  artifact.save(output_dir)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

@dataclass
class MagazineArtifact:
    """杂志交付物"""
    title: str
    issue: str
    full_markdown: str
    format: str           # markdown / docx / html
    output_dir: Path
    articles_dir: Path
    metadata: dict

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
            return path
        elif self.format == "html":
            path = base_dir / f"magazine_{self.issue}.html"
            path.write_text(self._to_html(), encoding="utf-8")
            return path
        elif self.format == "docx":
            # DOCX 生成依赖 python-docx，fallback 到 Markdown
            path = base_dir / f"magazine_{self.issue}.md"
            path.write_text(self.full_markdown, encoding="utf-8")
            return path
        else:
            raise ValueError(f"Unknown format: {self.format}")

    def _to_html(self) -> str:
        """将 Markdown 转换为简单 HTML"""
        import re
        md = self.full_markdown

        # 简单的 Markdown → HTML 转换
        # 标题
        md = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md, flags=re.MULTILINE)
        md = re.sub(r'^## (.+)$', r'<h2>\1</h2>', md, flags=re.MULTILINE)
        md = re.sub(r'^### (.+)$', r'<h3>\1</h3>', md, flags=re.MULTILINE)

        # 段落：连续非空行合成 <p>
        lines = md.split('\n')
        result = []
        in_p = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('<h') or stripped.startswith('---'):
                if in_p:
                    result.append('</p>')
                    in_p = False
                result.append(stripped)
            elif stripped:
                if not in_p:
                    result.append('<p>')
                    in_p = True
                result.append(stripped)
            else:
                if in_p:
                    result.append('</p>')
                    in_p = False
        if in_p:
            result.append('</p>')

        body = '\n'.join(result)
        return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self.title} {self.issue}</title>
<style>
body {{ font-family: "Noto Serif CJK SC", "Source Han Serif CN", serif; max-width: 800px; margin: 2em auto; padding: 0 1em; line-height: 1.8; color: #333; }}
h1 {{ font-size: 1.8em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }}
h2 {{ font-size: 1.4em; margin-top: 1.5em; color: #444; }}
h3 {{ font-size: 1.1em; color: #555; }}
blockquote {{ border-left: 4px solid #ccc; margin: 1em 0; padding: 0.5em 1em; background: #f9f9f9; }}
hr {{ border: none; border-top: 1px solid #ccc; margin: 2em 0; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────
# MagazineAssembler
# ─────────────────────────────────────────────────────────────────

ROLE_DISPLAY_NAMES = {
    "cover_story": "封面专题",
    "explain":      "科学解释",
    "industry":     "产业透视",
    "news_brief":   "科技动态",
    "oped":         "观点交锋",
}


class MagazineAssembler:
    """
    杂志产品组装器。

    将 MagazineRunResult 中的各篇文章组装为完整杂志，
    支持 Markdown / HTML / DOCX 输出。
    """

    def assemble(
        self,
        run_result: "MagazineRunResult",
        fmt: str = "markdown",
    ) -> MagazineArtifact:
        """
        组装杂志。

        参数：
          run_result：MagazineRunResult（Orchestrator 输出）
          fmt：输出格式，markdown / html / docx

        返回：
          MagazineArtifact
        """
        spec = run_result.spec
        articles = run_result.articles
        issue = spec.get("issue", "unknown")

        # 生成杂志 slug
        title_slug = spec.get("title", "科学前沿").replace("/", "_")

        # 渲染各部分
        cover_md = self._render_cover(spec, run_result)
        toc_md = self._render_toc(articles)
        articles_md = []
        for role, article_result in articles.items():
            md = self._render_article(role, article_result)
            articles_md.append(md)
        backcover_md = self._render_backcover(spec, run_result)

        # 合并
        parts = [cover_md, toc_md] + articles_md + [backcover_md]
        full_md = "\n\n---\n\n".join(parts)

        # 元数据
        metadata = {
            "run_id": run_result.run_id,
            "blueprint_id": run_result.blueprint_id,
            "run_at": run_result.run_at,
            "title": spec.get("title", ""),
            "domain_topic": spec.get("domain_topic", ""),
            "issue": issue,
            "audience": spec.get("audience", ""),
            "publication_date": spec.get("publication_date", ""),
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
        )

        # 保存杂志主文件
        artifact.save()

        # 保存各篇文章独立文件
        artifact.articles_dir.mkdir(parents=True, exist_ok=True)
        role_order = ["cover_story", "explain", "industry", "news_brief", "oped"]
        for i, role in enumerate(role_order):
            if role in articles:
                art = articles[role]
                md = art.article.get("markdown", "") if isinstance(art.article, dict) else str(art.article.get("markdown", ""))
                art_path = artifact.articles_dir / f"{i+1:02d}_{role}_{art.topic[:20].replace('/', '_')}.md"
                art_path.write_text(md, encoding="utf-8")

        # 保存元数据
        meta_path = output_dir / "magazine_metadata.json"
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        return artifact

    def _render_cover(self, spec: dict, run_result: "MagazineRunResult") -> str:
        """渲染杂志封面"""
        title = spec.get("title", "科学前沿")
        issue = spec.get("issue", "")
        domain_topic = spec.get("domain_topic", "")
        audience = spec.get("audience", "")
        publication_date = spec.get("publication_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        all_passed = run_result.all_passed

        passed = run_result.get_passed_count()
        total = len(run_result.articles)
        status = "全部通过" if all_passed else f"{passed}/{total} 通过"

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
        """渲染杂志目录"""
        lines = ["## 目录\n"]
        role_order = ["cover_story", "explain", "industry", "news_brief", "oped"]

        for i, role in enumerate(role_order):
            if role not in articles:
                continue
            art = articles[role]
            role_name = ROLE_DISPLAY_NAMES.get(role, role)
            score = art.total_score
            status_icon = "✅" if art.passed else "⚠️"
            lines.append(
                f"{i+1}. **{role_name}** — {art.topic[:40]}"
                f" {status_icon} [{score:.0f}分]"
            )

        return "\n".join(lines)

    def _render_article(self, role: str, article_result: "ArticleRunResult") -> str:
        """渲染单篇文章（含 scorecard 摘要头）"""
        role_name = ROLE_DISPLAY_NAMES.get(role, role)
        topic = article_result.topic
        total_score = article_result.total_score
        action = article_result.action
        dims = article_result.scorecard.get("dimensions", {}) if isinstance(article_result.scorecard, dict) else {}
        gray_zones = article_result.gray_zones or []

        # 提取 markdown
        if isinstance(article_result.article, dict):
            md = article_result.article.get("markdown", "")
        else:
            md = str(article_result.article)

        # 生成评分头
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
        """渲染杂志封底"""
        title = spec.get("title", "科学前沿")
        issue = spec.get("issue", "")
        audience = spec.get("audience", "")

        # 文章评分汇总
        article_lines = []
        for role, art in sorted(run_result.articles.items()):
            role_name = ROLE_DISPLAY_NAMES.get(role, role)
            status = "✅" if art.passed else "⚠️"
            article_lines.append(f"- {role_name} [{art.total_score:.0f}分] {status}")

        return f"""---

## 杂志信息

**杂志**：{title}
**期号**：{issue}
**目标读者**：{audience}

### 质量报告

{chr(10).join(article_lines)}

**总体状态**：{'✅ 全部通过，可发布' if run_result.all_passed else '⚠️ 部分文章需修订'}

---

*© {datetime.now(timezone.utc).year} {title} · SPDT-005 AI 内容生成系统*
*编辑手记：本杂志由 AI 自动生成，内容仅供参考，不构成投资或政策建议。*
"""


# ─────────────────────────────────────────────────────────────────
# 路径引用（延迟求值，避免模块加载顺序问题）
# ─────────────────────────────────────────────────────────────────

def REPO_ROOT() -> Path:
    # magazine_assembler.py 位于 platform/2_structure/magazine/，
    # 需要 parents[3] 回到 SPDT-005_MediaContent
    return Path(__file__).resolve().parents[3]
