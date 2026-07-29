"""
SmartTextPlatform — 持续测试主控程序
=====================================
三层测试：分类回归 → 集群能力 → 质量评估
自动生成测试报告并保存历史
"""

import sys, os, json, time, yaml
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tests"))

# ═══════════════════════════════════════

def run_classification_tests():
    """Layer 1: 路由器分类回归测试"""
    print("\n" + "=" * 60)
    print("  LAYER 1: 路由器分类回归测试")
    print("=" * 60)
    
    sys.path.insert(0, str(BASE / "router"))
    from classifier import TextClassifier
    from test_golden import GOLDEN, EDGE
    
    tc = TextClassifier()
    
    results = {"layer": 1, "name": "分类回归", "golden_tests": [], "edge_cases": []}
    
    # Golden tests
    correct = 0
    for i, (text, expected) in enumerate(GOLDEN):
        t0 = time.time()
        result = tc.process(text)
        latency = time.time() - t0
        ok = result.cluster.value == expected
        if ok:
            correct += 1
        results["golden_tests"].append({
            "id": i + 1,
            "input": text[:80],
            "expected": expected,
            "actual": result.cluster.value,
            "passed": ok,
            "confidence": result.confidence,
            "latency_ms": round(latency * 1000),
        })
    
    accuracy = correct / len(GOLDEN) * 100
    results["accuracy"] = round(accuracy, 1)
    results["golden_passed"] = correct
    results["golden_total"] = len(GOLDEN)
    
    print(f"  Golden: {correct}/{len(GOLDEN)} = {accuracy:.0f}%")
    
    # Edge cases
    for i, (text, case) in enumerate(EDGE):
        try:
            t0 = time.time()
            result = tc.process(text)
            latency = time.time() - t0
            results["edge_cases"].append({
                "id": i + 1,
                "case": case,
                "result": result.cluster.value,
                "crashed": False,
                "latency_ms": round(latency * 1000),
            })
        except Exception as e:
            results["edge_cases"].append({
                "id": i + 1,
                "case": case,
                "result": "CRASH",
                "crashed": True,
                "error": str(e)[:100],
            })
            print(f"  Edge {case}: ❌ CRASH")
            continue
        print(f"  Edge {case}: ✅ → {result.cluster.value}")
    
    return results


def run_cluster_benchmark():
    """Layer 2: 集群文字创作能力基准"""
    print("\n" + "=" * 60)
    print("  LAYER 2: 集群文字创作能力基准")
    print("=" * 60)
    
    from continuous.cluster_benchmark import run_benchmark
    results = run_benchmark(verbose=True)
    
    return {
        "layer": 2,
        "name": "集群能力基准",
        "total": results["total_cases"],
        "passed": results["passed"],
        "failed": results["failed"],
        "mock_mode": results["summary"]["mock_mode"],
        "per_cluster": results["summary"]["per_cluster"],
        "cases": results["cases"],
    }


def run_quality_evaluation(benchmark_results: dict):
    """Layer 3: 深度文字质量评估"""
    print("\n" + "=" * 60)
    print("  LAYER 3: 文字质量深度评估")
    print("=" * 60)
    
    from continuous.quality_evaluator import evaluate_batch
    
    # 收集所有生成的内容
    cases_with_content = []
    for case in benchmark_results.get("cases", []):
        if case.get("passed"):
            cases_with_content.append({
                "id": case["id"],
                "cluster": case["cluster"],
                "label": case["label"],
                "content": case.get("content_preview", ""),
                "spec": {},  # Will be enriched if needed
            })
    
    if not cases_with_content:
        print("  ⚠️ 无可用内容供评估")
        return {"layer": 3, "name": "质量评估", "evaluated": 0, "results": []}
    
    quality_results = evaluate_batch(cases_with_content, use_llm=False)
    
    total_overall = sum(r["scores"].get("overall", 0) for r in quality_results)
    avg_overall = total_overall / len(quality_results) if quality_results else 0
    
    print(f"  Evaluated: {len(quality_results)} cases")
    print(f"  Avg quality score: {avg_overall:.0f}/100")
    
    return {
        "layer": 3,
        "name": "质量评估",
        "evaluated": len(quality_results),
        "avg_overall_score": round(avg_overall),
        "results": quality_results,
    }


def generate_report(all_results: list) -> str:
    """生成可读报告"""
    report = []
    report.append("=" * 60)
    report.append("  SmartTextPlatform 持续测试报告")
    report.append(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)
    
    for layer_result in all_results:
        name = layer_result.get("name", "")
        
        if layer_result["layer"] == 1:
            acc = layer_result.get("accuracy", 0)
            status = "✅" if acc >= 95 else "⚠️" if acc >= 80 else "❌"
            report.append(f"\n  [L1] 分类回归: {status} {acc:.1f}% ({layer_result['golden_passed']}/{layer_result['golden_total']})")
            for t in layer_result.get("golden_tests", []):
                if not t["passed"]:
                    report.append(f"    ❌ #{t['id']}: expected {t['expected']}, got {t['actual']} — \"{t['input']}\"")
        
        elif layer_result["layer"] == 2:
            passed = layer_result.get("passed", 0)
            total = layer_result.get("total", 0)
            mock = layer_result.get("mock_mode", True)
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            mock_note = " [MOCK — 无真实LLM]" if mock else " [REAL LLM]"
            report.append(f"\n  [L2] 集群能力: {status} {passed}/{total}{mock_note}")
            for cluster, stats in sorted(layer_result.get("per_cluster", {}).items()):
                report.append(f"    {cluster}: {stats['pass_rate']} | avg {stats['avg_chars']} chars | {stats['avg_latency_ms']}ms")
            for c in layer_result.get("cases", []):
                if not c["passed"]:
                    report.append(f"    ❌ {c['id']} {c['label']}: {c.get('stages','?')} stages")
        
        elif layer_result["layer"] == 3:
            avg = layer_result.get("avg_overall_score", 0)
            n = layer_result.get("evaluated", 0)
            status = "✅" if avg >= 70 else "⚠️" if avg >= 50 else "❌"
            report.append(f"\n  [L3] 质量评估: {status} avg {avg}/100 ({n} cases)")
    
    report.append(f"\n{'='*60}")
    return "\n".join(report)


def main():
    print("=" * 60)
    print("  SmartTextPlatform — 持续测试")
    print(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_results = []
    
    # Layer 1: 分类回归
    try:
        l1 = run_classification_tests()
        all_results.append(l1)
    except Exception as e:
        print(f"  ❌ Layer 1 失败: {e}")
        all_results.append({"layer": 1, "name": "分类回归", "error": str(e)})
    
    # Layer 2: 集群能力
    try:
        l2 = run_cluster_benchmark()
        all_results.append(l2)
    except Exception as e:
        print(f"  ❌ Layer 2 失败: {e}")
        all_results.append({"layer": 2, "name": "集群能力基准", "error": str(e)})
    
    # Layer 3: 质量评估
    try:
        l2_data = l2 if (len(all_results) > 1 and l2 and isinstance(l2, dict)) else {}
        l3 = run_quality_evaluation(l2_data)
        all_results.append(l3)
    except Exception as e:
        print(f"  ❌ Layer 3 失败: {e}")
        all_results.append({"layer": 3, "name": "质量评估", "evaluated": 0, "avg_overall_score": 0, "error": str(e)})
    
    # 保存完整结果
    results_dir = BASE / "tests" / "continuous" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = results_dir / f"full_run_{timestamp}.json"
    
    combined = {
        "timestamp": datetime.now().isoformat(),
        "layers": all_results,
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    
    # 生成报告
    report = generate_report(all_results)
    print("\n" + report)
    
    # 保存报告
    report_file = results_dir / f"report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n  结果已保存: {result_file}")
    print(f"  报告已保存: {report_file}")
    
    # 汇总判定
    l1 = all_results[0] if len(all_results) > 0 else {}
    l2 = all_results[1] if len(all_results) > 1 else {}
    l3 = all_results[2] if len(all_results) > 2 else {}
    l1_ok = l1.get("accuracy", 0) >= 95
    l2_ok = l2.get("failed", 99) == 0
    l3_ok = l3.get("avg_overall_score", 0) >= 50
    
    if l1_ok and l2_ok and l3_ok:
        print("\n  🎉 全部通过!")
    else:
        print("\n  ⚠️ 存在未通过的测试项")
    
    return combined


if __name__ == "__main__":
    main()
