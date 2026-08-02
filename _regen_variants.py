"""
SPDT-005 Magazine Style Variant Generator (v1.5)
使用 v1.5 简化样式重新生成所有变体
"""
import re
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).parent
MAGAZINE_DIR = REPO_ROOT / "platform" / "5_deliver" / "results" / "magazine" / "科学前沿_2026-Q3"

# 读取原始杂志HTML
src_html = (MAGAZINE_DIR / "magazine_2026-Q3.html").read_text(encoding="utf-8")

# ============================================================
# v1.5 现代数字风格 (MIT Technology Review) — 默认主版本
# ============================================================
STYLE_MODERN_V15 = """
/* ── Modern Digital: MIT Technology Review 风格 (v1.5) ──────── */
:root {
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
}
body {
    font-family: var(--font-sans);
    background: var(--color-bg);
    color: var(--color-text);
    line-height: var(--line-height);
    -webkit-font-smoothing: antialiased;
}
::selection { background: rgba(56,189,248,0.15); color: inherit; }
.magazine-container { max-width: var(--max-width); margin: 0 auto; padding: 0 1.5rem; }

/* 封面 */
.cover {
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
}
.cover::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(56,189,248,0.08) 0%, transparent 50%),
                linear-gradient(225deg, rgba(139,92,246,0.06) 0%, transparent 50%);
    pointer-events: none;
}
.cover::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 300px;
    background: linear-gradient(to top, rgba(15,23,42,0.8), transparent);
    pointer-events: none;
}
.cover-inner { max-width: 700px; text-align: center; position: relative; z-index: 1; }
.cover-issue { font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.3em; text-transform: uppercase; color: rgba(241,245,249,0.5); margin-bottom: 1.5rem; }
.cover-title { font-family: var(--font-serif); font-size: clamp(2.5rem, 7vw, 4.5rem); font-weight: 800; color: #fff; letter-spacing: -0.02em; line-height: 1.1; margin-bottom: 1.5rem; }
.cover-topic { font-family: var(--font-serif); font-size: clamp(1.1rem, 3vw, 1.5rem); color: var(--color-cover-accent); font-weight: 600; line-height: 1.5; margin-bottom: 2rem; }
.cover-editor-note { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1.25rem 1.5rem; text-align: left; margin: 2rem 0; backdrop-filter: blur(4px); }
.cover-editor-label { display: block; font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(241,245,249,0.4); margin-bottom: 0.5rem; }
.cover-editor-note p { font-size: 0.95rem; line-height: 1.7; color: rgba(241,245,249,0.85); }
.cover-date { font-size: 0.8rem; color: rgba(241,245,249,0.3); letter-spacing: 0.15em; margin-top: 2rem; }

/* 目录 */
.toc { max-width: var(--max-width); margin: 0 auto 3rem; padding: 0 1.5rem; }
.toc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid var(--color-border); }
.toc-header h2 { font-family: var(--font-serif); font-size: 1.5rem; font-weight: 700; color: var(--color-text); }
.toc-issue { font-size: 0.7rem; color: var(--color-text-muted); font-family: var(--font-mono); }
.toc-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.75rem; }
.toc-item { display: flex; flex-direction: column; gap: 0.5rem; padding: 1rem; background: #fff; border: 1px solid var(--color-border); border-radius: 12px; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.toc-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-2px); }
.toc-item-num { font-family: var(--font-mono); font-size: 0.7rem; color: var(--color-text-muted); }
.toc-item-badge { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.05em; padding: 0.2rem 0.5rem; border-radius: 6px; white-space: nowrap; width: fit-content; }
.toc-item-title { font-family: var(--font-serif); font-size: 0.95rem; font-weight: 600; color: var(--color-text); line-height: 1.4; }

/* 文章 */
.article { max-width: var(--max-width); margin: 0 auto 3rem; padding: 0 1.5rem; }
.article-header { margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 2px solid var(--color-border); position: relative; }
.article-header::before { content: ''; position: absolute; bottom: -2px; left: 0; width: 50px; height: 3px; background: var(--role-color, #666); border-radius: 2px; }
.article-role-badge { display: inline-block; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.08em; padding: 0.3rem 0.8rem; border-radius: 6px; margin-bottom: 0.75rem; text-transform: uppercase; }
.article-title { font-family: var(--font-serif); font-size: clamp(1.4rem, 4vw, 1.8rem); font-weight: 700; line-height: 1.3; color: var(--color-text); margin-bottom: 0.75rem; }
.article-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; }
.article-score { font-family: var(--font-mono); font-size: 1.4rem; font-weight: 700; color: var(--color-text); }
.article-score small { font-size: 0.8rem; color: var(--color-text-muted); margin-left: 0.1rem; }
.article-dims { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.dim-chip { font-family: var(--font-mono); font-size: 0.7rem; background: var(--color-quote-bg); color: var(--color-text-muted); padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid var(--color-border); }
.article-notice { margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }
.article-notice span { font-size: 0.72rem; color: #b55400; background: #fff3e0; padding: 0.2rem 0.6rem; border-radius: 4px; border: 1px solid #ffcc80; }

/* 正文 */
.article-body { font-size: 1rem; line-height: var(--line-height); color: var(--color-text); }
.section-heading { font-family: var(--font-serif); font-size: 1.25rem; font-weight: 700; color: var(--color-text); margin: 2.5rem 0 1rem; padding-left: 0.75rem; border-left: 4px solid var(--role-color, #666); line-height: 1.4; }
.subsection-heading { font-family: var(--font-serif); font-size: 1.05rem; font-weight: 600; color: #333; margin: 2rem 0 0.75rem; border-bottom: 1px solid var(--color-border-light); padding-bottom: 0.4rem; }
.article-body p { margin-bottom: 1.2em; overflow-wrap: break-word; }
.article-body p:first-of-type { text-indent: 0; }
.key-terms { background: var(--color-quote-bg); border-left: 4px solid var(--role-color, #666); padding: 0.75rem 1.25rem; margin: 1.5rem 0; border-radius: 0 8px 8px 0; font-size: 0.9rem; color: #444; line-height: 1.7; }
.article-divider { border: none; border-top: 1px solid var(--color-border); margin: 2.5rem 0; }
.list-item { margin: 0.5rem 0; padding-left: 1.5em; position: relative; font-size: 0.95rem; }
.list-item::before { content: '→'; position: absolute; left: 0; color: var(--role-color, #666); font-weight: 600; }
.article-footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--color-border-light); text-align: right; }
.article-word-count { font-size: 0.75rem; color: var(--color-text-muted); font-family: var(--font-mono); }
.source-ref { font-family: var(--font-mono); font-size: 0.7em; font-weight: 700; vertical-align: super; cursor: help; text-decoration: none; padding: 0 0.1em; }

/* 封底 */
.backcover { max-width: var(--max-width); margin: 0 auto 3rem; padding: 4rem 2rem; background: var(--color-cover-bg); color: var(--color-cover-text); text-align: center; border-radius: 16px; margin-left: 1.5rem; margin-right: 1.5rem; }
.backcover-divider { color: rgba(241,245,249,0.3); letter-spacing: 0.5em; margin: 2rem 0; font-size: 0.9rem; }
.backcover-heading { font-family: var(--font-serif); font-size: 1.2rem; font-weight: 700; color: rgba(241,245,249,0.8); margin-bottom: 1.5rem; letter-spacing: 0.05em; }
.backcover-summary { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 2rem; text-align: left; max-width: 500px; margin-left: auto; margin-right: auto; }
.summary-item { display: grid; grid-template-columns: 5rem 1fr auto; align-items: center; gap: 0.75rem; font-size: 0.85rem; color: rgba(241,245,249,0.7); }
.summary-badge { font-size: 0.6rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 6px; color: #fff; white-space: nowrap; text-align: center; }
.summary-score { font-family: var(--font-mono); font-size: 0.8rem; font-weight: 700; color: #4ade80; white-space: nowrap; }
.backcover-next { margin: 1.5rem 0; }
.next-badge { display: inline-block; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; background: linear-gradient(90deg, var(--color-cover-accent), #8b5cf6); color: var(--color-cover-bg); padding: 0.3rem 1rem; border-radius: 20px; margin-bottom: 0.75rem; }
.backcover-next p { font-size: 0.9rem; color: rgba(241,245,249,0.7); line-height: 1.6; }
.backcover-footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid rgba(241,245,249,0.1); }
.backcover-copyright { font-size: 0.72rem; color: rgba(241,245,249,0.3); line-height: 1.7; }

@media (max-width: 600px) {
    .cover { min-height: auto; padding: 3rem 1.5rem; }
    .cover-title { font-size: 2.5rem; }
    .toc-list { grid-template-columns: 1fr; }
}
@media print {
    body { background: #fff; color: #000; }
    .cover { border-radius: 0 !important; }
}
"""

# ============================================================
# 风格2: Classic Editorial (学术经典) — 对标 Nature
# ============================================================
STYLE_CLASSIC_V15 = """
/* ── Classic Editorial: Nature / Scientific American 风格 (v1.5) ── */
:root {
    --font-serif: "Noto Serif SC", "Source Han Serif CN", "SimSun", serif;
    --font-sans: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    --font-mono: "Georgia", "Times New Roman", serif;
    --line-height: 1.9;
    --max-width: 720px;
    --color-bg: #ffffff;
    --color-text: #1a1a1a;
    --color-text-muted: #555;
    --color-border: #d0d0d0;
    --color-border-light: #f0f0f0;
    --color-quote-bg: #fafafa;
    --color-cover-bg: #1c3a5f;
    --color-cover-text: #f8f8f2;
    --color-cover-accent: #c9a227;
}
body { font-family: var(--font-serif); background: var(--color-bg); color: var(--color-text); line-height: var(--line-height); -webkit-font-smoothing: antialiased; }
::selection { background: rgba(201,162,39,0.15); color: inherit; }
.magazine-container { max-width: var(--max-width); margin: 0 auto; padding: 0 2rem; }

.cover { background: var(--color-cover-bg); color: var(--color-cover-text); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 4rem 2rem; margin-bottom: 4rem; position: relative; }
.cover::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse at 30% 40%, rgba(201,162,39,0.15) 0%, transparent 60%); pointer-events: none; }
.cover-inner { max-width: 550px; text-align: center; position: relative; z-index: 1; }
.cover-issue { font-family: var(--font-mono); font-size: 0.75rem; letter-spacing: 0.4em; text-transform: uppercase; color: rgba(248,248,242,0.5); margin-bottom: 2rem; }
.cover-title { font-family: var(--font-serif); font-size: clamp(3rem, 8vw, 5rem); font-weight: 400; color: #fff; letter-spacing: 0.1em; line-height: 1.1; margin-bottom: 2rem; }
.cover-topic { font-family: var(--font-serif); font-size: clamp(1rem, 2.5vw, 1.3rem); color: var(--color-cover-accent); font-weight: 400; font-style: italic; line-height: 1.7; margin-bottom: 1.5rem; }
.cover-editor-note { background: rgba(255,255,255,0.05); border-left: 2px solid var(--color-cover-accent); border-radius: 0 4px 4px 0; padding: 1rem 1.5rem; text-align: left; margin: 1.5rem 0; }
.cover-editor-label { display: block; font-size: 0.65rem; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(248,248,242,0.4); margin-bottom: 0.5rem; font-family: var(--font-sans); }
.cover-editor-note p { font-size: 0.9rem; line-height: 1.7; color: rgba(248,248,242,0.85); }
.cover-date { font-size: 0.7rem; color: rgba(248,248,242,0.4); letter-spacing: 0.1em; margin-top: 2rem; font-family: var(--font-mono); }

.toc { max-width: var(--max-width); margin: 0 auto 3rem; padding: 0 2rem; }
.toc-header { display: flex; align-items: baseline; gap: 1rem; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--color-border); }
.toc-header h2 { font-family: var(--font-serif); font-size: 1.8rem; font-weight: 400; color: var(--color-text); }
.toc-issue { font-size: 0.75rem; color: var(--color-text-muted); font-style: italic; }
.toc-list { display: flex; flex-direction: column; gap: 0; }
.toc-item { display: grid; grid-template-columns: 2.5rem 5rem 1fr; align-items: start; gap: 0.75rem; padding: 1rem 0; border-bottom: 1px solid var(--color-border-light); }
.toc-item:last-child { border-bottom: none; }
.toc-item-num { font-family: var(--font-mono); font-size: 0.9rem; color: var(--color-text-muted); padding-top: 0.2rem; }
.toc-item-badge { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.05em; padding: 0.2rem 0.5rem; border-radius: 2px; white-space: nowrap; font-family: var(--font-sans); }
.toc-item-title { font-family: var(--font-serif); font-size: 0.95rem; font-weight: 400; color: var(--color-text); line-height: 1.4; }

.article { max-width: var(--max-width); margin: 0 auto 3.5rem; padding: 0 2rem; }
.article-header { margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--color-border); }
.article-header::before { display: none; }
.article-role-badge { display: inline-block; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.1em; padding: 0.25rem 0.75rem; border-radius: 2px; margin-bottom: 0.75rem; text-transform: uppercase; font-family: var(--font-sans); }
.article-title { font-family: var(--font-serif); font-size: clamp(1.5rem, 4vw, 2rem); font-weight: 400; line-height: 1.3; color: var(--color-text); margin-bottom: 0.75rem; }
.article-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; }
.article-score { font-family: var(--font-mono); font-size: 1.5rem; font-weight: 400; color: var(--color-text); }
.article-score small { font-size: 0.8rem; color: var(--color-text-muted); margin-left: 0.1rem; }
.article-dims { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.dim-chip { font-family: var(--font-mono); font-size: 0.7rem; background: var(--color-quote-bg); color: var(--color-text-muted); padding: 0.15rem 0.4rem; border-radius: 2px; border: 1px solid var(--color-border-light); }
.article-notice { margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }
.article-notice span { font-size: 0.72rem; color: #8b4513; background: #fffaf0; padding: 0.15rem 0.5rem; border-radius: 2px; border: 1px solid #deb887; }

.article-body { font-size: 1.05rem; line-height: var(--line-height); color: var(--color-text); }
.section-heading { font-family: var(--font-serif); font-size: 1.3rem; font-weight: 400; color: var(--color-text); margin: 2.5rem 0 1rem; padding-left: 0.75rem; border-left: 3px solid var(--role-color, #666); line-height: 1.4; }
.subsection-heading { font-family: var(--font-serif); font-size: 1.05rem; font-weight: 600; color: #333; margin: 2rem 0 0.75rem; border-bottom: 1px solid var(--color-border-light); padding-bottom: 0.3rem; }
.article-body p { margin-bottom: 1.3em; text-align: justify; overflow-wrap: break-word; text-indent: 2em; }
.article-body p:first-of-type { text-indent: 0; }
.key-terms { background: var(--color-quote-bg); border-left: 3px solid var(--role-color, #666); padding: 0.75rem 1.25rem; margin: 1.5rem 0; border-radius: 0 4px 4px 0; font-size: 0.9rem; color: #444; line-height: 1.7; }
.article-divider { border: none; border-top: 1px solid var(--color-border); margin: 2.5rem 0; }
.list-item { margin: 0.5rem 0; padding-left: 1.5em; position: relative; font-size: 1rem; }
.list-item::before { content: '—'; position: absolute; left: 0.3em; color: var(--role-color, #666); }
.article-footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--color-border-light); text-align: right; }
.article-word-count { font-size: 0.75rem; color: var(--color-text-muted); font-family: var(--font-mono); }
.source-ref { font-family: var(--font-mono); font-size: 0.7em; font-weight: 700; vertical-align: super; cursor: help; text-decoration: none; }

.backcover { max-width: var(--max-width); margin: 0 auto 3rem; padding: 3rem 2rem; background: var(--color-cover-bg); color: var(--color-cover-text); text-align: center; }
.backcover-divider { color: rgba(248,248,242,0.3); letter-spacing: 0.5em; margin: 2rem 0; font-size: 0.9rem; }
.backcover-heading { font-family: var(--font-serif); font-size: 1.2rem; font-weight: 400; color: rgba(248,248,242,0.8); margin-bottom: 1.5rem; letter-spacing: 0.1em; }
.backcover-summary { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 2rem; text-align: left; max-width: 480px; margin-left: auto; margin-right: auto; }
.summary-item { display: grid; grid-template-columns: 5rem 1fr auto; align-items: center; gap: 0.75rem; font-size: 0.85rem; color: rgba(248,248,242,0.7); }
.summary-badge { font-size: 0.6rem; font-weight: 700; padding: 0.15rem 0.4rem; border-radius: 2px; color: #fff; white-space: nowrap; text-align: center; }
.summary-score { font-family: var(--font-mono); font-size: 0.8rem; font-weight: 400; color: #8fbc8f; white-space: nowrap; }
.backcover-next { margin: 1.5rem 0; }
.next-badge { display: inline-block; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; background: var(--color-cover-accent); color: var(--color-cover-bg); padding: 0.25rem 0.8rem; border-radius: 2px; margin-bottom: 0.75rem; }
.backcover-next p { font-size: 0.9rem; color: rgba(248,248,242,0.7); line-height: 1.6; }
.backcover-footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid rgba(248,248,242,0.1); }
.backcover-copyright { font-size: 0.72rem; color: rgba(248,248,242,0.3); line-height: 1.7; }

@media (max-width: 600px) {
    .cover { min-height: auto; padding: 3rem 1.5rem; }
    .cover-title { font-size: 2.5rem; }
    .toc-item { grid-template-columns: 2rem 1fr; }
    .toc-item-badge { display: none; }
}
@media print { body { background: #fff; color: #000; } .cover { background: var(--color-cover-bg) !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
"""

# ============================================================
# 风格3: Dark Mode (暗色模式) — 对标 Wired
# ============================================================
STYLE_DARK_V15 = """
/* ── Dark Mode: Wired / 科技暗色风格 (v1.5) ─────────────── */
:root {
    --font-serif: "Noto Serif SC", "Source Han Serif CN", "SimSun", serif;
    --font-sans: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    --font-mono: "JetBrains Mono", "Fira Code", monospace;
    --line-height: 1.8;
    --max-width: 800px;
    --color-bg: #0d0d0d;
    --color-text: #e0e0e0;
    --color-text-muted: #888;
    --color-border: #2a2a2a;
    --color-border-light: #1a1a1a;
    --color-quote-bg: #161616;
    --color-cover-bg: #000;
    --color-cover-text: #fff;
    --color-cover-accent: #ff3c00;
}
body { font-family: var(--font-sans); background: var(--color-bg); color: var(--color-text); line-height: var(--line-height); -webkit-font-smoothing: antialiased; }
::selection { background: rgba(255,60,0,0.2); color: inherit; }
.magazine-container { max-width: var(--max-width); margin: 0 auto; padding: 0 1.5rem; }

.cover { background: var(--color-cover-bg); color: var(--color-cover-text); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 4rem 2rem; margin-bottom: 4rem; position: relative; overflow: hidden; }
.cover::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse at 20% 50%, rgba(255,60,0,0.12) 0%, transparent 60%), radial-gradient(ellipse at 80% 30%, rgba(255,200,0,0.06) 0%, transparent 50%); pointer-events: none; }
.cover-inner { max-width: 600px; text-align: center; position: relative; z-index: 1; }
.cover-issue { font-family: var(--font-mono); font-size: 0.65rem; letter-spacing: 0.5em; text-transform: uppercase; color: rgba(255,255,255,0.3); margin-bottom: 2rem; }
.cover-title { font-family: var(--font-serif); font-size: clamp(3rem, 9vw, 5.5rem); font-weight: 900; color: #fff; letter-spacing: 0.02em; line-height: 1; margin-bottom: 1.5rem; text-transform: uppercase; }
.cover-topic { font-family: var(--font-serif); font-size: clamp(1.1rem, 3vw, 1.4rem); color: var(--color-cover-accent); font-weight: 600; line-height: 1.5; margin-bottom: 1rem; }
.cover-editor-note { background: rgba(255,255,255,0.03); border-left: 3px solid var(--color-cover-accent); padding: 1rem 1.5rem; text-align: left; margin: 1.5rem 0; }
.cover-editor-label { display: block; font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.3); margin-bottom: 0.5rem; }
.cover-editor-note p { font-size: 0.9rem; line-height: 1.7; color: rgba(255,255,255,0.7); }
.cover-date { font-size: 0.6rem; color: rgba(255,255,255,0.15); letter-spacing: 0.15em; margin-top: 2rem; text-transform: uppercase; }

.toc { max-width: var(--max-width); margin: 0 auto 3rem; padding: 0 1.5rem; }
.toc-header { display: flex; align-items: baseline; gap: 1rem; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--color-border); }
.toc-header h2 { font-family: var(--font-serif); font-size: 1.5rem; font-weight: 700; color: #fff; text-transform: uppercase; letter-spacing: 0.05em; }
.toc-issue { font-size: 0.7rem; color: var(--color-text-muted); font-family: var(--font-mono); }
.toc-list { display: flex; flex-direction: column; gap: 0; }
.toc-item { display: grid; grid-template-columns: 2.5rem 1fr; align-items: center; gap: 1rem; padding: 1rem 0; border-bottom: 1px solid var(--color-border-light); }
.toc-item:hover { background: rgba(255,255,255,0.02); margin: 0 -0.5rem; padding-left: 0.5rem; padding-right: 0.5rem; border-radius: 4px; }
.toc-item-num { font-family: var(--font-mono); font-size: 0.9rem; color: var(--color-cover-accent); text-align: center; font-weight: 700; }
.toc-item-badge { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.05em; padding: 0.25rem 0.6rem; border-radius: 2px; white-space: nowrap; }
.toc-item-title { font-family: var(--font-serif); font-size: 1rem; font-weight: 500; color: #ccc; line-height: 1.4; }

.article { max-width: var(--max-width); margin: 0 auto 3rem; padding: 0 1.5rem; }
.article-header { margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--color-border); position: relative; }
.article-header::before { content: ''; position: absolute; bottom: -1px; left: 0; width: 40px; height: 2px; background: var(--role-color, #666); }
.article-role-badge { display: inline-block; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.1em; padding: 0.25rem 0.6rem; border-radius: 2px; margin-bottom: 0.75rem; text-transform: uppercase; }
.article-title { font-family: var(--font-serif); font-size: clamp(1.4rem, 4vw, 1.9rem); font-weight: 700; line-height: 1.25; color: #f0f0f0; margin-bottom: 0.75rem; }
.article-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; }
.article-score { font-family: var(--font-mono); font-size: 1.4rem; font-weight: 700; color: #f0f0f0; }
.article-score small { font-size: 0.8rem; color: var(--color-text-muted); margin-left: 0.1rem; }
.article-dims { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.dim-chip { font-family: var(--font-mono); font-size: 0.7rem; background: var(--color-quote-bg); color: #888; padding: 0.15rem 0.4rem; border-radius: 2px; border: 1px solid var(--color-border); }
.article-notice { margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }
.article-notice span { font-size: 0.72rem; color: #ff8c00; background: rgba(255,140,0,0.1); padding: 0.15rem 0.5rem; border-radius: 2px; border: 1px solid rgba(255,140,0,0.3); }

.article-body { font-size: 1rem; line-height: var(--line-height); color: #ccc; }
.section-heading { font-family: var(--font-serif); font-size: 1.25rem; font-weight: 700; color: #f0f0f0; margin: 2.5rem 0 1rem; padding-left: 0.75rem; border-left: 3px solid var(--role-color, #666); line-height: 1.4; }
.subsection-heading { font-family: var(--font-serif); font-size: 1.05rem; font-weight: 600; color: #aaa; margin: 2rem 0 0.75rem; border-bottom: 1px solid var(--color-border-light); padding-bottom: 0.3rem; }
.article-body p { margin-bottom: 1.2em; overflow-wrap: break-word; }
.article-body p:first-of-type { text-indent: 0; }
.key-terms { background: var(--color-quote-bg); border-left: 3px solid var(--role-color, #666); padding: 0.75rem 1.25rem; margin: 1.5rem 0; border-radius: 0 4px 4px 0; font-size: 0.9rem; color: #999; line-height: 1.7; }
.article-divider { border: none; border-top: 1px solid var(--color-border); margin: 2.5rem 0; }
.list-item { margin: 0.5rem 0; padding-left: 1.5em; position: relative; font-size: 0.95rem; color: #bbb; }
.list-item::before { content: '//'; position: absolute; left: 0; color: var(--role-color, #666); font-weight: 600; font-family: var(--font-mono); font-size: 0.8rem; }
.article-footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--color-border-light); text-align: right; }
.article-word-count { font-size: 0.75rem; color: #666; font-family: var(--font-mono); }
.source-ref { font-family: var(--font-mono); font-size: 0.7em; font-weight: 700; vertical-align: super; cursor: help; text-decoration: none; padding: 0 0.1em; color: var(--role-color, #888); }

.backcover { max-width: var(--max-width); margin: 0 auto 3rem; padding: 4rem 2rem; background: var(--color-cover-bg); color: var(--color-cover-text); text-align: center; border-top: 4px solid var(--color-cover-accent); }
.backcover-divider { color: rgba(255,255,255,0.1); letter-spacing: 0.5em; margin: 2rem 0; font-size: 0.9rem; }
.backcover-heading { font-family: var(--font-serif); font-size: 1.2rem; font-weight: 700; color: rgba(255,255,255,0.8); margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 0.1em; }
.backcover-summary { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 2rem; text-align: left; max-width: 500px; margin-left: auto; margin-right: auto; }
.summary-item { display: grid; grid-template-columns: 5rem 1fr auto; align-items: center; gap: 0.75rem; font-size: 0.85rem; color: rgba(255,255,255,0.5); }
.summary-badge { font-size: 0.6rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 2px; color: #000; white-space: nowrap; text-align: center; }
.summary-score { font-family: var(--font-mono); font-size: 0.8rem; font-weight: 700; color: #ff6b35; white-space: nowrap; }
.backcover-next { margin: 1.5rem 0; }
.next-badge { display: inline-block; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; background: var(--color-cover-accent); color: #fff; padding: 0.3rem 1rem; border-radius: 2px; margin-bottom: 0.75rem; }
.backcover-next p { font-size: 0.9rem; color: rgba(255,255,255,0.5); line-height: 1.6; }
.backcover-footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.05); }
.backcover-copyright { font-size: 0.72rem; color: rgba(255,255,255,0.15); line-height: 1.7; }

@media (max-width: 600px) {
    .cover { min-height: auto; padding: 3rem 1.5rem; }
    .cover-title { font-size: 2.5rem; }
    .toc-item { grid-template-columns: 2rem 1fr; }
    .toc-item-badge { display: none; }
}
@media print {
    body { background: #fff; color: #000; }
    .cover { background: #000 !important; color: #fff !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .article-title, .section-heading { color: #000; }
}
"""

# ============================================================
# 风格4: Print Magazine (印刷杂志) — 对标 Quanta
# ============================================================
STYLE_PRINT_V15 = """
/* ── Print Magazine: Quanta 风格 (v1.5) ─────────────────── */
:root {
    --font-serif: "Noto Serif SC", "Source Han Serif CN", "SimSun", serif;
    --font-sans: "Noto Serif SC", "Source Han Serif CN", "SimSun", serif;
    --font-mono: "Courier New", "Courier", monospace;
    --line-height: 1.75;
    --max-width: 680px;
    --color-bg: #fdfcfa;
    --color-text: #222;
    --color-text-muted: #666;
    --color-border: #ccc;
    --color-border-light: #e8e8e4;
    --color-quote-bg: #f5f4f0;
    --color-cover-bg: #2d3436;
    --color-cover-text: #ffeaa7;
    --color-cover-accent: #d63031;
}
body { font-family: var(--font-serif); background: var(--color-bg); color: var(--color-text); line-height: var(--line-height); -webkit-font-smoothing: antialiased; }
::selection { background: rgba(214,48,49,0.1); color: inherit; }
.magazine-container { max-width: var(--max-width); margin: 0 auto; padding: 0 1.5rem; }

.cover { background: var(--color-cover-bg); color: var(--color-cover-text); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 4rem 2rem; margin-bottom: 4rem; position: relative; }
.cover::before { content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 70% 30%, rgba(214,48,49,0.2) 0%, transparent 50%); pointer-events: none; }
.cover-inner { max-width: 520px; text-align: center; position: relative; z-index: 1; }
.cover-issue { font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.3em; text-transform: uppercase; color: rgba(255,234,167,0.4); margin-bottom: 2rem; border-bottom: 1px solid rgba(255,234,167,0.2); padding-bottom: 1rem; }
.cover-title { font-family: var(--font-serif); font-size: clamp(2.8rem, 7vw, 4.5rem); font-weight: 700; color: var(--color-cover-text); letter-spacing: 0.15em; line-height: 1.15; margin-bottom: 2rem; }
.cover-topic { font-family: var(--font-serif); font-size: clamp(1rem, 2.5vw, 1.25rem); color: var(--color-cover-text); font-weight: 400; line-height: 1.7; margin-bottom: 1.5rem; opacity: 0.9; }
.cover-editor-note { border: 1px solid rgba(255,234,167,0.2); padding: 1rem 1.5rem; text-align: left; margin: 1.5rem 0; }
.cover-editor-label { display: block; font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,234,167,0.4); margin-bottom: 0.5rem; }
.cover-editor-note p { font-size: 0.9rem; line-height: 1.7; color: rgba(255,234,167,0.8); }
.cover-date { font-size: 0.6rem; color: rgba(255,234,167,0.2); letter-spacing: 0.15em; margin-top: 2rem; text-transform: uppercase; }

.toc { max-width: var(--max-width); margin: 0 auto 3rem; padding: 0 1.5rem; }
.toc-header { display: flex; align-items: baseline; gap: 1rem; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid var(--color-border); }
.toc-header h2 { font-family: var(--font-serif); font-size: 1.6rem; font-weight: 700; color: var(--color-text); letter-spacing: 0.1em; }
.toc-issue { font-size: 0.7rem; color: var(--color-text-muted); font-style: italic; }
.toc-list { display: flex; flex-direction: column; gap: 0; }
.toc-item { display: grid; grid-template-columns: 2rem 5rem 1fr; align-items: start; gap: 0.75rem; padding: 1rem 0; border-bottom: 1px solid var(--color-border-light); }
.toc-item:last-child { border-bottom: none; }
.toc-item-num { font-family: var(--font-mono); font-size: 0.8rem; color: var(--color-text-muted); padding-top: 0.2rem; }
.toc-item-badge { font-size: 0.55rem; font-weight: 700; letter-spacing: 0.05em; padding: 0.2rem 0.4rem; border-radius: 1px; white-space: nowrap; font-family: var(--font-sans); }
.toc-item-title { font-family: var(--font-serif); font-size: 0.95rem; font-weight: 400; color: var(--color-text); line-height: 1.4; }

.article { max-width: var(--max-width); margin: 0 auto 3.5rem; padding: 0 1.5rem; }
.article-header { margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--color-border); }
.article-header::before { display: none; }
.article-role-badge { display: inline-block; font-size: 0.55rem; font-weight: 700; letter-spacing: 0.15em; padding: 0.2rem 0.6rem; border-radius: 1px; margin-bottom: 0.75rem; text-transform: uppercase; }
.article-title { font-family: var(--font-serif); font-size: clamp(1.4rem, 4vw, 1.9rem); font-weight: 700; line-height: 1.25; color: var(--color-text); margin-bottom: 0.75rem; letter-spacing: 0.02em; }
.article-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; }
.article-score { font-family: var(--font-mono); font-size: 1.3rem; font-weight: 700; color: var(--color-text); }
.article-score small { font-size: 0.75rem; color: var(--color-text-muted); margin-left: 0.1rem; }
.article-dims { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.dim-chip { font-family: var(--font-mono); font-size: 0.65rem; background: var(--color-quote-bg); color: var(--color-text-muted); padding: 0.15rem 0.4rem; border-radius: 1px; border: 1px solid var(--color-border-light); }
.article-notice { margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }
.article-notice span { font-size: 0.7rem; color: #8b4513; background: #fff8f0; padding: 0.15rem 0.5rem; border-radius: 1px; border: 1px solid #d4a574; }

.article-body { font-size: 1rem; line-height: var(--line-height); color: var(--color-text); }
.section-heading { font-family: var(--font-serif); font-size: 1.2rem; font-weight: 700; color: var(--color-text); margin: 2.5rem 0 1rem; padding-left: 0.75rem; border-left: 3px solid var(--role-color, #666); line-height: 1.4; letter-spacing: 0.05em; }
.subsection-heading { font-family: var(--font-serif); font-size: 1rem; font-weight: 600; color: #333; margin: 2rem 0 0.75rem; border-bottom: 1px solid var(--color-border-light); padding-bottom: 0.3rem; }
.article-body p { margin-bottom: 1.2em; text-align: justify; overflow-wrap: break-word; text-indent: 2em; }
.article-body p:first-of-type { text-indent: 0; }
.key-terms { background: var(--color-quote-bg); border-left: 3px solid var(--role-color, #666); padding: 0.75rem 1.25rem; margin: 1.5rem 0; border-radius: 0 3px 3px 0; font-size: 0.88rem; color: #444; line-height: 1.7; }
.article-divider { border: none; border-top: 1px solid var(--color-border); margin: 2.5rem 0; }
.list-item { margin: 0.5rem 0; padding-left: 1.5em; position: relative; font-size: 0.95rem; }
.list-item::before { content: '•'; position: absolute; left: 0.4em; color: var(--role-color, #666); font-weight: 700; }
.article-footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--color-border-light); text-align: right; }
.article-word-count { font-size: 0.7rem; color: var(--color-text-muted); font-family: var(--font-mono); }
.source-ref { font-family: var(--font-mono); font-size: 0.7em; font-weight: 700; vertical-align: super; cursor: help; text-decoration: none; }

.backcover { max-width: var(--max-width); margin: 0 auto 3rem; padding: 3rem 1.5rem; background: var(--color-cover-bg); color: var(--color-cover-text); text-align: center; }
.backcover-divider { color: rgba(255,234,167,0.2); letter-spacing: 0.5em; margin: 2rem 0; font-size: 0.9rem; }
.backcover-heading { font-family: var(--font-serif); font-size: 1.1rem; font-weight: 700; color: rgba(255,234,167,0.8); margin-bottom: 1.5rem; letter-spacing: 0.15em; text-transform: uppercase; }
.backcover-summary { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 2rem; text-align: left; max-width: 450px; margin-left: auto; margin-right: auto; }
.summary-item { display: grid; grid-template-columns: 5rem 1fr auto; align-items: center; gap: 0.75rem; font-size: 0.8rem; color: rgba(255,234,167,0.6); }
.summary-badge { font-size: 0.55rem; font-weight: 700; padding: 0.15rem 0.4rem; border-radius: 1px; color: var(--color-cover-bg); white-space: nowrap; text-align: center; }
.summary-score { font-family: var(--font-mono); font-size: 0.75rem; font-weight: 700; color: #ffeaa7; white-space: nowrap; }
.backcover-next { margin: 1.5rem 0; }
.next-badge { display: inline-block; font-size: 0.55rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; background: var(--color-cover-accent); color: var(--color-cover-text); padding: 0.25rem 0.8rem; border-radius: 1px; margin-bottom: 0.75rem; }
.backcover-next p { font-size: 0.85rem; color: rgba(255,234,167,0.6); line-height: 1.6; }
.backcover-footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,234,167,0.1); }
.backcover-copyright { font-size: 0.7rem; color: rgba(255,234,167,0.2); line-height: 1.7; }

@media (max-width: 600px) {
    .cover { min-height: auto; padding: 3rem 1.5rem; }
    .cover-title { font-size: 2.5rem; }
    .toc-item { grid-template-columns: 2rem 1fr; }
    .toc-item-badge { display: none; }
}
@media print { body { background: #fff; color: #000; } .cover { background: var(--color-cover-bg) !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
"""

# ============================================================
# 辅助函数
# ============================================================
def extract_body(html: str) -> str:
    """提取<body>内容"""
    match = re.search(r'<body>(.*)</body>', html, re.DOTALL)
    return match.group(1) if match else html

def extract_fonts(html: str) -> str:
    """提取字体link"""
    match = re.search(r'(<link[^>]*fonts[^>]*>)', html, re.DOTALL)
    return match.group(1) if match else ""

def build_variant(html: str, style_css: str, variant_name: str, variant_key: str) -> str:
    """构建变体HTML"""
    body_content = extract_body(html)
    fonts = extract_fonts(html)

    new_html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>科学前沿 2026-Q3 — {variant_name}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
/* {variant_name} */
{style_css}
</style>
</head>
<body>
{body_content}
</body>
</html>"""
    return new_html

def main():
    output_dir = MAGAZINE_DIR / "variants"
    output_dir.mkdir(exist_ok=True)

    variants = [
        ("modern", "现代数字 (MIT Tech Review)", STYLE_MODERN_V15),
        ("classic", "学术经典 (Nature)", STYLE_CLASSIC_V15),
        ("print", "印刷杂志 (Quanta)", STYLE_PRINT_V15),
        ("dark", "暗色模式 (Wired)", STYLE_DARK_V15),
    ]

    for key, name, style in variants:
        html = build_variant(src_html, style, name, key)
        out_path = output_dir / f"magazine_2026-Q3_{key}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"[OK] Generated: {out_path.name} ({len(html)//1024}KB)")

    print(f"\n[Done] All 4 style variants regenerated in: {output_dir}")
    print("[INFO] Modern style is now the default (first variant)")

if __name__ == "__main__":
    main()
