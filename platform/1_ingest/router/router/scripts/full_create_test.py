"""文字创作集团军 — 全链路测试 (分类→集群→产出)"""
import sys, json, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, r'D:\92_products\TextClassifier\src')
from classifier import TextClassifier

# 加载各集群引擎
engines = {}
cluster_paths = {
    'A': r'D:\92_products\FlashNews',
    'B': r'D:\92_products\DeepProd',
    'C': r'D:\92_products\CreativeX',
    'D': r'D:\92_products\TechDoc',
    'E': r'D:\92_products\SciPop',
    'F': r'D:\92_products\OpEd',
}

for cid, cpath_str in cluster_paths.items():
    cpath = Path(cpath_str)
    engine_path = cpath / 'src' / 'engine.py'
    if engine_path.exists():
        sys.path.insert(0, str(cpath / 'src'))
        try:
            if cid == 'B':
                from engine import DeepProdEngine
                engines[cid] = DeepProdEngine()
            else:
                # Other clusters use standard engine
                from engine import ClusterEngine
                engines[cid] = ClusterEngine()
        except Exception as e:
            print(f"  ⚠️ {cid}: engine load failed - {e}")
        sys.path.pop(0)

# 12 test cases
tests = [
    ("A1", "写一条A股午间简讯，覆盖三大指数涨跌和热点板块，150字以内"),
    ("A2", "某芯片巨头宣布突破3nm制程，写一条300字快讯，含股价反应"),
    ("B1", "写一篇中国半导体设备国产化进程深度分析，含市场份额和技术路线对比，面向投资人群，5000字"),
    ("B2", "解读最新AI监管政策对科技行业的影响，要有正反方观点，面向决策者"),
    ("C1", "写一条双十一促销活动营销文案，面向25-35岁女性，强调性价比和限时优惠"),
    ("C2", "为一个新能源车企写一篇品牌故事，强调环保使命和技术创新"),
    ("D1", "写一份Python REST API接口文档，含认证/端点/错误码/示例代码"),
    ("D2", "写一份智能家居APP用户手册，含安装/配置/常见问题"),
    ("E1", "写一篇科普文章解释量子计算，面向高中生，用生活中的类比帮助理解"),
    ("E2", "用通俗语言解释什么是大语言模型，面向非技术人群，2000字"),
    ("F1", "写一篇关于AI替代人类工作的评论文章，要有深度思考和批判性，不要泛泛而谈"),
    ("F2", "写一篇对2026年下半年A股走势的观点文章，基于数据和逻辑论证"),
]

tc = TextClassifier()
output_dir = Path(r'D:\92_products\TextClassifier\output\samples')
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("  文字创作集团军 — 全链路创作测试")
print("=" * 60)

for case_id, text in tests:
    print(f"\n{'─'*60}")
    
    # Step 1: Classify
    result = tc.process(text)
    cluster = str(getattr(result, 'cluster', '?'))
    cluster_name = getattr(result, 'cluster_name', '?')
    conf = getattr(result, 'confidence', 0)
    
    # Map cluster to engine ID
    cluster_map = {
        'ClusterType.A_NEWS_FLASH': 'A',
        'ClusterType.B_DEEP_ANALYSIS': 'B',
        'ClusterType.C_KNOWLEDGE_POP': 'C',
        'ClusterType.D_TECH_DOC': 'D',
        'ClusterType.E_CREATIVE': 'E',
        'ClusterType.F_COMMERCIAL': 'F',
    }
    engine_id = cluster_map.get(cluster, 'B')  # default to B
    
    print(f"  [{case_id}] → {cluster} ({cluster_name}, {conf:.0%})")
    print(f"  输入: {text[:80]}...")
    
    # Step 2: Run cluster engine
    engine = engines.get(engine_id)
    if engine:
        try:
            start = time.time()
            output = engine.run_full_pipeline({
                'structured_spec': {
                    'core_intent': text[:50],
                    'product_type': str(getattr(result, 'structured', {})),
                }
            })
            elapsed = (time.time() - start) * 1000
            
            # Capture output
            output_text = json.dumps(output, ensure_ascii=False, indent=2) if isinstance(output, dict) else str(output)
            
            # Save individual file
            sample_file = output_dir / f"{case_id}_{engine_id}.json"
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "case_id": case_id,
                    "input": text,
                    "classification": {"cluster": cluster, "confidence": conf},
                    "engine": engine_id,
                    "output": output if isinstance(output, dict) else str(output)[:3000],
                    "elapsed_ms": elapsed,
                }, f, ensure_ascii=False, indent=2)
            
            # Print preview
            preview = str(output)[:200]
            print(f"  产出: {preview}...")
            print(f"  文件: {sample_file.name} ({elapsed:.0f}ms)")
            
        except Exception as e:
            print(f"  ⚠️ Engine error: {e}")
    else:
        print(f"  ⚠️ No engine for {engine_id}")

print(f"\n{'='*60}")
print(f"  Samples: {output_dir}")
print(f"{'='*60}")
