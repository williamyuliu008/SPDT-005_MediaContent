"""CLUSTER — SmartTextPlatform V3 (递进式管道)"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.cluster_engine_v3 import ClusterEngineV3

def main():
    cluster_id = os.path.basename(os.path.dirname(__file__))
    print(f"SmartTextPlatform V3 — {cluster_id}")
    engine = ClusterEngineV3(cluster_id)
    router_output = {
        "structured_spec": {"core_intent": "测试", "product_type": "测试"},
        "configuration": {"cluster": cluster_id},
    }
    t0 = time.time()
    results = engine.run_full_pipeline(router_output)
    for sid, r in results.items():
        chars = len(r.get("output", {}).get("content", ""))
        print(f"  [OK] {sid}: {chars} chars")
    total = (time.time() - t0) * 1000
    print(f"  Total: {total:.0f}ms")

if __name__ == "__main__":
    main()
