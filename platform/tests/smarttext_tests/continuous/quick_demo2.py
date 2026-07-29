"""
Append deepprod + techdoc + creativex to demo output
"""
import sys, os, time
from pathlib import Path

BASE = Path(r"D:\92_products\SmartTextPlatform")
sys.path.insert(0, str(BASE))
os.environ["DEEPSEEK_API_KEY"] = "sk-6ab54a235bcc45f0821d7f9fb014a9b7"

from shared.cluster_engine import ClusterEngine

OUT = BASE / "tests" / "continuous" / "results" / "demo_output.md"

with open(OUT, 'a', encoding='utf-8') as f:
    # ── Case 4: 深度生产 ──
    f.write("## 📊 CLUSTER-B 深度生产 | AI大模型竞争格局\n\n")
    engine = ClusterEngine('deepprod')
    t0 = time.time()
    r = engine.run_full_pipeline({
        'structured_spec': {
            'core_intent': '2026年全球AI大模型竞争格局分析',
            'product_type': '分析/报告', 'depth': '深度',
            'target_audience': '投资人群', 'style': '数据驱动',
            'domain_tags': ['AI','科技'],
        },
        'configuration': {'cluster': 'B', 'config_name': 'industry_analysis'},
    })
    for sid, rr in r.items():
        c = rr.get('output', {}).get('content', '')
        tk = rr.get('output', {}).get('tokens', 0)
        f.write(f"### {sid} (tokens: {tk})\n\n{c}\n\n")
    f.write(f"*⏱ {time.time()-t0:.1f}s*\n\n---\n\n")

    # ── Case 5: 技术文档 ──
    f.write("## 💻 CLUSTER-D 技术文档 | REST API 认证接口\n\n")
    engine = ClusterEngine('techdoc')
    t0 = time.time()
    r = engine.run_full_pipeline({
        'structured_spec': {
            'core_intent': '微服务网关API认证与授权文档',
            'product_type': '技术文档', 'target_audience': '开发者',
            'style': '技术准确', 'domain_tags': ['技术','软件'],
            'constraints': ['含代码示例','含错误码'],
        },
        'configuration': {'cluster': 'D'},
    })
    for sid, rr in r.items():
        c = rr.get('output', {}).get('content', '')
        tk = rr.get('output', {}).get('tokens', 0)
        f.write(f"### {sid} (tokens: {tk})\n\n{c}\n\n")
    f.write(f"*⏱ {time.time()-t0:.1f}s*\n\n---\n\n")

    # ── Case 6: 创意文案 ──
    f.write("## ✨ CLUSTER-C 创意转化 | 双十一促销文案\n\n")
    engine = ClusterEngine('creativex')
    t0 = time.time()
    r = engine.run_full_pipeline({
        'structured_spec': {
            'core_intent': '双十一大促活动营销文案',
            'product_type': '营销文案', 'target_audience': 'C端用户',
            'style': '情感共鸣+转化导向', 'domain_tags': ['消费','电商'],
            'channel': '社交媒体',
        },
        'configuration': {'cluster': 'C'},
    })
    for sid, rr in r.items():
        c = rr.get('output', {}).get('content', '')
        tk = rr.get('output', {}).get('tokens', 0)
        f.write(f"### {sid} (tokens: {tk})\n\n{c}\n\n")
    f.write(f"*⏱ {time.time()-t0:.1f}s*\n\n---\n\n")

print("DONE →", OUT)
