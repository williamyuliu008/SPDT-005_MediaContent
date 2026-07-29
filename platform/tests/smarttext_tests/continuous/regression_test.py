"""
SmartTextPlatform — 升级回归验证
===================================
每赛道 1 例，重点验证：Stage 间差异度（上次核心缺陷）
"""

import sys, os, json, time, difflib
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
os.environ["DEEPSEEK_API_KEY"] = "sk-6ab54a235bcc45f0821d7f9fb014a9b7"

from shared.cluster_engine import ClusterEngine

CASES = [
    ("flashnews", "A股收盘快评", {
        "structured_spec": {"core_intent":"今日A股收盘快评","product_type":"新闻/快讯","depth":"快讯级","timeliness":"日内","target_audience":"散户投资者","style":"数据驱动","domain_tags":["金融","证券"]},
        "configuration": {"cluster": "A"},
    }),
    ("deepprod", "AI大模型竞争格局", {
        "structured_spec": {"core_intent":"2026年全球AI大模型竞争格局分析","product_type":"分析/报告","depth":"深度","target_audience":"投资人群","style":"数据驱动","domain_tags":["AI","科技"]},
        "configuration": {"cluster": "B", "config_name": "industry_analysis"},
    }),
    ("creativex", "双十一促销文案", {
        "structured_spec": {"core_intent":"双十一大促活动营销文案","product_type":"营销文案","target_audience":"C端用户","style":"情感共鸣+转化导向","domain_tags":["消费","电商"],"channel":"社交媒体"},
        "configuration": {"cluster": "C"},
    }),
    ("techdoc", "REST API文档", {
        "structured_spec": {"core_intent":"REST API用户认证接口文档","product_type":"技术文档","target_audience":"技术人群","style":"技术准确","domain_tags":["技术","软件"],"constraints":["含代码示例","含错误码"]},
        "configuration": {"cluster": "D"},
    }),
    ("scipop", "量子计算科普", {
        "structured_spec": {"core_intent":"用通俗语言解释量子计算基本原理","product_type":"科普/教程","target_audience":"普通大众","style":"通俗易懂+类比丰富","domain_tags":["科技","量子"]},
        "configuration": {"cluster": "E"},
    }),
    ("oped", "AI全球监管观点", {
        "structured_spec": {"core_intent":"AI监管需要全球协作而非各自为政","product_type":"评论/观点","target_audience":"决策者+专业人士","style":"论证导向","domain_tags":["AI","政策"]},
        "configuration": {"cluster": "F"},
    }),
]

def similarity(a, b):
    """0 = 完全不同, 1 = 完全相同"""
    if not a or not b:
        return 0
    return difflib.SequenceMatcher(None, a, b).ratio()

print("=" * 64)
print("  SmartTextPlatform — 升级回归验证")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 64)

results = []

for cluster_id, label, spec in CASES:
    print(f"\n{'─'*60}")
    print(f"  [{cluster_id.upper()}] {label}")
    print(f"{'─'*60}")

    t0 = time.time()
    engine = ClusterEngine(cluster_id)
    pipeline = engine.run_full_pipeline(spec)
    latency = time.time() - t0

    # 提取各 stage 内容
    stages = {}
    stage_order = []
    for sid, r in pipeline.items():
        content = r.get("output", {}).get("content", "")
        tokens = r.get("output", {}).get("tokens", 0)
        stages[sid] = content
        stage_order.append(sid)

    # 计算相邻 stage 相似度（核心指标）
    sims = []
    for i in range(len(stage_order) - 1):
        s1, s2 = stage_order[i], stage_order[i+1]
        sim = similarity(stages[s1], stages[s2])
        sims.append((s1, s2, sim))

    # 打印每阶段摘要 + 相似度
    for sid in stage_order:
        content = stages[sid]
        tokens = pipeline[sid].get("output", {}).get("tokens", 0)
        preview = content[:120].replace('\n', ' ')
        print(f"  {sid:16s} | {tokens:5d} tk | {preview}...")

    # 相似度报告
    print(f"\n  📊 Stage 相邻相似度:")
    statuses = []
    for s1, s2, sim in sims:
        bar = "▓" * int(sim * 10) + "░" * (10 - int(sim * 10))
        if sim < 0.3:
            status = "✅ 差异大"
        elif sim < 0.6:
            status = "🟡 中等"
        else:
            status = "❌ 重复"
        statuses.append(status)
        print(f"    {s1} → {s2}: [{bar}] {sim:.2f}  {status}")

    avg_sim = sum(s for _, _, s in sims) / len(sims) if sims else 0
    ok = avg_sim < 0.5  # 平均相似度 < 50% = 通过
    status = "✅ 通过" if ok else "❌ 未通过"
    print(f"    平均: {avg_sim:.2f} → {status}")

    results.append({
        "cluster": cluster_id,
        "label": label,
        "stages": len(stage_order),
        "avg_similarity": round(avg_sim, 3),
        "similarities": [round(s, 3) for _, _, s in sims],
        "passed": ok,
        "latency_s": round(latency, 1),
        "total_tokens": sum(pipeline[s].get("output", {}).get("tokens", 0) for s in stage_order),
    })

# 总览
print(f"\n{'='*64}")
print(f"  📊 验收结果总览")
print(f"{'='*64}")
print(f"  {'赛道':12s} {'Stage':>5s} {'相邻相似度':>10s} {'耗时':>8s} {'Tokens':>7s} {'判定'}")
print(f"  {'─'*55}")

all_pass = True
for r in results:
    sim_str = f"{r['avg_similarity']:.2f}"
    flag = "✅" if r['passed'] else "❌"
    if not r['passed']:
        all_pass = False
    print(f"  {r['cluster']:12s} {r['stages']:>5d} {sim_str:>10s} {r['latency_s']:>6.1f}s {r['total_tokens']:>7d} {flag}")

print(f"\n  判定: {'🎉 全部通过' if all_pass else '⚠️ 存在未通过项'}")
print(f"{'='*64}")

# 保存结果
out = BASE / "tests" / "continuous" / "results" / f"regression_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump({"timestamp": datetime.now().isoformat(), "results": results, "all_pass": all_pass}, f, ensure_ascii=False, indent=2)
print(f"\n  结果: {out}")
