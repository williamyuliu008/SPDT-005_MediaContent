#!/usr/bin/env python3
"""SmartText 生成桥接脚本 — 供 build_all.py 调用"""
import sys, json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from smartext.engine import SmartTextEngine

bundle_path = sys.argv[1]
format_name = sys.argv[2]
out_md = sys.argv[3]
out_json = sys.argv[4]

with open(bundle_path, 'r', encoding='utf-8') as f:
    bundle = json.load(f)

engine = SmartTextEngine()
result = engine.generate(bundle, format_name)

with open(out_md, 'w', encoding='utf-8') as f:
    f.write(result.get('rendered', ''))
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

words = result.get('meta', {}).get('total_words', 0)
sections = result.get('meta', {}).get('sections_generated', 0)
print(f'OK: {words} chars, {sections} sections')
