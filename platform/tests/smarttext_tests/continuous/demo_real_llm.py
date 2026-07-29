"""
SmartTextPlatform — 真实 LLM 创作能力演示
=============================================
6 集群各选 1 个代表性场景，展示完整文字产出
"""
import sys, os, json, time
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))

os.environ["DEEPSEEK_API_KEY"] = "sk-6ab54a235bcc45f0821d7f9fb014a9b7"

from shared.cluster_engine import ClusterEngine

DEMO_CASES = [
    # ── A: 实时快反 ──
    {
        "cluster": "flashnews",
        "label": "A股收盘快评",
        "spec": {
            "structured_spec": {
                "core_intent": "今日A股收盘快评",
                "product_type": "新闻/快讯",
                "depth": "快讯级",
                "timeliness": "日内",
                "target_audience": "散户投资者",
                "style": "数据驱动",
                "domain_tags": ["金融", "证券"],
            },
            "configuration": {"cluster": "A"},
        },
    },
    # ── B: 深度生产 ──
    {
        "cluster": "deepprod",
        "label": "AI大模型竞争格局",
        "spec": {
            "structured_spec": {
                "core_intent": "2026年全球AI大模型竞争格局分析",
                "product_type": "分析/报告",
                "depth": "深度",
                "target_audience": "投资人群",
                "style": "数据驱动",
                "domain_tags": ["AI", "科技"],
            },
            "configuration": {"cluster": "B", "config_name": "industry_analysis"},
        },
    },
    # ── C: 创意转化 ──
    {
        "cluster": "creativex",
        "label": "双十一促销文案",
        "spec": {
            "structured_spec": {
                "core_intent": "双十一大促活动营销文案",
                "product_type": "营销文案",
                "target_audience": "C端用户",
                "style": "情感共鸣+转化导向",
                "domain_tags": ["消费", "电商"],
                "channel": "社交媒体",
            },
            "configuration": {"cluster": "C"},
        },
    },
    # ── D: 技术文档 ──
    {
        "cluster": "techdoc",
        "label": "REST API 接口文档",
        "spec": {
            "structured_spec": {
                "core_intent": "REST API 用户认证接口文档",
                "product_type": "技术文档",
                "target_audience": "技术人群",
                "style": "技术准确",
                "domain_tags": ["技术", "软件"],
                "constraints": ["含代码示例", "含错误码"],
            },
            "configuration": {"cluster": "D"},
        },
    },
    # ── E: 知识科普 ──
    {
        "cluster": "scipop",
        "label": "量子计算科普",
        "spec": {
            "structured_spec": {
                "core_intent": "用通俗语言解释量子计算基本原理",
                "product_type": "科普/教程",
                "target_audience": "普通大众",
                "style": "通俗易懂+类比丰富",
                "domain_tags": ["科技", "量子"],
            },
            "configuration": {"cluster": "E"},
        },
    },
    # ── F: 观点论证 ──
    {
        "cluster": "oped",
        "label": "AI全球监管观点",
        "spec": {
            "structured_spec": {
                "core_intent": "AI监管需要全球协作而非各自为政",
                "product_type": "评论/观点",
                "target_audience": "决策者+专业人士",
                "style": "论证导向",
                "domain_tags": ["AI", "政策"],
            },
            "configuration": {"cluster": "F"},
        },
    },
]

print("=" * 24)
print("  SmartTextPlatform — 真实 LLM 创作演示")
print("=" * 24)

all_outputs = []

for case in DEMO_CASES:
    cluster = case["cluster"]
    label = case["label"]
    
    delim = "─" * 60
    print(f"\n{delim}")
    print(f"\n## {cluster.upper()} | {label}\n")
    print(f"{delim}\n")
    
    t0 = time.time()
    engine = ClusterEngine(cluster)
    results = engine.run_full_pipeline(case["spec"])
    latency = (time.time() - t0)
    
    for stage_id, r in results.items():
        content = r.get("output", {}).get("content", "")
        tokens = r.get("output", {}).get("tokens", 0)
        gate = r.get("gate", "")
        status = "✅" if r.get("gate_passed") else "❌"
        
        print(f"### {stage_id} [{status}] — tokens: {tokens}\n")
        print(content)
        print()
    
    total_chars = sum(len(r.get("output", {}).get("content", "")) for r in results.values())
    total_tokens = sum(r.get("output", {}).get("tokens", 0) for r in results.values())
    print(f"**总计**: {total_chars} 字 | {total_tokens} tokens | {latency:.1f}s\n")
    
    all_outputs.append({
        "cluster": cluster,
        "label": label,
        "chars": total_chars,
        "tokens": total_tokens,
        "latency_s": round(latency, 1),
    })

# Summary
print("\n" + "=" * 60)
print("  📊 总览")
print("=" * 60)
for o in all_outputs:
    print(f"  {o['cluster']:12s} {o['label']:16s} | {o['chars']:5d} chars | {o['tokens']:4d} tokens | {o['latency_s']:.1f}s")

total_chars = sum(o['chars'] for o in all_outputs)
total_tokens = sum(o['tokens'] for o in all_outputs)
total_time = sum(o['latency_s'] for o in all_outputs)
print(f"\n  合计: {total_chars} chars | {total_tokens} tokens | {total_time:.1f}s")
print("=" * 60)
