#!/usr/bin/env python3
"""
Radar 信号分类器 — Signal Taxonomy
====================================
将原始 CI Engine 事件按 6 种信号类型自动分类。
策略: 规则匹配（event_type + tags + keywords）→ LLM fallback（未命中规则）

6 种信号类型:
  capability   — 技术能力的阶跃变化 → compete
  structural   — 行业结构的重组变化 → compete, chips
  supply_chain — 硬件/产能/价格变化 → chips
  ecosystem    — 开源/平台/开发者变化 → oss
  paradigm     — 交互模式/设计语言变化 → design
  risk         — 安全/合规/伦理变化 → (future)

用法:
  from radar.signal_taxonomy import classify, classify_batch
"""

import re
import json
from typing import Optional

# ══════════════════════════════════════════════
# 6 种信号类型定义
# ══════════════════════════════════════════════

SIGNAL_TYPES = [
    "capability",
    "structural",
    "supply_chain",
    "ecosystem",
    "paradigm",
    "risk",
]

# 目标频道映射
TYPE_TO_CHANNEL = {
    "capability": "compete",
    "structural": "compete",       # also routed to chips in dispatch
    "supply_chain": "chips",
    "ecosystem": "oss",
    "paradigm": "design",
    "risk": None,                  # future: public_welfare
}

# ══════════════════════════════════════════════
# 规则库: event_type → signal_type
# ══════════════════════════════════════════════

EVENT_TYPE_RULES = {
    "product_launch": "capability",
    "model_release": "capability",
    "funding": "structural",
    "ipo": "structural",
    "acquisition": "structural",
    "partnership": "structural",
    "personnel": "structural",
    "price_change": "supply_chain",
    "open_source_release": "ecosystem",
    "platform_launch": "ecosystem",
    "regulation": "risk",
    "security_incident": "risk",
    "safety_report": "risk",
}

# ══════════════════════════════════════════════
# 关键词规则: tag/keyword → signal_type
# ══════════════════════════════════════════════

TAG_RULES = {
    "capability": [
        "model_release", "model", "gpt", "gemini", "claude", "llama",
        "mistral", "frontier", "sota", "benchmark", "context_window",
        "reasoning", "multimodal", "flash", "moe", "training",
        "efficiency", "cost_breakthrough", "life_sciences", "vertical_ai",
        "specialized", "drug_discovery", "code_generation", "coding",
    ],
    "structural": [
        "ipo", "capital_markets", "commercialization", "funding",
        "acquisition", "merger", "personnel", "leadership", "layoff",
        "reorganization", "invest", "revenue", "earnings",
    ],
    "supply_chain": [
        "supply_chain", "manufacturing", "产能", "价格", "pricing",
        "hardware", "gpu", "tpu", "chip", "semiconductor", "fabrication",
        "gpu_shortage", "export_control", "china_gpu", "blackwell",
        "grace_blackwell", "h100", "h200", "b200", "edge_ai",
        "personal_agents", "windows", "pc", "compute",
    ],
    "ecosystem": [
        "open_source", "github", "huggingface", "platform",
        "ecosystem", "developer", "api", "sdk", "derived_models",
        "downloads", "community", "oss", "qwen", "deepseek",
        "agent_platform", "coze", "collaboration", "multi_agent",
    ],
    "paradigm": [
        "ux", "design", "interaction", "agent", "super_app",
        "integration", "copilot", "siri", "assistant", "voice",
        "hybrid_inference", "subscription", "consumer", "enterprise",
        "search", "browser", "chat", "personalization",
    ],
    "risk": [
        "safety", "regulation", "security", "ethics", "consciousness",
        "debate", "philosophy", "export_control", "compliance",
        "privacy", "confidential_computing", "data_protection",
    ],
}

# ══════════════════════════════════════════════
# Title/Summary 关键词（中文 + 英文）
# ══════════════════════════════════════════════

TITLE_KEYWORDS = {
    "capability": [
        "发布", "推出", "开源", "release", "launch", "model", "announce",
        "benchmark", "超越", "outperform", "sota", "升级", "upgrade",
    ],
    "structural": [
        "ipo", "上市", "融资", "funding", "收购", "acquisition", "合并",
        "merger", "重组", "restructure", "任命", "appoint", "离职",
        "招股", "s-1", "sec",
    ],
    "supply_chain": [
        "芯片", "chip", "gpu", "tpu", "制程", "量产", "production",
        "降价", "price", "供应", "supply", "产能", "capacity",
        "特供", "出口管制", "export",
    ],
    "ecosystem": [
        "开源", "open source", "github", "huggingface", "平台",
        "platform", "开发者", "developer", "生态", "ecosystem",
        "下载", "download", "衍生", "derived",
    ],
    "paradigm": [
        "交互", "interaction", "体验", "experience", "设计", "design",
        "超级应用", "super app", "copilot", "助手", "assistant",
        "agent", "智能体", "入口", "门户",
    ],
    "risk": [
        "安全", "safety", "监管", "regulation", "合规", "compliance",
        "伦理", "ethics", "意识", "consciousness", "风险", "risk",
        "隐私", "privacy",
    ],
}


def _build_text_blob(event: dict) -> str:
    """构建用于规则匹配的文本块"""
    parts = [
        event.get("event_type", ""),
        event.get("title", ""),
        event.get("summary", ""),
        " ".join(event.get("tags", [])),
        " ".join(event.get("affected_dimensions", [])),
    ]
    return " ".join(parts).lower()


def classify(event: dict) -> str:
    """
    对单条事件分类，返回 signal_type。
    
    优先级: event_type 规则 > tags 规则 > title/summary 关键词 > LLM fallback
    """
    event_type = event.get("event_type", "").lower()
    tags = [t.lower() for t in event.get("tags", [])]
    title = event.get("title", "").lower()
    summary = event.get("summary", "").lower()
    text_blob = _build_text_blob(event)
    
    # ── Level 1: event_type 精确规则 ──
    if event_type in EVENT_TYPE_RULES:
        return EVENT_TYPE_RULES[event_type]
    
    # ── Level 2: tags 关键词规则 ──
    scores = {st: 0 for st in SIGNAL_TYPES}
    for st, keywords in TAG_RULES.items():
        for tag in tags:
            if tag in keywords:
                scores[st] += 3  # tag 精确匹配最高权重
        for kw in keywords:
            if kw in text_blob:
                scores[st] += 1  # 文本模糊匹配
    
    # 找到最高分且有显著优势的类型
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    if ranked[0][1] >= 3 and (ranked[0][1] - ranked[1][1] >= 2):
        return ranked[0][0]
    
    # ── Level 3: title/summary 关键词 ──
    title_scores = {st: 0 for st in SIGNAL_TYPES}
    for st, keywords in TITLE_KEYWORDS.items():
        for kw in keywords:
            if kw in title:
                title_scores[st] += 2
            if kw in summary:
                title_scores[st] += 1
    
    ranked = sorted(title_scores.items(), key=lambda x: -x[1])
    if ranked[0][1] >= 2:
        return ranked[0][0]
    
    # ── Level 4: product_launch 默认 capability ──
    if event_type in ("product_launch", "model_release"):
        return "capability"
    
    # ── Level 5: LLM fallback（未实现时标记为 unclassified）──
    return "unclassified"


def classify_batch(events: list) -> list:
    """批量分类，返回带 signal_type 的事件列表"""
    results = []
    for e in events:
        signal_type = classify(e)
        e["signal_type"] = signal_type
        results.append(e)
    return results


def llm_classify_fallback(event: dict, llm_gateway) -> str:
    """
    LLM fallback 分类（当规则无法确定时）。
    
    使用 shared.llm_gateway 调用 LLM 进行分类。
    返回 signal_type 字符串。
    """
    system_prompt = """你是 AI 竞争情报分类专家。将以下事件归类为 6 种信号类型之一：
- capability: 技术能力的阶跃变化（模型发布、性能突破、新能力）
- structural: 行业结构重组变化（融资、IPO、收购、人事、合作）
- supply_chain: 硬件/产能/价格变化（芯片、制程、供应、定价）
- ecosystem: 开源/平台/开发者生态变化（开源发布、平台建设、社区）
- paradigm: 交互模式/设计语言变化（UX、Agent、超级应用、产品形态）
- risk: 安全/合规/伦理变化（监管、安全事件、伦理争议）

只返回信号类型单词，不要其他内容。"""

    user_prompt = f"""事件类型: {event.get('event_type', '')}
标题: {event.get('title', '')}
摘要: {event.get('summary', '')[:500]}
标签: {', '.join(event.get('tags', []))}
影响维度: {', '.join(event.get('affected_dimensions', []))}

信号类型:"""

    try:
        from shared.llm_gateway import LLMGateway
        gw = llm_gateway or LLMGateway()
        resp = gw.call(system_prompt, user_prompt, max_tokens=16, temperature=0.1)
        result = resp.content.strip().lower()
        # 确保返回有效类型
        for st in SIGNAL_TYPES:
            if st in result:
                return st
        return "unclassified"
    except Exception:
        return "unclassified"


# ══════════════════════════════════════════════
# 统计分析
# ══════════════════════════════════════════════

def classification_stats(events: list) -> dict:
    """分类统计: 每类信号的数量和占比"""
    total = len(events)
    by_type = {}
    for e in events:
        st = e.get("signal_type", "unclassified")
        by_type[st] = by_type.get(st, 0) + 1
    
    return {
        "total": total,
        "by_type": by_type,
        "by_type_pct": {k: round(v / total * 100, 1) for k, v in by_type.items()},
        "unclassified": by_type.get("unclassified", 0),
        "accuracy_estimate": round((total - by_type.get("unclassified", 0)) / total * 100, 1),
    }


# ══════════════════════════════════════════════
# CLI 测试入口
# ══════════════════════════════════════════════

if __name__ == "__main__":
    import os
    
    # 加载 6/17 CI Engine 事件
    events_path = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events\2026-06\0617_extracted.json"
    if os.path.exists(events_path):
        with open(events_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        classified = classify_batch(events)
        stats = classification_stats(classified)
        
        print("=" * 60)
        print("  Radar 信号分类器 — 分类结果")
        print("=" * 60)
        print(f"\n总事件: {stats['total']}")
        print("\n按类型分布:")
        for st in SIGNAL_TYPES + ["unclassified"]:
            count = stats["by_type"].get(st, 0)
            pct = stats["by_type_pct"].get(st, 0)
            print(f"  {st:20s} {count:3d} 条 ({pct}%)")
        
        print(f"\n未分类: {stats['unclassified']} 条")
        print(f"规则覆盖率: {stats['accuracy_estimate']}%")
        
        print("\n── 详细分类 ──")
        for e in classified:
            print(f"  [{e['signal_type']:15s}] {e.get('company', '?'):12s} {e['title'][:60]}")
    else:
        print(f"事件文件不存在: {events_path}")
