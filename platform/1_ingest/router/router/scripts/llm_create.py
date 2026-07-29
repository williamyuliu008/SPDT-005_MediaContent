"""文字创作集团军 — LLM全链路创作 (12案例→实际产出)"""
import sys, json, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, r'D:\92_products\TextClassifier\src')
from classifier import TextClassifier
from llm_gateway import generate_for_cluster

tc = TextClassifier()

tests = [
    ("A1", "写一条A股午间简讯，覆盖三大指数涨跌和热点板块，150字以内"),
    ("A2", "某芯片巨头宣布突破3nm制程，写一条300字快讯，含股价反应"),
    ("B1", "写一篇中国半导体设备国产化进程深度分析，含市场份额和技术路线对比"),
    ("B2", "解读最新AI监管政策对科技行业的影响，要有正反方观点"),
    ("C1", "写一条双十一促销活动营销文案，面向25-35岁女性，强调性价比和限时优惠"),
    ("C2", "为一个新能源车企写一篇品牌故事，强调环保使命和技术创新"),
    ("D1", "写一份Python REST API接口文档，含认证/端点/错误码/示例代码"),
    ("D2", "写一份智能家居APP用户手册，含安装/配置/常见问题"),
    ("E1", "写一篇科普文章解释量子计算，面向高中生，用生活中的类比帮助理解"),
    ("E2", "用通俗语言解释什么是大语言模型，面向非技术人群"),
    ("F1", "写一篇关于AI替代人类工作的评论文章，要有深度思考和批判性"),
    ("F2", "写一篇对2026年下半年A股走势的观点文章，基于数据和逻辑论证"),
]

# Cluster mapping from classifier
cluster_map = {
    'ClusterType.A_NEWS_FLASH': 'A',
    'ClusterType.B_DEEP_ANALYSIS': 'B',
    'ClusterType.C_KNOWLEDGE_POP': 'C',
    'ClusterType.D_TECH_DOC': 'D',
    'ClusterType.E_CREATIVE': 'E',
    'ClusterType.F_COMMERCIAL': 'F',
}

output_dir = Path(r'D:\92_products\TextClassifier\output\llm_samples')
output_dir.mkdir(parents=True, exist_ok=True)
results = []

print("=" * 60)
print("  文字创作集团军 — LLM 全链路创作")
print("=" * 60)

for case_id, text in tests:
    print(f"\n{'─'*60}")
    
    # Step 1: Classify
    result = tc.process(text)
    cluster = str(getattr(result, 'cluster', '?'))
    cluster_name = getattr(result, 'cluster_name', '?')
    conf = getattr(result, 'confidence', 0)
    l2 = getattr(result, 'l2_config', {})
    reasoning = getattr(result, 'reasoning', '')
    
    cid = cluster_map.get(cluster, 'B')
    
    print(f"  [{case_id}] → [{cid}] {cluster_name} ({conf:.0%})")
    print(f"  输入: {text[:60]}...")
    
    # Step 2: LLM generate
    try:
        start = time.time()
        content = generate_for_cluster(cid, text)
        elapsed = time.time() - start
        
        # Save
        out = {
            "case_id": case_id,
            "cluster": cid,
            "input": text,
            "classification": {"cluster": cluster, "confidence": conf, "reasoning": str(reasoning)},
            "l2_config": str(l2),
            "output": content,
            "output_length": len(content),
            "elapsed_sec": round(elapsed, 1),
        }
        
        with open(output_dir / f"{case_id}.json", 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        
        # Preview
        preview = content[:150].replace('\n', ' ')
        print(f"  产出({len(content)}字, {elapsed:.1f}s): {preview}...")
        results.append(out)
        
    except Exception as e:
        print(f"  ❌ {e}")

print(f"\n{'='*60}")
print(f"  完成: {len(results)}/{len(tests)} cases")
print(f"  结果: {output_dir}")
print(f"{'='*60}")
