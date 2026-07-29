"""
Quick demo: 3 representative clusters → file output
"""
import sys, os, json, time
from pathlib import Path

BASE = Path(r"D:\92_products\SmartTextPlatform")
sys.path.insert(0, str(BASE))
os.environ["DEEPSEEK_API_KEY"] = "sk-6ab54a235bcc45f0821d7f9fb014a9b7"

from shared.cluster_engine import ClusterEngine

OUT = BASE / "tests" / "continuous" / "results" / "demo_output.md"

with open(OUT, 'w', encoding='utf-8') as f:
    f.write("# SmartTextPlatform — 真实 LLM 文字创作演示\n\n")
    f.write(f"*生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
    f.write("---\n\n")

    # ── Case 1: 快讯 ──
    f.write("## 📰 CLUSTER-A 实时快反 | A股收盘快评\n\n")
    engine = ClusterEngine('flashnews')
    t0 = time.time()
    r = engine.run_full_pipeline({
        'structured_spec': {
            'core_intent': '今日A股收盘快评',
            'product_type': '新闻/快讯', 'depth': '快讯级',
            'timeliness': '日内', 'target_audience': '散户投资者',
            'style': '数据驱动', 'domain_tags': ['金融','证券'],
        },
        'configuration': {'cluster': 'A'},
    })
    for sid, rr in r.items():
        c = rr.get('output', {}).get('content', '')
        tk = rr.get('output', {}).get('tokens', 0)
        f.write(f"### {sid} (tokens: {tk})\n\n{c}\n\n")
    f.write(f"*⏱ {time.time()-t0:.1f}s*\n\n---\n\n")

    # ── Case 2: 科普 ──
    f.write("## 🔬 CLUSTER-E 知识科普 | 量子计算入门\n\n")
    engine = ClusterEngine('scipop')
    t0 = time.time()
    r = engine.run_full_pipeline({
        'structured_spec': {
            'core_intent': '用通俗语言解释量子计算基本原理',
            'product_type': '科普/教程', 'target_audience': '普通大众',
            'style': '通俗易懂+类比丰富', 'domain_tags': ['科技','量子'],
        },
        'configuration': {'cluster': 'E'},
    })
    for sid, rr in r.items():
        c = rr.get('output', {}).get('content', '')
        tk = rr.get('output', {}).get('tokens', 0)
        f.write(f"### {sid} (tokens: {tk})\n\n{c}\n\n")
    f.write(f"*⏱ {time.time()-t0:.1f}s*\n\n---\n\n")

    # ── Case 3: 观点 ──
    f.write("## 🎯 CLUSTER-F 观点论证 | AI全球监管\n\n")
    engine = ClusterEngine('oped')
    t0 = time.time()
    r = engine.run_full_pipeline({
        'structured_spec': {
            'core_intent': 'AI监管需要全球协作而非各自为政',
            'product_type': '评论/观点', 'target_audience': '决策者+专业人士',
            'style': '论证导向', 'domain_tags': ['AI','政策'],
        },
        'configuration': {'cluster': 'F'},
    })
    for sid, rr in r.items():
        c = rr.get('output', {}).get('content', '')
        tk = rr.get('output', {}).get('tokens', 0)
        f.write(f"### {sid} (tokens: {tk})\n\n{c}\n\n")
    f.write(f"*⏱ {time.time()-t0:.1f}s*\n\n---\n\n")

    f.write("\n\n*🎉 演示完成。更多集群测试请运行 `python tests/continuous/run_all.py`*\n")

print("DONE →", OUT)
