#!/usr/bin/env python3
"""
AI 瞭望台日报生成器 v2.0 — 调用 SmartText Engine
────────────────────────────────────────────────
Radar Bundle → SmartTextEngine.generate() → 日报 Markdown

用法: python daily.py [--date YYYY-MM-DD]
"""

import sys, json, argparse
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RADAR_PLATFORM = Path(r"D:\9_infra\radar_platform")

sys.path.insert(0, str(PROJECT_ROOT))
from smartext.engine import SmartTextEngine


def find_bundle(domain, date_str):
    """查找 Radar Bundle，支持回退"""
    dd = date_str[5:7] + date_str[8:10]
    path = RADAR_PLATFORM / "bundles" / domain / date_str[:7] / f"{dd}.json"
    
    for attempt in range(3):
        if attempt == 0 and path.exists():
            return path
        # 回退
        prev = datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=attempt+1)
        p = RADAR_PLATFORM / "bundles" / domain / prev.strftime('%Y-%m') / f"{prev.strftime('%m%d')}.json"
        if p.exists():
            return p
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--domain', default='ai_tech')
    parser.add_argument('--format', default='daily_report')
    args = parser.parse_args()

    date_str = args.date
    print(f"📰 {args.format}: {date_str} (domain={args.domain})")

    # Load Radar Bundle
    bundle_path = find_bundle(args.domain, date_str)
    if not bundle_path:
        print(f"❌ 无可用 Radar Bundle")
        sys.exit(1)

    with open(bundle_path, 'r', encoding='utf-8') as f:
        bundle = json.load(f)

    # Generate via SmartText Engine
    engine = SmartTextEngine()
    result = engine.generate(bundle, args.format)

    # Save
    md_path = PROJECT_ROOT / "channels" / f"{date_str}.md"
    json_path = PROJECT_ROOT / "channels" / f"{date_str}.json"

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(result.get('rendered', ''))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    words = result.get('meta', {}).get('total_words', 0)
    sections = result.get('meta', {}).get('sections_generated', 0)
    print(f"✅ {md_path} ({words} chars, {sections} sections)")


if __name__ == '__main__':
    main()
