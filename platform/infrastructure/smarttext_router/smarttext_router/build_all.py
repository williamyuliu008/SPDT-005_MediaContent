#!/usr/bin/env python3
"""
SmartTextPlatform · 一键构建 v2.0（三段编排）
Radar → SmartText → AutoPublish
"""

import sys, os, json, subprocess, argparse, time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
RADAR_PLATFORM = Path(r"D:\9_infra\radar_platform")
AUTOPUBLISH = Path(r"D:\9_infra\autopublish")


def run(cmd, cwd=None):
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        r = subprocess.run(cmd, shell=True, cwd=cwd or PROJECT_ROOT,
                          capture_output=True, text=True, timeout=120,
                          encoding='utf-8', errors='replace', env=env)
        return r.returncode == 0, (r.stdout or '') + '\n' + (r.stderr or '')
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--domain', default='ai_tech')
    parser.add_argument('--format', default='daily_report')
    parser.add_argument('--channel', default='website')
    args = parser.parse_args()

    date_str = args.date
    print("=" * 70)
    print(f"  三段工具链构建  {date_str}")
    print(f"  Radar({args.domain}) -> SmartText({args.format}) -> AutoPublish({args.channel})")
    print("=" * 70)

    t_start = time.time()

    # ═══ Layer 1: Radar ═══
    print(f"\n[1/3] Radar: {args.domain} 领域扫描")
    ok, out = run(f"python engine/pipeline.py --domain {args.domain} --date {date_str}",
                  cwd=RADAR_PLATFORM)
    for line in out.strip().split('\n')[-2:]:
        print(f"  {line.strip()[:100]}")

    # 找 bundle
    dd = date_str[5:7] + date_str[8:10]
    bundle_path = RADAR_PLATFORM / "bundles" / args.domain / date_str[:7] / f"{dd}.json"
    if not bundle_path.exists():
        # 回退
        bundles = sorted(RADAR_PLATFORM.rglob(f"bundles/{args.domain}/**/*.json"))
        bundle_path = bundles[-1] if bundles else None
    if bundle_path and bundle_path.exists():
        with open(bundle_path, 'r', encoding='utf-8') as f:
            sigs = len(json.load(f).get('signals', []))
        print(f"  {'✅' if ok else '🔄'} {sigs} signals -> {bundle_path.name}")
    else:
        print(f"  ❌ No bundle found")
        return 1

    # ═══ Layer 2: SmartText ═══
    print(f"\n[2/3] SmartText: {args.format} 生成")
    md_out = PROJECT_ROOT / "channels" / f"{date_str}.md"
    json_out = PROJECT_ROOT / "channels" / f"{date_str}.json"
    bridge = PROJECT_ROOT / "channels" / "_smartext_bridge.py"

    ok2, out2 = run(f'python "{bridge}" "{bundle_path}" {args.format} "{md_out}" "{json_out}"')
    for line in out2.strip().split('\n'):
        if 'OK:' in line or 'Error' in line:
            print(f"  {line.strip()[:100]}")
    print(f"  {'✅' if ok2 else '❌'} channels/{date_str}.md")
    ok = ok and ok2

    # ═══ Layer 3: AutoPublish ═══
    print(f"\n[3/3] AutoPublish: {args.channel} 部署")
    ok3, out3 = run(f"python channels/website/build.py --date {date_str}",
                    cwd=AUTOPUBLISH)
    for line in out3.strip().split('\n')[-2:]:
        print(f"  {line.strip()[:100]}")
    print(f"  {'✅' if ok3 else '❌'} 网站更新")
    ok = ok and ok3

    # ═══ 知识底座 ═══
    print(f"\n[+] 知识底座更新")
    run("python knowledge_base/extract_entities.py")

    # ═══ 验证 ═══
    elapsed = time.time() - t_start
    checks = {
        "日报": (PROJECT_ROOT / "channels" / f"{date_str}.md").exists(),
        "网站": (PROJECT_ROOT / "canvas" / "ai-lookout" / "index.html").exists(),
        "索引": (PROJECT_ROOT / "canvas" / "ai-lookout" / "search" / "index.json").exists(),
        "知识": (PROJECT_ROOT / "knowledge_base" / "index.json").exists(),
    }
    print(f"\n{'='*70}")
    for name, okv in checks.items():
        print(f"  {'✅' if okv else '❌'} {name}")
    all_pass = all(checks.values())
    print(f"  {elapsed:.1f}s | {'全部通过' if all_pass else '有未达标项'}")
    print(f"{'='*70}")
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
