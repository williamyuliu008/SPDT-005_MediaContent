# -*- coding: utf-8 -*-
"""跑测全部3条管线：science_research + deep_industry_report + oped_argument"""
import sys, os, json, time, re
from pathlib import Path
from datetime import date

os.environ["DEEPSEEK_API_KEY"] = "sk-91c9278a57b84e909c823c2acc4fae10"
REPO_ROOT = Path(__file__).resolve().parent
_RUN_TS = str(int(time.time() * 1000))


def load_module(file_path, cache_key):
    import importlib.util
    key = f"{_RUN_TS}_{cache_key}"
    for m in list(sys.modules.keys()):
        if m.startswith(('_spdt', '_m_', key)):
            del sys.modules[m]
    spec = importlib.util.spec_from_file_location(key, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def get_dict(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(obj)
    return dict(obj) if obj else {}


def extract_score(sc_dict):
    sc = sc_dict.get("scorecard", sc_dict)
    inner = sc.get("scorecard", {}) if isinstance(sc, dict) else {}
    total = inner.get("total_score", sc.get("total_score", 0)) if isinstance(sc, dict) else 0
    dims = inner.get("dimensions", sc.get("dimensions", {})) if isinstance(sc, dict) else {}
    action = sc_dict.get("action", "?")
    return total, dims, action


def para_stats(md):
    """段落统计"""
    body = re.sub(r'(?s)^---.*?---\n', '', md)
    body = re.sub(r'(?m)^#.+$', '', body)
    paras = [p.strip() for p in re.findall(r'(?m)^(.+)$', body) if len(p.strip()) > 20]
    if not paras:
        return "N/A", "N/A", "N/A", "N/A"
    lens = [len(p) for p in paras]
    long_cnt = len([p for p in paras if len(p) > 120])
    sentences = len(re.findall(r'[。！？]', body))
    return len(paras), sum(lens)//len(paras), max(lens), long_cnt


def save_md(out_dir, ct_label, topic, total, action, md):
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '_', topic[:20])
    today = date.today().isoformat()
    path = out_dir / f"{ct_label}_{slug}_{today}_{total:.0f}.md"
    fm = f'---\ntitle: "{topic}"\ncontent_type: {ct_label}\nscore: {total}\naction: {action}\n---\n\n'
    path.write_text(fm + md, encoding="utf-8")
    return path


# ─── Pipeline 1: science_research ───────────────────────────────
def run_science_research():
    print("\n" + "=" * 70)
    print("PIPELINE 1: science_research")
    print("=" * 70)

    topic = "量子计算突破：Google Willow芯片的科学意义"
    RADAR   = load_module(REPO_ROOT / "platform/1_ingest/radar/radar_science_fact.py",       "_m_sr1")
    ARTICLE = load_module(REPO_ROOT / "platform/2_structure/article/article_science_fact.py", "_m_sr2")
    RENDER  = load_module(REPO_ROOT / "platform/3_render/engines/text/render_science_fact.py", "_m_sr3")
    SCARD   = load_module(REPO_ROOT / "platform/4_adapt/scorecard/scorecard_science_fact.py", "_m_sr4")

    # S1
    req = RADAR.RadarScienceFactRequest(topic=topic, channels=[])
    res1 = RADAR.RadarScienceFact().run(req)
    brief = res1.brief
    print(f"[S1] brief_id={brief.get('brief_id','?')} signals={len(brief.get('signals',[]))}")

    # S2
    res2 = ARTICLE.ArticleScienceFact().run(brief)
    outline_dict = get_dict(res2.outline)
    if "outline" in outline_dict:
        outline_dict = outline_dict["outline"]
    secs = outline_dict.get("sections", [])
    print(f"[S2] sections={len(secs)}")

    # S3
    res3 = RENDER.RenderScienceFact().run(outline_dict)
    article = res3.article
    article_dict = get_dict(article)
    md = article_dict.get("markdown", "")
    print(f"[S3] word_count={article_dict.get('word_count','?')}")

    # S4
    res4 = SCARD.ScorecardScienceFact().run(article)
    total, dims, action = extract_score(get_dict(res4))
    print(f"[S4] score={total:.1f}/100 action={action}")
    print(f"     dims: {json.dumps(dims, ensure_ascii=False)}")

    n_para, avg_len, max_len, n_long = para_stats(md)
    print(f"[MD] paras={n_para} avg_len={avg_len}字 max={max_len}字 long_para={n_long}")

    path = save_md(REPO_ROOT / "platform/5_deliver/results/delivered/science_research",
                   "science_research", topic, total, action, md)
    print(f"[OUT] {path.name}")
    return {"type": "science_research", "score": total, "action": action,
            "dims": dims, "para_stats": f"p{n_para}/avg{avg_len}字/max{max_len}字/long{n_long}"}


# ─── Pipeline 2: deep_industry_report ──────────────────────────
def run_deep_industry():
    print("\n" + "=" * 70)
    print("PIPELINE 2: deep_industry_report")
    print("=" * 70)

    topic = "2026年中国新能源汽车行业深度分析"
    RADAR   = load_module(REPO_ROOT / "platform/1_ingest/radar/radar_deep_industry.py",        "_m_di1")
    ARTICLE = load_module(REPO_ROOT / "platform/2_structure/article/article_deep_industry.py", "_m_di2")
    RENDER  = load_module(REPO_ROOT / "platform/3_render/engines/text/render_deep_industry.py", "_m_di3")
    SCARD   = load_module(REPO_ROOT / "platform/4_adapt/scorecard/scorecard_deep_industry.py", "_m_di4")

    req = RADAR.RadarDeepIndustryRequest(topic=topic, industry="新能源汽车", max_signals=5)
    res1 = RADAR.RadarDeepIndustry().run(req)
    brief = res1.brief
    print(f"[S1] sources={len(brief.get('sources', []))}")

    res2 = ARTICLE.ArticleDeepIndustry().run(brief)
    outline_dict = get_dict(res2.outline)
    if "outline" in outline_dict:
        outline_dict = outline_dict["outline"]
    secs = outline_dict.get("sections", [])
    print(f"[S2] sections={len(secs)}")

    res3 = RENDER.RenderDeepIndustry().run(outline_dict)
    article = res3.article
    article_dict = get_dict(article)
    md = article_dict.get("markdown", "")
    print(f"[S3] word_count={article_dict.get('word_count','?')}")

    res4 = SCARD.ScorecardDeepIndustry().run(article)
    total, dims, action = extract_score(get_dict(res4))
    print(f"[S4] score={total:.1f}/100 action={action}")
    print(f"     dims: {json.dumps(dims, ensure_ascii=False)}")

    n_para, avg_len, max_len, n_long = para_stats(md)
    print(f"[MD] paras={n_para} avg_len={avg_len}字 max={max_len}字 long_para={n_long}")

    path = save_md(REPO_ROOT / "platform/5_deliver/results/delivered/deep_industry_report",
                   "deep_industry_report", topic, total, action, md)
    print(f"[OUT] {path.name}")
    return {"type": "deep_industry_report", "score": total, "action": action,
            "dims": dims, "para_stats": f"p{n_para}/avg{avg_len}字/max{max_len}字/long{n_long}"}


# ─── Pipeline 3: oped_argument ─────────────────────────────────
def run_oped():
    print("\n" + "=" * 70)
    print("PIPELINE 3: oped_argument")
    print("=" * 70)

    topic = "AI监管：必要的刹车而非倒车"
    RADAR   = load_module(REPO_ROOT / "platform/1_ingest/radar/radar_opinion.py",          "_m_op1")
    ARTICLE = load_module(REPO_ROOT / "platform/2_structure/article/article_opinion.py",       "_m_op2")
    RENDER  = load_module(REPO_ROOT / "platform/3_render/engines/text/render_opinion.py",    "_m_op3")
    SCARD   = load_module(REPO_ROOT / "platform/4_adapt/scorecard/scorecard_opinion.py",     "_m_op4")

    req = RADAR.RadarOpinionRequest(
        topic=topic, perspective="支持",
        industry_focus="科技行业", max_signals=4
    )
    brief = RADAR.RadarOpinion().run(req)
    brief_dict = brief.to_dict()
    print(f"[S1] brief_id={brief_dict['brief_id']} "
          f"support={len(brief_dict['supporting_signals'])} "
          f"oppose={len(brief_dict['opposing_signals'])}")

    res2 = ARTICLE.ArticleOpinion().run(brief, title=topic)
    article_dict = res2.to_dict()
    print(f"[S2] outline_id={article_dict['outline_id']} "
          f"sections={list(article_dict['sections'].keys())}")

    res3 = RENDER.RenderOpinion().run(res2, brand_voice="assertive")
    render_dict = res3.to_dict()
    md = render_dict["markdown"]
    print(f"[S3] word_count={render_dict['word_count']} "
          f"citations={len(render_dict['citations'])} "
          f"tone_ok={render_dict['tone_check']['passed']}")

    res4 = SCARD.ScorecardOpinion().run(res3)
    sc_dict = res4.to_dict()
    sc = sc_dict["scorecard"]
    dims = sc["dimensions"]
    total = sc["total_score"]
    action = sc_dict["action"]
    print(f"[S4] score={total:.1f}/100 action={action}")
    print(f"     dims: {json.dumps(dims, ensure_ascii=False)}")

    n_para, avg_len, max_len, n_long = para_stats(md)
    print(f"[MD] paras={n_para} avg_len={avg_len}字 max={max_len}字 long_para={n_long}")

    path = save_md(REPO_ROOT / "platform/5_deliver/results/delivered/oped_argument",
                   "oped_argument", topic, total, action, md)
    print(f"[OUT] {path.name}")
    return {"type": "oped_argument", "score": total, "action": action,
            "dims": dims, "para_stats": f"p{n_para}/avg{avg_len}字/max{max_len}字/long{n_long}"}


# ─── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    results = []
    results.append(run_science_research())
    results.append(run_deep_industry())
    results.append(run_oped())

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"{'Pipeline':<30} {'Score':>8} {'Action':<10} {'Para Stats'}")
    print("-" * 70)
    for r in results:
        print(f"{r['type']:<30} {r['score']:>7.1f}  {r['action']:<10} {r['para_stats']}")
    print("=" * 70)
