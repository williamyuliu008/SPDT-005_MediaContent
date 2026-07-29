#!/usr/bin/env python3
"""批量写入 10 家公司知识底座种子实体卡片"""
import json, os

entities = {
    "openai": {
        "entity_id": "openai", "name": "OpenAI", "type": "company",
        "domains": ["大模型", "基础研究", "API平台"],
        "key_products": ["GPT-5", "Sora", "ChatGPT", "Codex", "DALL-E"],
        "competitors": ["Google DeepMind", "Anthropic", "Meta AI"],
        "suppliers": ["Microsoft Azure"],
        "timeline": [], "last_updated": "2026-06-17"
    },
    "google": {
        "entity_id": "google", "name": "Google DeepMind", "type": "company",
        "domains": ["大模型", "搜索", "云计算"],
        "key_products": ["Gemini", "Gemma", "Vertex AI", "AlphaFold"],
        "competitors": ["OpenAI", "Microsoft", "Anthropic"],
        "suppliers": ["自研TPU"], "timeline": [], "last_updated": "2026-06-17"
    },
    "microsoft": {
        "entity_id": "microsoft", "name": "Microsoft", "type": "company",
        "domains": ["云计算", "AI平台", "办公"],
        "key_products": ["Azure AI", "Copilot", "Phi-4"],
        "competitors": ["Google Cloud", "AWS"],
        "suppliers": ["NVIDIA", "OpenAI"], "timeline": [], "last_updated": "2026-06-17"
    },
    "anthropic": {
        "entity_id": "anthropic", "name": "Anthropic", "type": "company",
        "domains": ["大模型", "AI安全"],
        "key_products": ["Claude 5", "Constitutional AI"],
        "competitors": ["OpenAI", "Google DeepMind"],
        "suppliers": ["AWS", "Google Cloud"], "timeline": [], "last_updated": "2026-06-17"
    },
    "nvidia": {
        "entity_id": "nvidia", "name": "NVIDIA / 英伟达", "type": "company",
        "domains": ["AI芯片", "GPU", "AI计算"],
        "key_products": ["H200", "B200", "CUDA", "DGX"],
        "competitors": ["AMD", "Intel", "华为昇腾"],
        "suppliers": ["TSMC", "SK海力士", "三星"], "timeline": [], "last_updated": "2026-06-17"
    },
    "bytedance": {
        "entity_id": "bytedance", "name": "字节跳动", "type": "company",
        "domains": ["大模型", "应用", "推荐"],
        "key_products": ["豆包", "火山引擎", "Coze"],
        "competitors": ["百度", "阿里巴巴", "腾讯"],
        "suppliers": ["NVIDIA", "华为"], "timeline": [], "last_updated": "2026-06-17"
    },
    "baidu": {
        "entity_id": "baidu", "name": "百度", "type": "company",
        "domains": ["大模型", "自动驾驶", "搜索"],
        "key_products": ["文心一言", "Apollo", "百度智能云"],
        "competitors": ["字节跳动", "阿里巴巴"],
        "suppliers": ["NVIDIA", "华为昇腾"], "timeline": [], "last_updated": "2026-06-17"
    },
    "alibaba": {
        "entity_id": "alibaba", "name": "阿里巴巴", "type": "company",
        "domains": ["云计算", "大模型", "开源"],
        "key_products": ["通义千问", "阿里云", "ModelScope"],
        "competitors": ["腾讯", "百度", "AWS"],
        "suppliers": ["NVIDIA", "Intel"], "timeline": [], "last_updated": "2026-06-17"
    },
    "tencent": {
        "entity_id": "tencent", "name": "腾讯", "type": "company",
        "domains": ["大模型", "社交", "游戏"],
        "key_products": ["混元大模型", "腾讯云", "微信AI"],
        "competitors": ["字节跳动", "阿里巴巴", "百度"],
        "suppliers": ["NVIDIA"], "timeline": [], "last_updated": "2026-06-17"
    },
    "perplexity": {
        "entity_id": "perplexity", "name": "Perplexity", "type": "company",
        "domains": ["AI搜索", "Agent"],
        "key_products": ["Perplexity Pro", "Perplexity API"],
        "competitors": ["Google", "OpenAI", "You.com"],
        "suppliers": ["Google Cloud"], "timeline": [], "last_updated": "2026-06-17"
    }
}

out_dir = r"D:\92_products\SmartTextPlatform\knowledge_base\entities"
os.makedirs(out_dir, exist_ok=True)
for eid, data in entities.items():
    with open(os.path.join(out_dir, f"{eid}.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {eid}.json")

print(f"\n共写入 {len(entities)} 个种子实体")
