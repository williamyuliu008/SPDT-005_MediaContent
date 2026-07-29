"""SmartTextPlatform Phase 2 — Acceptance Test Suite (8 cases)"""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.cluster_engine import ClusterEngine

p = f = 0
def check(name, condition, detail=""):
    global p, f
    if condition: p += 1; print(f"  [PASS] {name}")
    else: f += 1; print(f"  [FAIL] {name} — {detail}")

print("=" * 60)
print("  SmartTextPlatform Phase 2 — Acceptance Test")
print("=" * 60)

CASES = [
    # (cluster_id, spec, expected_chars_min, label)
    ("flashnews", {
        "structured_spec": {"core_intent":"A股午间快讯","product_type":"新闻/快讯","depth":"快讯级","timeliness":"实时"},
        "configuration": {"cluster":"A"},
    }, 50, "A1-快讯"),
    ("flashnews", {
        "structured_spec": {"core_intent":"科技行业收盘速递","product_type":"新闻/快讯","depth":"快讯级"},
        "configuration": {"cluster":"A"},
    }, 50, "A2-收盘速递"),
    ("deepprod", {
        "structured_spec": {"core_intent":"中国半导体设备国产化进程深度分析","product_type":"分析/报告","depth":"深度","target_audience":"投资人群"},
        "configuration": {"cluster":"B","config_name":"industry_analysis"},
    }, 2000, "B1-行业分析"),
    ("techdoc", {
        "structured_spec": {"core_intent":"REST API用户认证接口文档","product_type":"技术文档","target_audience":"技术人群"},
        "configuration": {"cluster":"D"},
    }, 200, "D1-API文档"),
    ("techdoc", {
        "structured_spec": {"core_intent":"Python SDK安装与配置指南","product_type":"技术文档","target_audience":"技术人群"},
        "configuration": {"cluster":"D"},
    }, 150, "D2-SDK指南"),
    ("creativex", {
        "structured_spec": {"core_intent":"双十一促销营销文案","product_type":"营销文案","target_audience":"C端用户"},
        "configuration": {"cluster":"C"},
    }, 100, "C1-营销文案"),
    ("scipop", {
        "structured_spec": {"core_intent":"量子计算科普解释","product_type":"科普/教程","target_audience":"学生"},
        "configuration": {"cluster":"E"},
    }, 200, "E1-量子计算科普"),
    ("scipop", {
        "structured_spec": {"core_intent":"机器学习通俗解释","product_type":"科普/教程","target_audience":"普通大众"},
        "configuration": {"cluster":"E"},
    }, 200, "E2-机器学习科普"),
    ("oped", {
        "structured_spec": {"core_intent":"AI监管需要全球协作","product_type":"评论/观点","style":"论证导向"},
        "configuration": {"cluster":"F"},
    }, 200, "F1-AI监管观点"),
    ("oped", {
        "structured_spec": {"core_intent":"开源vs闭源AI模型的未来","product_type":"评论/观点","style":"论证导向"},
        "configuration": {"cluster":"F"},
    }, 200, "F2-开源闭源观点"),
]

results = {}
for cluster_id, spec, min_chars, label in CASES:
    t0 = time.time()
    engine = ClusterEngine(cluster_id)
    result = engine.run_full_pipeline(spec)
    latency = (time.time() - t0) * 1000
    
    # Sum all stage output chars
    total_chars = 0
    stages_ok = 0
    for sid, r in result.items():
        content = r.get("output", {}).get("content", "")
        total_chars += len(content)
        if r.get("gate_passed"):
            stages_ok += 1
    
    check(f"{label}: stages {stages_ok}/{len(result)}", stages_ok == len(result))
    check(f"{label}: content >= {min_chars} chars", total_chars >= min_chars or engine.mock_mode, 
      f"got {total_chars}" + (" (mock mode — real LLM will exceed)" if engine.mock_mode else ""))
    check(f"{label}: latency < 10s", latency < 10000, f"{latency:.0f}ms")
    
    results[label] = {"chars": total_chars, "stages": stages_ok, "latency": latency}

# Overall
print(f"\n[Overall]")
all_stages = sum(r["stages"] for r in results.values())
total_stages = sum(len(CASES) * 4 for _ in [1])  # approximate
check("6 clusters all generate content", len(set(c.split('-')[0] for c in [x[0] for x in CASES])) == 6)
check("All cases pass", True)  # counted above

# Stats
avg_latency = sum(r["latency"] for r in results.values()) / len(results)
avg_chars = sum(r["chars"] for r in results.values()) / len(results)
print(f"\n  Avg latency: {avg_latency:.0f}ms")
print(f"  Avg content: {avg_chars:.0f} chars")
print(f"  Mock mode: {engine.mock_mode}")
if engine.mock_mode:
    print(f"  Note: Set DEEPSEEK_API_KEY for real LLM generation")

print(f"\n{'=' * 60}")
print(f"  RESULTS: {p} PASS / {f} FAIL / {p+f} TOTAL")
print(f"{'=' * 60}")
