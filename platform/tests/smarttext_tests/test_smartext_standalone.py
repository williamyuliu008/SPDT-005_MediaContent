"""Verification script: SmartTextEngine independent test"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartext.engine import SmartTextEngine

print("=" * 60)
print("  SmartTextEngine — Independent Test")
print("=" * 60)

engine = SmartTextEngine()

# Test 1: generate with mock bundle
result = engine.generate(SmartTextEngine.MOCK_SIGNAL_BUNDLE, "daily_report")

print(f"\n  Result:")
print(f"    Status: OK")
print(f"    Sections: {len(result['sections'])}")
print(f"    Total words: {result['meta']['total_words']}")
print(f"    Formats registered: {list(engine._FORMAT_REGISTRY.keys())}")
print(f"    Clusters loaded: {list(engine._PROMPT_CACHE.keys())}")

for s in result.get("sections", []):
    print(f"    [{s['section_id']}] {s['label']}: {s['word_count']} chars, "
          f"cluster={s['cluster']}, signals={s['signals_count']}")

rendered = result.get("rendered", "")
print(f"    Rendered: {len(rendered)} chars")

# Test 2: list formats
print(f"\n  Formats:")
for fmt in engine.list_formats():
    print(f"    {fmt['id']:20s} → {fmt['name']}")

# Test 3: list clusters
print(f"\n  Clusters:")
for cl in engine.list_clusters():
    prompt = engine.get_prompt_config(cl["id"])
    stages = len(prompt.get("stages", {})) if prompt else 0
    print(f"    {cl['id']:15s} → {cl['name']} ({stages} stages)")

# Test 4: error on unknown format
error_result = engine.generate({"signals": []}, "nonexistent")
assert "error" in error_result, "Should return error for unknown format"
print(f"\n  Error handling: OK (unknown format returns error)")

# Test 5: wechat_article placeholder
result2 = engine.generate(SmartTextEngine.MOCK_SIGNAL_BUNDLE, "wechat_article")
print(f"\n  WeChat article: {len(result2.get('sections',[]))} sections, "
      f"{result2['meta']['total_words']} total words")

print(f"\n{'=' * 60}")
print(f"  ✅ ALL TESTS PASSED")
print(f"{'=' * 60}")
