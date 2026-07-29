#!/usr/bin/env python3
"""
SR-KB-001: AI 知识底座 — 实体提取脚本
────────────────────────────────────
从频道 Markdown 产出中提取实体卡片和关系数据

Phase 1: 基于规则和种子数据的实体提取
Phase 3: NER + 关系抽取（ML pipeline）

用法: python extract_entities.py [--full]
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ─── 配置 ──────────────────────────────────────────

PROJECT_ROOT = Path(r"D:\92_products\SmartTextPlatform")
KB_ROOT = PROJECT_ROOT / "knowledge_base"
CHANNELS_DIR = PROJECT_ROOT / "channels"

# 种子实体定义（MKT 内阁确认的 10 家公司）
SEED_ENTITIES = {
    "openai": {
        "entity_id": "openai",
        "name": "OpenAI",
        "type": "company",
        "domains": ["大模型", "基础研究", "API平台"],
        "key_products": ["GPT-5", "Sora", "ChatGPT", "Codex"],
        "competitors": ["Google DeepMind", "Anthropic", "Meta AI"],
        "suppliers": ["Microsoft Azure"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "google": {
        "entity_id": "google",
        "name": "Google DeepMind",
        "type": "company",
        "domains": ["大模型", "搜索", "云计算"],
        "key_products": ["Gemini", "Gemma", "Vertex AI"],
        "competitors": ["OpenAI", "Microsoft", "Anthropic"],
        "suppliers": ["自研TPU"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "microsoft": {
        "entity_id": "microsoft",
        "name": "Microsoft",
        "type": "company",
        "domains": ["云计算", "AI平台", "办公"],
        "key_products": ["Azure AI", "Copilot", "Phi-4"],
        "competitors": ["Google Cloud", "AWS", "OpenAI"],
        "suppliers": ["NVIDIA", "OpenAI"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "anthropic": {
        "entity_id": "anthropic",
        "name": "Anthropic",
        "type": "company",
        "domains": ["大模型", "AI安全"],
        "key_products": ["Claude 5", "Constitutional AI"],
        "competitors": ["OpenAI", "Google DeepMind"],
        "suppliers": ["AWS", "Google Cloud"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "nvidia": {
        "entity_id": "nvidia",
        "name": "NVIDIA / 英伟达",
        "type": "company",
        "domains": ["AI芯片", "GPU", "AI计算"],
        "key_products": ["H200", "B200", "CUDA", "DGX"],
        "competitors": ["AMD", "Intel", "华为昇腾"],
        "suppliers": ["TSMC", "SK海力士", "三星"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "bytedance": {
        "entity_id": "bytedance",
        "name": "字节跳动",
        "type": "company",
        "domains": ["大模型", "应用", "推荐"],
        "key_products": ["豆包", "火山引擎", "Coze"],
        "competitors": ["百度", "阿里巴巴", "腾讯"],
        "suppliers": ["NVIDIA", "华为"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "baidu": {
        "entity_id": "baidu",
        "name": "百度",
        "type": "company",
        "domains": ["大模型", "自动驾驶", "搜索"],
        "key_products": ["文心一言", "Apollo", "百度智能云"],
        "competitors": ["字节跳动", "阿里巴巴", "OpenAI"],
        "suppliers": ["NVIDIA", "华为昇腾"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "alibaba": {
        "entity_id": "alibaba",
        "name": "阿里巴巴",
        "type": "company",
        "domains": ["云计算", "大模型", "开源"],
        "key_products": ["通义千问", "阿里云", "ModelScope"],
        "competitors": ["腾讯", "百度", "AWS"],
        "suppliers": ["NVIDIA", "Intel"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "tencent": {
        "entity_id": "tencent",
        "name": "腾讯",
        "type": "company",
        "domains": ["大模型", "社交", "游戏"],
        "key_products": ["混元大模型", "腾讯云", "微信AI"],
        "competitors": ["字节跳动", "阿里巴巴", "百度"],
        "suppliers": ["NVIDIA"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
    "perplexity": {
        "entity_id": "perplexity",
        "name": "Perplexity",
        "type": "company",
        "domains": ["AI搜索", "Agent"],
        "key_products": ["Perplexity Pro", "Perplexity API"],
        "competitors": ["Google", "OpenAI", "You.com"],
        "suppliers": ["Google Cloud"],
        "timeline": [],
        "last_updated": "2026-06-17",
    },
}

# 实体别名映射（用于在文本中识别）
ENTITY_ALIASES = {
    "openai": ["OpenAI", "openai", "GPT", "ChatGPT", "Sam Altman"],
    "google": ["Google", "DeepMind", "Gemini", "Google DeepMind"],
    "microsoft": ["Microsoft", "微软", "Azure", "Copilot"],
    "anthropic": ["Anthropic", "Claude", "anthropic"],
    "nvidia": ["NVIDIA", "英伟达", "nvidia", "H100", "B200", "CUDA"],
    "bytedance": ["字节跳动", "ByteDance", "bytedance", "豆包", "火山引擎"],
    "baidu": ["百度", "Baidu", "baidu", "文心", "Apollo"],
    "alibaba": ["阿里巴巴", "Alibaba", "阿里", "通义"],
    "tencent": ["腾讯", "Tencent", "tencent", "混元"],
    "perplexity": ["Perplexity", "perplexity"],
}

# 附加实体（产品/技术/人物，从频道文本中识别）
EXTRA_ENTITY_PATTERNS = {
    "tsmc": {"aliases": ["TSMC", "台积电", "tsmc"], "type": "company", "domains": ["芯片代工"]},
    "meta": {"aliases": ["Meta", "Facebook", "Llama", "meta"], "type": "company", "domains": ["大模型", "开源"]},
    "amd": {"aliases": ["AMD", "amd"], "type": "company", "domains": ["芯片", "GPU"]},
    "huawei": {"aliases": ["华为", "Huawei", "昇腾", "鸿蒙"], "type": "company", "domains": ["芯片", "操作系统"]},
    "sk_hynix": {"aliases": ["SK海力士", "SK hynix", "Hynix"], "type": "company", "domains": ["存储芯片", "HBM"]},
    "samsung": {"aliases": ["三星", "Samsung"], "type": "company", "domains": ["存储芯片", "代工"]},
    "asml": {"aliases": ["ASML", "asml"], "type": "company", "domains": ["光刻机"]},
    "intel": {"aliases": ["Intel", "intel", "英特尔"], "type": "company", "domains": ["芯片", "代工"]},
}


# ─── 实体提取逻辑 ──────────────────────────────

def extract_entity_mentions(text: str) -> dict:
    """从文本中提取实体提及"""
    mentions = defaultdict(int)

    for entity_id, aliases in ENTITY_ALIASES.items():
        for alias in aliases:
            # case-insensitive match
            count = len(re.findall(re.escape(alias), text, re.IGNORECASE))
            if count > 0:
                mentions[entity_id] += count

    for entity_id, info in EXTRA_ENTITY_PATTERNS.items():
        for alias in info["aliases"]:
            count = len(re.findall(re.escape(alias), text, re.IGNORECASE))
            if count > 0:
                mentions[entity_id] += count

    return dict(mentions)


def scan_channel_files(days: int = 7) -> list:
    """扫描最近 N 天的频道产出"""
    files = []
    cutoff = datetime.now() - timedelta(days=days)

    for ch_dir in CHANNELS_DIR.iterdir():
        if not ch_dir.is_dir():
            continue
        for md_file in ch_dir.glob("*.md"):
            try:
                date_str = md_file.stem  # YYYY-MM-DD
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date >= cutoff:
                    files.append({
                        "path": str(md_file),
                        "channel": ch_dir.name,
                        "date": date_str,
                    })
            except ValueError:
                continue

    return sorted(files, key=lambda f: f["date"])


def update_entity_timelines(channel_files: list) -> dict:
    """从频道文件中更新实体时间线"""
    entities = json.loads(json.dumps(SEED_ENTITIES))  # deep copy

    for cf in channel_files:
        try:
            with open(cf["path"], 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            continue

        mentions = extract_entity_mentions(content)
        if not mentions:
            continue

        # 为每个被提及的实体添加时间线条目
        for entity_id, count in mentions.items():
            if entity_id not in entities:
                # 检查 EXTRA_ENTITY_PATTERNS
                if entity_id in EXTRA_ENTITY_PATTERNS:
                    info = EXTRA_ENTITY_PATTERNS[entity_id]
                    entities[entity_id] = {
                        "entity_id": entity_id,
                        "name": info["aliases"][0],
                        "type": info["type"],
                        "domains": info["domains"],
                        "key_products": [],
                        "competitors": [],
                        "suppliers": [],
                        "timeline": [],
                        "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    }
                else:
                    continue

            # 提取该实体在文件中的关键句子
            key_sentences = []
            for line in content.split('\n'):
                if entity_id in ENTITY_ALIASES:
                    for alias in ENTITY_ALIASES[entity_id]:
                        if alias.lower() in line.lower() and len(line) > 20:
                            key_sentences.append(line.strip()[:120])
                            break
                elif entity_id in EXTRA_ENTITY_PATTERNS:
                    for alias in EXTRA_ENTITY_PATTERNS[entity_id]["aliases"]:
                        if alias.lower() in line.lower() and len(line) > 20:
                            key_sentences.append(line.strip()[:120])
                            break

            entities[entity_id]["timeline"].append({
                "date": cf["date"],
                "event": key_sentences[0] if key_sentences else f"在 {cf['channel']} 频道中被提及 {count} 次",
                "source": f"channels/{cf['channel']}/{cf['date']}.md",
            })

    return entities


def build_relations(entities: dict) -> dict:
    """构建实体间关系"""
    relations = {
        "supply_chain": [],  # 供应链关系
        "compete": [],       # 竞争关系
        "invest": [],        # 投资关系
    }

    # 供应链关系（基于上游/下游）
    supply_pairs = [
        ("nvidia", "tsmc", "代工"),
        ("nvidia", "sk_hynix", "HBM供应"),
        ("nvidia", "samsung", "HBM供应"),
        ("amd", "tsmc", "代工"),
        ("intel", "tsmc", "代工"),
        ("huawei", "tsmc", "代工(历史)"),
        ("asml", "tsmc", "设备供应"),
        ("microsoft", "openai", "云服务"),
        ("anthropic", "google", "云服务"),
        ("baidu", "nvidia", "芯片采购"),
        ("alibaba", "nvidia", "芯片采购"),
        ("tencent", "nvidia", "芯片采购"),
        ("bytedance", "nvidia", "芯片采购"),
    ]

    for source, target, relation_type in supply_pairs:
        if source in entities:
            relations["supply_chain"].append({
                "source": source,
                "target": target,
                "relation": relation_type,
            })

    # 竞争关系
    compete_pairs = [
        ("openai", "anthropic", "模型竞争"),
        ("openai", "google", "模型竞争"),
        ("google", "microsoft", "云+AI竞争"),
        ("nvidia", "amd", "GPU竞争"),
        ("nvidia", "huawei", "AI芯片竞争"),
        ("bytedance", "baidu", "国内大模型竞争"),
        ("bytedance", "tencent", "应用层竞争"),
        ("alibaba", "tencent", "云+AI竞争"),
        ("alibaba", "baidu", "国内大模型竞争"),
        ("perplexity", "google", "AI搜索竞争"),
        ("perplexity", "openai", "搜索Agent竞争"),
        ("intel", "amd", "CPU/GPU竞争"),
    ]

    for source, target, relation_type in compete_pairs:
        if source in entities:
            relations["compete"].append({
                "source": source,
                "target": target,
                "relation": relation_type,
            })

    # 投资关系
    invest_pairs = [
        ("microsoft", "openai", "战略投资"),
    ]

    for source, target, relation_type in invest_pairs:
        if source in entities:
            relations["invest"].append({
                "source": source,
                "target": target,
                "relation": relation_type,
            })

    return relations


def build_global_index(entities: dict, relations: dict, channel_files: list) -> dict:
    """构建全局索引"""
    return {
        "build_time": datetime.now().isoformat(),
        "entity_count": len(entities),
        "relation_count": sum(len(v) for v in relations.values()),
        "channel_files_scanned": len(channel_files),
        "entities": list(entities.keys()),
        "relation_types": list(relations.keys()),
        "entity_summary": {
            eid: {
                "name": e.get("name", eid),
                "domains": e.get("domains", []),
                "timeline_events": len(e.get("timeline", [])),
            }
            for eid, e in entities.items()
        },
    }


# ─── 主流程 ────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SR-KB-001 知识底座实体提取")
    parser.add_argument("--full", action="store_true", help="全量扫描所有历史文件")
    parser.add_argument("--days", type=int, default=7, help="扫描最近 N 天（默认 7）")
    args = parser.parse_args()

    print("=" * 60)
    print("  SR-KB-001: AI 知识底座 · 实体提取")
    print("=" * 60)

    # 1. 扫描频道文件
    scan_days = 365 if args.full else args.days
    print(f"\n📂 扫描频道文件（最近 {scan_days} 天）...")
    channel_files = scan_channel_files(days=scan_days)
    print(f"   找到 {len(channel_files)} 个文件")

    if not channel_files:
        print("⚠️  未找到频道产出文件，仅生成种子数据。")

    # 2. 更新实体时间线
    print(f"\n🔍 提取实体提及...")
    entities = update_entity_timelines(channel_files)

    total_timeline = sum(len(e.get("timeline", [])) for e in entities.values())
    print(f"   提取 {len(entities)} 个实体，{total_timeline} 条时间线事件")

    # 3. 保存实体卡片
    print(f"\n💾 保存实体卡片...")
    entities_dir = KB_ROOT / "entities"
    os.makedirs(entities_dir, exist_ok=True)

    for entity_id, entity_data in entities.items():
        entity_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        filepath = entities_dir / f"{entity_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(entity_data, f, ensure_ascii=False, indent=2)

    print(f"   已保存 {len(entities)} 个实体到 {entities_dir}")

    # 4. 构建关系
    print(f"\n🔗 构建实体关系...")
    relations = build_relations(entities)
    relations_dir = KB_ROOT / "relations"
    os.makedirs(relations_dir, exist_ok=True)

    for rel_type, rel_list in relations.items():
        filepath = relations_dir / f"{rel_type}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rel_list, f, ensure_ascii=False, indent=2)
        print(f"   {rel_type}: {len(rel_list)} 条关系")

    # 5. 构建全局索引
    print(f"\n📊 构建全局索引...")
    index = build_global_index(entities, relations, channel_files)
    index_path = KB_ROOT / "index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"   ✅ 已保存到 {index_path}")

    # 6. 导出假设追踪模板（如果不存在）
    assumptions_path = KB_ROOT / "assumptions" / "assumptions_log.json"
    if not assumptions_path.exists():
        os.makedirs(assumptions_path.parent, exist_ok=True)
        template = {
            "2026-06": {
                "assumptions": [],
                "notes": "月报生成后将自动填充核心假设"
            }
        }
        with open(assumptions_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"   📝 已创建假设追踪模板")

    print(f"\n{'=' * 60}")
    print(f"  ✅ 知识底座更新完成")
    print(f"  📦 实体: {len(entities)} | 关系: {sum(len(v) for v in relations.values())}")
    print(f"  📁 输出目录: {KB_ROOT}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
