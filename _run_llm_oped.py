# -*- coding: utf-8 -*-
"""
_run_llm_oped.py — oped_argument 真实 LLM 管线
================================================
使用 DeepSeek API 跑完整管线并输出 Markdown
"""
import sys, os, json
from pathlib import Path

# Set API key
os.environ["DEEPSEEK_API_KEY"] = "sk-91c9278a57b84e909c823c2acc4fae10"

REPO_ROOT = Path(__file__).resolve().parent


def load_module(file_path, cache_key):
    import importlib.util
    if cache_key in sys.modules:
        return sys.modules[cache_key]
    spec = importlib.util.spec_from_file_location(cache_key, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module


# ─── 1. Load modules ───────────────────────────────────────────────
RADAR_O    = load_module(REPO_ROOT / "platform/1_ingest/radar/radar_opinion.py",       "_spdt_radar_op")
ARTICLE_O  = load_module(REPO_ROOT / "platform/2_structure/article/article_opinion.py", "_spdt_article_op")
RENDER_O   = load_module(REPO_ROOT / "platform/3_render/engines/text/render_opinion.py", "_spdt_render_op")
SCORECARD_O = load_module(REPO_ROOT / "platform/4_adapt/scorecard/scorecard_opinion.py", "_spdt_scorecard_op")

topic = "AI监管：必要的刹车而非倒车"

# ─── 2. Stage 1: Ingest ─────────────────────────────────────────
print("=" * 60)
print("[S1] LLM RadarOpinion...")
radar = RADAR_O.RadarOpinion()
req = RADAR_O.RadarOpinionRequest(
    topic=topic, perspective="支持",
    industry_focus="科技行业", max_signals=4
)
brief = radar.run(req)
brief_dict = brief.to_dict()
print(f"  brief_id={brief_dict['brief_id']}")
print(f"  support={len(brief_dict['supporting_signals'])} "
      f"opposing={len(brief_dict['opposing_signals'])} "
      f"rebuttals={len(brief_dict['rebuttal_points'])}")

# ─── 3. Stage 2: Structure ──────────────────────────────────────
print("=" * 60)
print("[S2] LLM ArticleOpinion...")
article_gen = ARTICLE_O.ArticleOpinion()
article_result = article_gen.run(brief, title=topic)
article_dict = article_result.to_dict()
print(f"  outline_id={article_dict['outline_id']}")
print(f"  sections={list(article_dict['sections'].keys())}")
print(f"  word_count={article_dict['total_word_count']}")

# ─── 4. Stage 3: Render ─────────────────────────────────────────
print("=" * 60)
print("[S3] LLM RenderOpinion...")
renderer = RENDER_O.RenderOpinion()
render_result = renderer.run(article_result, brand_voice="assertive")
render_dict = render_result.to_dict()
print(f"  content_id={render_dict['content_id']}")
print(f"  word_count={render_dict['word_count']}")
print(f"  citations={len(render_dict['citations'])}")
print(f"  tone_check_passed={render_dict['tone_check']['passed']}")
if render_dict['tone_check'].get('violations'):
    print(f"  tone_violations={render_dict['tone_check']['violations']}")

# ─── 5. Stage 4: Adapt (Scorecard) ──────────────────────────────
print("=" * 60)
print("[S4] LLM ScorecardOpinion...")
scorecard_cls = SCORECARD_O.ScorecardOpinion()
scorecard_result = scorecard_cls.run(render_result)
sc_dict = scorecard_result.to_dict()
sc = sc_dict["scorecard"]
dims = sc["dimensions"]
print(f"  total_score={sc['total_score']}/100")
print(f"  action={sc_dict['action']}")
print(f"  logic={dims['logic']} factual={dims['factual']} source={dims['source']}")
print(f"  readability={dims['readability']} brand={dims['brand']}")

# ─── 6. Save Markdown ────────────────────────────────────────────
output_dir = REPO_ROOT / "platform/5_deliver/results/delivered/oped_argument"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / f"oped_argument_AI_jianguan_2026-07-31_83.md"

md = render_dict["markdown"]
fm = f"""---
title: "{article_dict["title"]}"
content_type: oped_argument
publish_time: "{render_dict["timestamp"]}"
keywords: ["AI监管", "观点评论", "科技行业"]
score: {sc["total_score"]}
action: {sc_dict["action"]}
dimensions:
  logic: {dims["logic"]}
  factual: {dims["factual"]}
  source: {dims["source"]}
  readability: {dims["readability"]}
  brand: {dims["brand"]}
gray_zones: {sc_dict["gray_zones"]}
---

"""
full_md = fm + md
output_path.write_text(full_md, encoding="utf-8")
print("=" * 60)
print(f"[OUTPUT] Saved: {output_path}")
print(f"  size={len(full_md)} bytes")
print("DONE")
