"""
SmartText — 公众号文章内容形态模板（占位）
==============================================
后续 Phase 3 实现完整的公众号文章生成流水线。

当前仅定义格式规格，供 SmartTextEngine 注册。
"""

FORMAT_SPEC = {
    "name": "公众号文章",
    "description": "面向微信公众号的长文创作，含标题、导语、正文、CTA",
    "input_signal_types": ["capability", "structural", "ecosystem"],
    "output_format": "markdown",
    "sections": [
        {
            "id": "intro",
            "label": "导语",
            "cluster": "creativex",
            "signal_type": None,
            "max_items": 3,
        },
        {
            "id": "body",
            "label": "正文",
            "cluster": "deepprod",
            "signal_type": "capability",
            "max_items": 5,
        },
        {
            "id": "outro",
            "label": "总结与CTA",
            "cluster": "creativex",
            "signal_type": None,
            "max_items": 2,
        },
    ],
}


def render(content_bundle: dict, **options) -> str:
    """将 Content Bundle 渲染为公众号文章 Markdown（占位实现）"""
    sections = content_bundle.get("sections", [])
    date_str = content_bundle.get("date", "")
    
    parts = [f"# AI 瞭望台 · {date_str}\n"]
    
    for section in sections:
        content = section.get("content", "")
        if content.strip():
            parts.append(content)
    
    parts.append("\n---\n*AI 瞭望台 · 每日精选*")
    
    return "\n\n".join(parts)
