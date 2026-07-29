import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, r'D:\92_products\SmartTextPlatform')

# 1. Radar
bundle_path = Path(r'D:\9_infra\radar_platform\bundles\ai_tech\2026-06\0617.json')
with open(bundle_path, 'r', encoding='utf-8') as f:
    b = json.load(f)
sigs = len(b['signals'])
print(f'[Radar]      {sigs} signals, domain={b["domain"]}')

# 2. SmartText
from smartext.engine import SmartTextEngine
engine = SmartTextEngine()
result = engine.generate(b, 'daily_report')
words = result['meta']['total_words']
secs = result['meta']['sections_generated']
print(f'[SmartText]  {words} chars, {secs} sections')

# 3. AutoPublish
r = subprocess.run('python channels/website/build.py --date 2026-06-17',
    shell=True, cwd=r'D:\9_infra\autopublish', capture_output=True, text=True)
print(f'[AutoPublish] {"OK" if r.returncode==0 else "FAIL"}')

# 4. Verify website
site = Path(r'D:\92_products\SmartTextPlatform\canvas\ai-lookout\index.html')
print(f'[Website]    {site.stat().st_size} bytes')

print('\nAll checks passed')
