# -*- coding: utf-8 -*-
"""
_run_magazine_demo.py - SPDT-005 科学杂志生成器 Demo (v1.1)
================================================================

v1.0: 预置模板生成 Blueprint
v1.1: LLM 增强 Blueprint（自动推荐文章 topic + 编辑手记）

运行：
  python _run_magazine_demo.py
  python _run_magazine_demo.py --no-llm   # 预置模板模式
"""

import os
import sys
import time
import argparse
from pathlib import Path

# 强制 UTF-8 输出
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 设置 API Key
os.environ["DEEPSEEK_API_KEY"] = "sk-91c9278a57b84e909c823c2acc4fae10"

REPO_ROOT = Path(__file__).resolve().parent
TS = str(int(time.time() * 1000))


def load_magazine_module(name: str):
    """安全加载杂志模块"""
    import importlib.util, sys as _sys
    cache_key = f"_mg_{TS}_{name}"
    for m in list(_sys.modules.keys()):
        if m.startswith("_mg_"):
            del _sys.modules[m]
    path = REPO_ROOT / f"platform/2_structure/magazine/{name}.py"
    spec = importlib.util.spec_from_file_location(cache_key, str(path))
    m = importlib.util.module_from_spec(spec)
    _sys.modules[cache_key] = m
    spec.loader.exec_module(m)
    return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true", help="Use template mode instead of LLM")
    args = parser.parse_args()

    use_llm = not args.no_llm
    mode = "LLM-enhanced (v1.1)" if use_llm else "Template-based (v1.0)"

    print("=" * 70)
    print(f"SPDT-005 Magazine Generator - {mode}")
    print("Topic: AI for Science Breakthroughs")
    print("=" * 70)

    # Step 1: Blueprint
    print("\n[Step 1] Loading MagazineBlueprint...")
    bp_mod = load_magazine_module("magazine_blueprint")

    if use_llm:
        gen = bp_mod.MagazineBlueprintGenerator().init_llm()
        blueprint = gen.generate(
            domain_topic="人工智能与科学研究的交叉突破",
            title="科学前沿",
            issue="2026-Q3",
            audience="理工科研究生及以上",
            description="聚焦 AI for Science 领域的最新突破与思考",
        )
        if hasattr(blueprint, "_llm_editor_note"):
            print(f"  LLM Editor note: {blueprint._llm_editor_note[:80]}...")
    else:
        blueprint = bp_mod.load_blueprint(
            domain_topic="人工智能与科学研究的交叉突破",
            title="科学前沿",
            issue="2026-Q3",
            audience="理工科研究生及以上",
            description="聚焦 AI for Science 领域",
        )

    print(f"  Blueprint ID: {blueprint.blueprint_id}")
    print(f"  Articles: {len(blueprint.articles)}")
    for art in blueprint.articles:
        angle = art.constraints.get("angle", "")[:50]
        print(f"    [{art.article_role:12s}] {art.topic[:50]}")
        if angle:
            print(f"                     angle: {angle}")

    # Step 2: Orchestration
    print("\n[Step 2] Orchestrating pipelines (parallel)...")
    orch_mod = load_magazine_module("magazine_orchestrator")
    orchestrator = orch_mod.MagazineOrchestrator()

    t0 = time.time()
    run_result = orchestrator.run(blueprint)
    elapsed = time.time() - t0

    print(f"\n  Done in {elapsed:.1f}s")
    print(f"  Overall: {'ALL_PASS' if run_result.all_passed else 'NEED_REVISE'}")
    for role, art in run_result.articles.items():
        status = "PASS" if art.passed else "FAIL"
        if art.error:
            status = f"ERR:{art.error[:50]}"
        print(f"    {status} [{role:15s}] score={art.total_score:5.1f}")

    # Step 3: Assembly
    print("\n[Step 3] Assembling magazine...")
    asm_mod = load_magazine_module("magazine_assembler")
    assembler = asm_mod.MagazineAssembler()

    artifact = assembler.assemble(run_result, fmt="markdown")
    print(f"  Output: {artifact.output_dir}")
    print(f"  File: magazine_{artifact.issue}.md")

    # Quality summary
    print("\n" + "=" * 70)
    print("Quality Summary")
    print("=" * 70)
    for role, art in sorted(run_result.articles.items()):
        icon = "PASS" if art.passed else "FAIL"
        dims = art.scorecard.get("dimensions", {})
        dims_str = " | ".join([f"{k}={v.get('score',v) if isinstance(v,dict) else v}"
                                for k, v in list(dims.items())[:4]])
        print(f"[{icon}] {role:15s} total={art.total_score:5.1f}")
        if dims_str:
            print(f"        {dims_str}")

    # Metadata
    import json
    meta_path = artifact.output_dir / "run_summary.json"
    meta_path.write_text(json.dumps(run_result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Metadata: {meta_path}")
    print("\nALL DONE")


if __name__ == "__main__":
    main()
