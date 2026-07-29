import sys, json
sys.path.insert(0, r'D:\92_products\SmartTextPlatform')
from smartext.engine import SmartTextEngine

engine = SmartTextEngine()

with open(r'D:\9_infra\radar_platform\bundles\ai_tech\2026-06\0617.json','r',encoding='utf-8') as f:
    bundle = json.load(f)

result = engine.generate(bundle, 'daily_report')
print('Keys:', list(result.keys()))
for k, v in result.items():
    if isinstance(v, dict):
        print(f'  {k}: {list(v.keys())[:5]}')
    elif isinstance(v, str):
        print(f'  {k}: {len(v)} chars')
    else:
        print(f'  {k}: {v}')
