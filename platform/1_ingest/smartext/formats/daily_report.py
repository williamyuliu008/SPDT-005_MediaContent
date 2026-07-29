"""
SmartText — 日报内容形态模板
================================
AI 瞭望台日报：4 板块 + 热度图 + 一句话归档

从 Signal Bundle 中提取信号，按板块分组，调用相应集群生成内容，
最终渲染为 Markdown 格式的日报。

数据源: Signal Bundle (来自 Radar Platform)
输出: channels/YYYY-MM-DD.md
"""

from datetime import datetime

# ═══════════════════════════════════════
# 日报板块定义
# ═══════════════════════════════════════

FORMAT_SPEC = {
    "name": "AI 瞭望台日报",
    "description": "Stratechery 式每日一更：4 板块 + 热度图 + 信号归档",
    "input_signal_types": ["capability", "structural", "supply_chain", "ecosystem"],
    "output_format": "markdown",
    "sections": [
        {
            "id": "compete",
            "label": "竞争态势",
            "emoji": "📊",
            "cluster": "deepprod",
            "signal_type": None,        # 所有信号
            "max_items": 3,
        },
        {
            "id": "chips",
            "label": "芯事",
            "emoji": "📡",
            "cluster": "flashnews",
            "signal_type": "supply_chain",
            "max_items": 3,
        },
        {
            "id": "oss",
            "label": "开源雷达",
            "emoji": "🔬",
            "cluster": "scipop",
            "signal_type": "ecosystem",
            "max_items": 3,
        },
        {
            "id": "design",
            "label": "设计前线",
            "emoji": "🏗",
            "cluster": "creativex",
            "signal_type": None,
            "max_items": 2,
            "condition": "design_day",   # 仅周一/周四发布
        },
    ],
}

# ═══════════════════════════════════════
# 追踪公司 & 标签映射
# ═══════════════════════════════════════

TRACKED_COMPANIES = [
    "openai", "google", "microsoft", "anthropic", "nvidia",
    "bytedance", "baidu", "alibaba", "tencent", "perplexity"
]

COMPANY_NAMES = {
    "openai": "OpenAI", "google": "Google DeepMind", "microsoft": "Microsoft",
    "anthropic": "Anthropic", "nvidia": "NVIDIA", "bytedance": "字节跳动",
    "baidu": "百度", "alibaba": "阿里巴巴", "tencent": "腾讯", "perplexity": "Perplexity"
}

COMPANY_DOMAINS = {
    "openai": "大模型/基础研究", "google": "大模型/搜索/云", "microsoft": "云/AI平台/办公",
    "anthropic": "大模型/安全", "nvidia": "AI芯片/硬件", "bytedance": "大模型/应用/推荐",
    "baidu": "大模型/自动驾驶", "alibaba": "云/大模型/开源", "tencent": "大模型/社交/游戏",
    "perplexity": "AI搜索/Agent"
}

# 关键词分类（兼容旧 daily.py 的 classify_signal 逻辑）
SECTION_KEYWORDS = {
    "chips": ["GPU", "HBM", "CoWoS", "TSMC", "芯片", "算力", "Blackwell", "H100", "B200",
              "供应链", "产能", "出口管制", "光刻", "ASML", "封装", "HBM3", "N3", "N2",
              "petaflop", "Grace", "CUDA", "DGX", "spark", "edge_ai", "personal_agents"],
    "oss": ["开源", "open_source", "github", "huggingface", "Llama", "Mistral", "Qwen",
            "DeepSeek", "模型权重", "Apache", "MIT", "GPL", "衍生模型", "下载量",
            "open-sourced", "OSI", "openweight", "open_model", "open_weights", "SDK"],
    "design": ["UX", "UI", "设计", "交互", "Copilot", "ChatGPT", "Claude", "Agent",
               "卡片", "对话式", "多模态", "voice", "notebook", "code", "product_hunt",
               "cursor", "granola", "lovable", "devtool", "super_app", "personal_agent"],
}


def classify_signal(signal: dict) -> str:
    """
    关键词分类：将信号分到 chips / oss / design / compete 板块。
    与旧版 channels/daily.py 的 classify_signal() 逻辑一致。
    """
    title = (signal.get("title", "") + " " + " ".join(signal.get("tags", []))).lower()
    summary = signal.get("summary", "").lower()
    text = title + " " + summary
    
    if any(kw.lower() in text for kw in SECTION_KEYWORDS["chips"]):
        return "chips"
    if any(kw.lower() in text for kw in SECTION_KEYWORDS["oss"]):
        return "oss"
    if any(kw.lower() in text for kw in SECTION_KEYWORDS["design"]):
        return "design"
    return "compete"


def _is_design_day(date_str: str) -> bool:
    """设计前线仅在周一/周四发布"""
    try:
        wd = datetime.strptime(date_str, "%Y-%m-%d").weekday()
        return wd in (0, 3)  # Monday=0, Thursday=3
    except ValueError:
        return True


def _get_day_name(date_str: str) -> str:
    """获取中文星期名"""
    try:
        return ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][
            datetime.strptime(date_str, "%Y-%m-%d").weekday()
        ]
    except ValueError:
        return ""


def format_signal_card(signal: dict, max_summary: int = 150) -> str:
    """格式化单条信号为 Markdown 卡片"""
    company = signal.get("company", "")
    company_name = COMPANY_NAMES.get(company, company)
    domain = COMPANY_DOMAINS.get(company, "")
    title = signal.get("title", "N/A")
    summary = signal.get("summary", "")
    score = signal.get("importance_score", 0.0)
    
    if len(summary) > max_summary:
        summary = summary[:max_summary].rsplit(" ", 1)[0] + "…"
    
    meta = f"{company_name} · {domain}" if domain else company_name
    return f"**{title}**\n{summary}\n\n> {meta} | 影响力 {score:.2f}\n"


def render(content_bundle: dict, **options) -> str:
    """
    将 Content Bundle 渲染为完整的日报 Markdown。
    
    Args:
        content_bundle: SmartTextEngine.generate() 的输出
        **options: 额外选项（如 --date）
    
    Returns:
        日报 Markdown 字符串
    """
    date_str = content_bundle.get("date", options.get("date", datetime.now().strftime("%Y-%m-%d")))
    day_name = _get_day_name(date_str)
    
    signals = content_bundle.get("meta", {})
    sections = content_bundle.get("sections", [])
    heat_data = content_bundle.get("heat", {})
    
    # 头部
    total_signals = signals.get("signals_processed", 0)
    covered = set()
    for section in sections:
        for sig_id in section.get("signals", []):
            covered.add(sig_id)
    coverage = len(covered)
    
    header = f"# 🔭 AI 瞭望台 · {date_str} {day_name}\n\n"
    header += f"> 信号 {total_signals} 条 · 覆盖 {min(coverage, 10)}/10 家公司\n\n"
    
    # 各板块内容
    body_parts = []
    for section in sections:
        section_id = section.get("section_id", "")
        emoji = ""
        for sect_spec in FORMAT_SPEC["sections"]:
            if sect_spec["id"] == section_id:
                emoji = sect_spec.get("emoji", "")
                break
        
        content = section.get("content", "")
        if not content.strip():
            continue
        
        # 确保内容有二级标题
        if not content.startswith("##"):
            content = f"## {emoji} {section.get('label', section_id)}\n\n{content}"
        
        body_parts.append(content)
    
    body = "\n\n".join(body_parts)
    
    # 热度统计
    top_tags = heat_data.get("top_tags", [])
    heat_lines = ["## 📊 今日信号热度\n"]
    if top_tags:
        max_v = top_tags[0]["count"]
        for item in top_tags[:8]:
            tag, cnt = item["tag"], item["count"]
            bar_len = int(cnt / max_v * 20) if max_v > 0 else 0
            heat_lines.append(f"`{tag}` {'▓' * bar_len}{'░' * (20 - bar_len)} {cnt}\n")
    else:
        heat_lines.append("_信号累积中…_\n")
    
    heat = "\n".join(heat_lines)
    
    # 页脚
    footer = f"\n\n---\n*AI 瞭望台 · SmartTextPlatform 自动生成 · {date_str} · 追踪 10 家 AI 核心公司*"
    
    return header + body + "\n\n" + heat + footer
