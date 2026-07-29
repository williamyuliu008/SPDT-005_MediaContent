#!/usr/bin/env python3
"""
channels/website/build.py — 网站构建脚本
=========================================
从 SmartTextPlatform channels/ 目录读取日报 Markdown，渲染为完整 HTML 网站页面。

用法: python build.py --date YYYY-MM-DD
"""

import json
import re
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path


# ── 路径配置 ────────────────────────────────────────────────

# SmartTextPlatform 项目根目录（日报 Markdown 来源）
SMARTTEXT_ROOT = Path("D:/92_products/SmartTextPlatform")
CHANNELS_DIR = SMARTTEXT_ROOT / "channels"

# 网站部署目标目录
SITE_ROOT = SMARTTEXT_ROOT / "canvas" / "ai-lookout"

# 静态资源路径（相对于 SITE_ROOT）
CSS_PATH = "assets/css/style.css"
FLEXSEARCH_CDN = "https://cdn.jsdelivr.net/npm/flexsearch@0.7.31/dist/flexsearch.bundle.js"


# ── HTML 模板 ───────────────────────────────────────────────

NAV_HTML = """<header>
    <div class="header-inner">
        <a href="/" class="logo"><span class="icon">🔭</span>AI 瞭望台<span class="subtitle">· AI 产业情报自动化</span></a>
        <nav>
            <a href="/" class="active">今日</a>
            <a href="/archive/">📂 归档</a>
            <a href="/search/">🔍 搜索</a>
            <a href="/knowledge/">🧠 知识</a>
        </nav>
    </div>
</header>"""

FOOTER_HTML = """<footer>
    <p>AI 瞭望台 · SmartTextPlatform 自动化运营</p>
    <p>追踪 10 家 AI 核心公司 · 每日 10:30 自动更新</p>
</footer>"""


# ── Markdown → HTML 转换 ───────────────────────────────────

def md_to_html(md_text: str) -> str:
    """简易 Markdown → HTML"""
    lines = md_text.split('\n')
    html = []
    in_table = False
    in_code = False
    code_lines = []

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


# ── 搜索索引构建 ───────────────────────────────────────────

def _section_to_channel(section: str) -> str:
    if '竞争' in section: return 'compete'
    if '芯事' in section: return 'chips'
    if '开源' in section: return 'oss'
    if '设计' in section: return 'design'
    return 'compete'


def _extract_tags(text: str) -> list[str]:
    keywords = ["hardware","edge_ai","GPU","开源","open_source","IPO","model_release",
                "enterprise","agent","safety","compute","supply_chain","multimodal",
                "Mythos","frontier","Copilot","Gemini","Llama","AI芯片","大模型",
                "price_change","funding","product_launch","partnership"]
    return [k for k in keywords if k.lower() in text.lower()][:5]


def build_index(date_str: str) -> dict:
    """构建搜索索引（含完整字段）"""
    md_path = CHANNELS_DIR / f"{date_str}.md"
    if not md_path.exists():
        return {"channels": {}, "latest_date": date_str}

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取各板块信号
    current_section = None
    current_signal = None
    signals = []

    for line in content.split('\n'):
        if line.startswith('## '):
            current_section = line[3:].strip()
            continue
        if line.startswith('**') and line.endswith('**'):
            if current_signal:
                signals.append(current_signal)
            current_signal = {
                "section": current_section or "other",
                "title": line.strip('*').strip(),
                "summary": "",
                "meta": "",
                "importance_score": 0.0,
            }
            continue
        if current_signal:
            if line.startswith('> ') and '影响力' in line:
                m = re.search(r'影响力\s*([\d.]+)', line)
                if m:
                    current_signal["importance_score"] = float(m.group(1))
                current_signal["meta"] = line[2:].strip()
            elif not line.startswith('>') and not line.startswith('#') and line.strip():
                current_signal["summary"] += line.strip() + " "

    if current_signal:
        signals.append(current_signal)

    # 构建索引条目
    items = []
    companies_seen = set()
    tags_seen = set()

    for sig in signals:
        item = {
            "date": date_str,
            "title": sig["title"],
            "summary": sig["summary"].strip()[:200],
            "content": sig["summary"].strip(),
            "path": "/#",
            "importance_score": sig.get("importance_score", 0.0),
            "sentiment": "positive",
            "companies": [w for w in sig["title"].split() if w in {"NVIDIA","OpenAI","Google","Microsoft","Anthropic","字节跳动","百度","阿里巴巴","腾讯","Perplexity"}],
            "tags": _extract_tags(sig["title"] + " " + sig["summary"]),
            "section": sig.get("section", ""),
        }
        items.append(item)
        for c in item["companies"]: companies_seen.add(c)
        for t in item["tags"]: tags_seen.add(t)

    return {
        "build_time": datetime.now().isoformat(),
        "latest_date": date_str,
        "total_signals": len(items),
        "companies_covered": len(companies_seen),
        "items": items,
    }


# ── 主流程 ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI瞭望台网站构建")
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    args = parser.parse_args()
    date_str = args.date

    # 1. 读取日报
    md_path = CHANNELS_DIR / f"{date_str}.md"
    if not md_path.exists():
        print(f"❌ 日报未找到: {md_path}")
        sys.exit(1)

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 2. 提取标题中的日期用于显示
    title_match = re.search(r'# 🔭 AI 瞭望台 · (.+)', md_content)
    display_date = title_match.group(1) if title_match else date_str

    # 3. 构建 HTML
    body_html = md_to_html(md_content)

    # 4. 日期导航
    today = datetime.strptime(date_str, '%Y-%m-%d')
    yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    tomorrow = (today + timedelta(days=1)).strftime('%Y-%m-%d')

    nav_dates = f"""
    <div class="date-nav">
        <a href="/?date={yesterday}">← 前一天</a>
        <span class="date-nav-current">{display_date}</span>
        <a href="/?date={tomorrow}">后一天 →</a>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 瞭望台 · {date_str}</title>
    <link rel="stylesheet" href="{CSS_PATH}">
    <script src="{FLEXSEARCH_CDN}"></script>
</head>
<body>
{NAV_HTML}
<main>
    {nav_dates}
    <article class="daily-report">
        {body_html}
    </article>
    {nav_dates}
</main>
{FOOTER_HTML}
</body>
</html>"""

    # 5. 写入 HTML
    out_path = SITE_ROOT / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # 6. 构建搜索索引
    idx = build_index(date_str)
    idx_path = SITE_ROOT / "search" / "index.json"
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    with open(idx_path, 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

    print(f"✅ 网站: {out_path}")
    print(f"✅ 索引: {idx_path} ({idx['total_signals']} 条信号)")


if __name__ == '__main__':
    main()
