# -*- coding: utf-8 -*-
"""
run_classify_and_pipeline.py — P0 演示：NL分类 → ContentSpec → 管线执行
============================================================================
完整流程：SmartTextClassifier(classify) → ContentSpec → PipelineRouter(run)

使用方式：
  无 DEEPSEEK_API_KEY：mock 模式（规则匹配，无 LLM 调用）
  有 DEEPSEEK_API_KEY：LLM 模式（真实分类）
"""
import os
import sys
import io
import json
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).parent

# ── 加载分类器 ───────────────────────────────────────────────
print("[1] 加载 SmartTextClassifier...")
import importlib.util

_spec_name = "_spdt05_classifier"
spec = importlib.util.spec_from_file_location(
    _spec_name,
    str(REPO_ROOT / "platform/1_ingest/router/smarttext_classifier.py"),
)
classifier_mod = importlib.util.module_from_spec(spec)
sys.modules[_spec_name] = classifier_mod
spec.loader.exec_module(classifier_mod)

SmartTextClassifier = classifier_mod.SmartTextClassifier

mock = not bool(os.environ.get("DEEPSEEK_API_KEY"))
print(f"    模式: {'Mock (规则匹配)' if mock else 'LLM (真实分类)'}\n")

# ── 加载管线路由器 ───────────────────────────────────────────
print("[2] 加载 PipelineRouter...")
_r_name = "_spdt05_router"
_r_spec = importlib.util.spec_from_file_location(
    _r_name,
    str(REPO_ROOT / "platform/1_ingest/router/pipeline_router.py"),
)
_r_mod = importlib.util.module_from_spec(_r_spec)
_r_mod.__name__ = _r_name
sys.modules[_r_name] = _r_mod
_r_spec.loader.exec_module(_r_mod)

PipelineRouter = _r_mod.PipelineRouter

# ── 测试用例 ────────────────────────────────────────────────
TESTS = [
    ("DeepMind发布AlphaFold3，生物学革命", "science_research"),
    ("突发：某地发现不明原因肺炎病例", "breakdown_news"),
    ("AI监管是必要的刹车而非倒车", "oped_argument"),
    ("小米15 ultra评测：影像旗舰的极限在哪里", "product_review"),
    ("一位乡村教师的二十六年坚守", "creative"),
    ("2026年中国新能源汽车行业深度分析", "deep_industry_report"),
]

print(f"[3] 运行分类测试（{len(TESTS)} 条）\n")
results = []
for i, (nl_input, expected) in enumerate(TESTS, 1):
    print(f"[{i}] NL: {nl_input}")

    # Step 1: 分类
    t0 = time.time()
    spec_lite = SmartTextClassifier(mock=mock).classify(nl_input)
    classify_time = time.time() - t0

    match = "✅" if spec_lite.content_type == expected else f"❌ (期望 {expected})"
    print(f"    分类: {spec_lite.content_type} {match}")
    print(f"    标题: {spec_lite.title}")
    print(f"    渠道: {spec_lite.channels}")
    print(f"    置信度: {spec_lite.metadata.get('classification_confidence','?')}")
    print(f"    耗时: {classify_time:.2f}s")
    print()

    results.append({
        "nl_input": nl_input,
        "expected": expected,
        "got": spec_lite.content_type,
        "match": spec_lite.content_type == expected,
        "confidence": spec_lite.metadata.get("classification_confidence"),
        "classify_time": round(classify_time, 2),
    })

# ── 结果摘要 ────────────────────────────────────────────────
passed = sum(1 for r in results if r["match"])
print("─" * 50)
print(f"分类结果: {passed}/{len(results)} 匹配")
for r in results:
    status = "✅" if r["match"] else "❌"
    print(f"  {status} {r['nl_input'][:30]} → {r['got']} (置信度 {r['confidence']})")

# ── 可选：执行管线（只跑第一个 mock 示例） ──────────────────
print("\n[4] 执行管线演示（breakdown_news 示例）...")
if mock:
    print("    (mock 模式，跳过管线执行，仅演示流程)")
    print("    完整流程: SmartTextClassifier → PipelineRouter.run(spec)")
else:
    try:
        router = PipelineRouter()
        demo_spec = SmartTextClassifier(mock=False).classify(TESTS[0][0])
        print(f"    分类结果: {demo_spec.content_type}")
        print(f"    → PipelineRouter.run() 开始执行...")
        # router.run(demo_spec.to_router_spec())  # 取消注释启用完整管线
        print("    ✅ 管线接口就绪，可调用 router.run(spec)")
    except Exception as e:
        print(f"    ⚠️ 管线执行出错（预期，演示目的）: {e}")

print("\n[P0 SmartTextClassifier 演示完成]")
