# -*- coding: utf-8 -*-
"""
_reorganize_output.py — 重构 5_deliver 输出目录结构
======================================================

旧结构（问题）：
  5_deliver/checkpoint/results/   ← 所有文件平铺，无分类

新结构（规划）：
  5_deliver/
  ├── checkpoint/
  │   ├── checkpoints/            ← 各阶段中间快照 CHK_*.json
  │   └── policy_audit.jsonl     ← Policy 审计日志
  ├── results/
  │   ├── delivered/              ← action=deliver（已发布成品）
  │   │   ├── oped_argument/
  │   │   ├── deep_industry_report/
  │   │   ├── science_research/
  │   │   └── breakdown_news/
  │   ├── revise/                ← action=revise（待修改）
  │   └── archive/                ← 历史测试文件（已废弃）
  └── product/                    ← 最终发布产品（已上线版本）
      └── <content_type>/<date>_<title>.md

运行方式：python _reorganize_output.py
"""

import json, re, os, shutil
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "platform/5_deliver/checkpoint/results"
CHECKPOINT_DIR = REPO_ROOT / "platform/5_deliver/checkpoint/checkpoints"
DELIVER_BASE = REPO_ROOT / "platform/5_deliver/results/delivered"
ARCHIVE_DIR = REPO_ROOT / "platform/5_deliver/results/archive"
REVISE_DIR = REPO_ROOT / "platform/5_deliver/results/revise"

# ── 子类型目录 ─────────────────────────────────────────────────
SUB_DIRS = [
    "oped_argument",
    "deep_industry_report",
    "science_research",
    "breakdown_news",
    "science_fact",
    "product_review",
    "creative",
]


def slugify(title: str) -> str:
    """标题转换为安全文件名"""
    s = re.sub(r'[\\/:*?"<>|]', "", title)
    s = re.sub(r'\s+', "_", s.strip())
    return s[:40]


def ensure_dirs():
    """创建所有目标目录"""
    DELIVER_BASE.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    REVISE_DIR.mkdir(parents=True, exist_ok=True)
    for sub in SUB_DIRS:
        (DELIVER_BASE / sub).mkdir(parents=True, exist_ok=True)
        (ARCHIVE_DIR / sub).mkdir(parents=True, exist_ok=True)
        (REVISE_DIR / sub).mkdir(parents=True, exist_ok=True)
    print("[OK] 目录结构已创建")


def parse_pipeline_json(path: Path) -> dict:
    """解析 Pipeline JSON，提取 metadata"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        spec = data.get("content_spec", {})
        content_type = spec.get("content_type", "unknown")
        title = spec.get("title", "无题")
        # scorecard 可能在 artifact 或外层
        sc = data.get("artifact", {}).get("scorecard", {})
        if isinstance(sc, dict):
            total = sc.get("total_score", sc.get("scorecard", {}).get("total_score", 0))
        else:
            total = 0
        # action
        action = data.get("artifact", {}).get("action", "unknown")
        ts = data.get("completed_at", data.get("timestamp", ""))
        date_str = ts[:10] if ts else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {
            "content_type": content_type,
            "title": title,
            "score": total,
            "action": action,
            "date": date_str,
            "pipeline_id": data.get("pipeline_id", path.stem),
        }
    except Exception as e:
        return {"content_type": "unknown", "title": path.stem, "score": 0,
                "action": "unknown", "date": "", "pipeline_id": path.stem}


def classify_and_move():
    """遍历 results/，按 action 分类移动文件"""
    moved = {"delivered": [], "revise": [], "archive": []}
    to_archive = []

    if not RESULTS_DIR.exists():
        print("[WARN] results/ 目录不存在，跳过")
        return moved

    for fp in sorted(RESULTS_DIR.iterdir()):
        if fp.is_dir():
            continue

        stem = fp.stem
        suffix = fp.suffix.lower()

        # 跳过非目标文件
        if suffix not in (".json", ".md"):
            print(f"  [SKIP] {fp.name} (非目标类型)")
            continue

        # Markdown 文件 → 直接分类
        if suffix == ".md":
            ct = "unknown"
            # 尝试从 frontmatter 提取 content_type
            try:
                text = fp.read_text(encoding="utf-8")
                m = re.search(r'content_type:\s*"?([^"\n]+)"?', text)
                if m:
                    ct = m.group(1).strip()
                # 提取 score
                m2 = re.search(r'^score:\s*([\d.]+)', text, re.MULTILINE)
                score = float(m2.group(1)) if m2 else 0
                # 提取 action
                m3 = re.search(r'^action:\s*"?([^"\n]+)"?', text, re.MULTILINE)
                action = m3.group(1).strip() if m3 else "unknown"
                # 提取 title
                m4 = re.search(r'^title:\s*"?([^"\n]+)"?', text)
                title = m4.group(1).strip() if m4 else "无题"
            except Exception:
                ct, score, action, title = "unknown", 0, "unknown", fp.stem

            ct_dir = ct if ct in SUB_DIRS else "unknown"
            if action == "deliver":
                dest = DELIVER_BASE / ct_dir / fp.name
            elif action == "revise":
                dest = REVISE_DIR / ct_dir / fp.name
            else:
                dest = ARCHIVE_DIR / ct_dir / fp.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(fp), str(dest))
            moved.get(action, moved["archive"]).append(str(fp.relative_to(REPO_ROOT)))
            print(f"  [MD] {action:8s} {ct_dir:25s} → {dest.name}")
            continue

        # JSON 文件
        if not stem.startswith("PL_"):
            print(f"  [SKIP] {fp.name} (非 Pipeline 结果)")
            continue

        meta = parse_pipeline_json(fp)
        ct = meta["content_type"]
        action = meta["action"]
        ct_dir = ct if ct in SUB_DIRS else "unknown"

        # 判断是否归档（历史测试文件通常是 breakdown_news 且 action=pass 或空）
        is_test = ct == "breakdown_news" and action in ("pass", "unknown", "")

        if action == "deliver":
            dest = DELIVER_BASE / ct_dir / fp.name
            moved["delivered"].append(str(fp.relative_to(REPO_ROOT)))
        elif action == "revise":
            dest = REVISE_DIR / ct_dir / fp.name
            moved["revise"].append(str(fp.relative_to(REPO_ROOT)))
        else:
            dest = ARCHIVE_DIR / ct_dir / fp.name
            moved["archive"].append(str(fp.relative_to(REPO_ROOT)))

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(fp), str(dest))
        print(f"  [JSON] {action:8s} {ct_dir:25s} {meta['title'][:30]:30s} score={meta['score']}")

    return moved


def build_manifest():
    """生成清单文件"""
    manifest = {"generated_at": datetime.now(timezone.utc).isoformat(), "delivered": {}, "revise": {}, "archive": {}}

    for section, key in [("delivered", "delivered"), ("revise", "revise"), ("archive", "archive")]:
        base = {
            "delivered": DELIVER_BASE,
            "revise": REVISE_DIR,
            "archive": ARCHIVE_DIR,
        }[section]
        manifest[key] = {}
        for sub in SUB_DIRS:
            sub_dir = base / sub
            if sub_dir.exists():
                files = sorted([f.name for f in sub_dir.iterdir() if f.is_file()])
                if files:
                    manifest[key][sub] = files

    manifest_path = REPO_ROOT / "platform/5_deliver/results/MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] MANIFEST.json 已生成: {manifest_path}")


def print_summary():
    """打印目录树"""
    print("\n" + "=" * 60)
    print("[NEW DIR STRUCTURE]")
    for section in ["delivered", "revise", "archive"]:
        base = {
            "delivered": DELIVER_BASE,
            "revise": REVISE_DIR,
            "archive": ARCHIVE_DIR,
        }[section]
        print(f"\n{base.relative_to(REPO_ROOT)}/")
        for sub in SUB_DIRS:
            sub_dir = base / sub
            if sub_dir.exists():
                files = sorted([f.name for f in sub_dir.iterdir() if f.is_file()])
                if files:
                    print(f"  {sub}/ ({len(files)} files)")
                    for fn in files[:5]:
                        print(f"    - {fn}")
                    if len(files) > 5:
                        print(f"    ... +{len(files)-5} more")


if __name__ == "__main__":
    print("=" * 60)
    print("[STEP 1] 创建目录结构")
    ensure_dirs()

    print("\n" + "=" * 60)
    print("[STEP 2] 分类移动现有文件")
    moved = classify_and_move()

    print("\n" + "=" * 60)
    print("[STEP 3] 生成 MANIFEST.json")
    build_manifest()

    print_summary()

    print("\n" + "=" * 60)
    print(f"[DONE] moved: delivered={len(moved['delivered'])} "
          f"revise={len(moved['revise'])} archive={len(moved['archive'])}")
