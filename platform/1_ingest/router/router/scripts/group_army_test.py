"""文字创作集团军 — 全集群测试 (12案例)"""
import sys, json, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, r'D:\92_products\TextClassifier\src')
from classifier import TextClassifier

# 6集群 × 2案例 = 12测试
test_cases = {
    "A_FlashNews": [
        ("A1_午间快讯", "写一条A股午间简讯，覆盖三大指数涨跌和热点板块，150字以内"),
        ("A2_突发新闻", "某芯片巨头宣布突破3nm制程，写一条300字快讯，含股价反应"),
    ],
    "B_DeepProd": [
        ("B1_行业分析", "写一篇中国半导体设备国产化进程深度分析，含市场份额和技术路线对比，面向投资人群，5000字"),
        ("B2_政策解读", "解读最新AI监管政策对科技行业的影响，要有正反方观点，面向决策者"),
    ],
    "C_CreativeX": [
        ("C1_营销文案", "写一条双十一促销活动营销文案，面向25-35岁女性，强调性价比和限时优惠"),
        ("C2_品牌故事", "为一个新能源车企写一篇品牌故事，强调环保使命和技术创新"),
    ],
    "D_TechDoc": [
        ("D1_API文档", "写一份Python REST API接口文档，含认证/端点/错误码/示例代码"),
        ("D2_用户手册", "写一份智能家居APP用户手册，含安装/配置/常见问题"),
    ],
    "E_SciPop": [
        ("E1_量子科普", "写一篇科普文章解释量子计算，面向高中生，用生活中的类比帮助理解"),
        ("E2_AI科普", "用通俗语言解释什么是大语言模型，面向非技术人群，2000字"),
    ],
    "F_OpEd": [
        ("F1_科技评论", "写一篇关于AI替代人类工作的评论文章，要有深度思考和批判性，不要泛泛而谈"),
        ("F2_投资观点", "写一篇对2026年下半年A股走势的观点文章，基于数据和逻辑论证"),
    ],
}

tc = TextClassifier()
results = []

print("=" * 60)
print("  文字创作集团军 — 全集群测试")
print("=" * 60)

for cluster_key, cases in test_cases.items():
    cluster_name = cluster_key.split("_")[1]
    print(f"\n{'─'*60}")
    print(f"  [{cluster_key}] {cluster_name}")
    
    for case_id, text in cases:
        start = time.time()
        result = tc.process(text)
        elapsed = (time.time() - start) * 1000
        
        cluster = str(getattr(result, 'cluster', '?'))
        conf = getattr(result, 'confidence', 0)
        rule = getattr(result, 'rule_matched', '')
        l2 = str(getattr(result, 'l2_config', {}))
        reasoning = getattr(result, 'reasoning', '')
        
        bar = '█' * int(conf * 10) + '░' * (10 - int(conf * 10))
        print(f"  [{case_id}] {cluster:<8} {bar} {conf:.0%} | {rule[:50]}...")
        
        results.append({
            "case_id": case_id,
            "cluster": cluster_key,
            "input": text,
            "classification": cluster,
            "confidence": conf,
            "rule": rule,
            "l2_config": l2,
            "reasoning": reasoning,
            "elapsed_ms": elapsed,
        })

# Save results
output_dir = Path(r'D:\92_products\TextClassifier\output')
output_dir.mkdir(exist_ok=True)
out_path = output_dir / f"group_army_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({"test_date": datetime.now().isoformat(), "total": len(results), "results": results}, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"  {len(results)} cases, {len(test_cases)} clusters tested")
print(f"  结果: {out_path}")
print(f"{'='*60}")
