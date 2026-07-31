# -*- coding: utf-8 -*-
"""
_run_all_llm.py — science_research + deep_industry_report 真实 LLM 管线
========================================================================
"""
import sys, os, json, time
from pathlib import Path

os.environ["DEEPSEEK_API_KEY"] = "sk-91c9278a57b84e909c823c2acc4fae10"
REPO_ROOT = Path(__file__).resolve().parent

# 时间戳 cache key（避免复用旧模块实例）
_RUN_TS = str(int(time.time() * 1000))


def load_module(file_path, cache_key):
    import importlib.util
    key = f"{_RUN_TS}_{cache_key}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def get_dict(obj):
    """安全提取 dict：支持 dataclass / plain dict / 已有点名对象"""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(obj)
    return dict(obj) if obj else {}


def extract_score(sc_dict: dict) -> tuple[float, dict, str]:
    """
    从 ScorecardResult 提取总分、维度、action。
    scorecard_deep_industry 和 scorecard_science_fact 的结构：
      sc_dict = {
        "scorecard": {
          "header": {...},
          "scorecard": {"total_score": 94.0, "dimensions": {...}},
          ...
        },
        "passed": True,
        "action": "deliver",
        ...
      }
    """
    sc = sc_dict.get("scorecard", sc_dict)  # 安全兜底
    # 尝试两层嵌套
    inner = sc.get("scorecard", {}) if isinstance(sc, dict) else {}
    total = inner.get("total_score", sc.get("total_score", 0)) if isinstance(sc, dict) else 0
    dims = inner.get("dimensions", sc.get("dimensions", {})) if isinstance(sc, dict) else {}
    action = sc_dict.get("action", "?")
    return total, dims, action


def save_md(path, fm, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(fm + content, encoding="utf-8")


def run_pipeline(topic, ct_label):
    """运行指定类型的完整 4 阶段管线"""
    print("\n" + "=" * 60)
    print(f"[{ct_label.upper()}] LLM pipeline — topic: {topic[:30]}")
    print("=" * 60)

    if ct_label == "science_research":
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
        outline = res2.outline
        outline_dict = get_dict(outline)
        sec_list = outline_dict.get("sections", [])
        sec_names = [s.get("section_id","")[:20] for s in (sec_list if isinstance(sec_list, list) else [])]
        print(f"[S2] sections={sec_names}")

        # S3
        res3 = RENDER.RenderScienceFact().run(outline)
        article = res3.article
        article_dict = get_dict(article)
        # v1.3: 从雷达 brief 注入来源验证状态到 article metadata
        article_dict.setdefault("metadata", {})["source_verified_count"] = (
            brief.get("header", {}).get("source_verified_count", 0)
            if "header" in brief
            else 0
        )
        md = article_dict.get("markdown", "")
        print(f"[S3] word_count={article_dict.get('word_count','?')}")

        # S4
        res4 = SCARD.ScorecardScienceFact().run(article)
        sc_dict = get_dict(res4)
        total, dims, action = extract_score(sc_dict)
        print(f"[S4] score={total:.1f}/100 action={action}")
        print(f"     factual={dims.get('factual')} source={dims.get('source')} "
              f"readability={dims.get('readability')} depth={dims.get('depth')}")

    elif ct_label == "deep_industry_report":
        RADAR   = load_module(REPO_ROOT / "platform/1_ingest/radar/radar_deep_industry.py",       "_m_di1")
        ARTICLE = load_module(REPO_ROOT / "platform/2_structure/article/article_deep_industry.py", "_m_di2")
        RENDER  = load_module(REPO_ROOT / "platform/3_render/engines/text/render_deep_industry.py", "_m_di3")
        SCARD   = load_module(REPO_ROOT / "platform/4_adapt/scorecard/scorecard_deep_industry.py", "_m_di4")

        # S1
        req = RADAR.RadarDeepIndustryRequest(topic=topic, industry="行业", max_signals=5)
        res1 = RADAR.RadarDeepIndustry().run(req)
        brief = res1.brief
        print(f"[S1] brief_id={brief.get('brief_id','?')} sources={len(brief.get('sources',[]))}")

        # S2
        res2 = ARTICLE.ArticleDeepIndustry().run(brief)
        outline = res2.outline
        outline_dict = get_dict(outline)
        sec_list = outline_dict.get("sections", [])
        sec_names = [s.get("section_id","")[:20] for s in (sec_list if isinstance(sec_list, list) else [])]
        print(f"[S2] sections={sec_names}")

        # S3
        res3 = RENDER.RenderDeepIndustry().run(outline)
        article = res3.article
        article_dict = get_dict(article)
        # v1.3: 从雷达 brief 注入来源验证状态到 article metadata
        article_dict.setdefault("metadata", {})["source_verified_count"] = (
            brief.get("metadata", {}).get("source_verified_count", 0)
        )
        md = article_dict.get("markdown", "")
        print(f"[S3] word_count={article_dict.get('word_count','?')}")

        # S4
        res4 = SCARD.ScorecardDeepIndustry().run(article)
        sc_dict = get_dict(res4)
        total, dims, action = extract_score(sc_dict)
        print(f"[S4] score={total:.1f}/100 action={action}")
        print(f"     factual={dims.get('factual')} source={dims.get('source')} "
              f"readability={dims.get('readability')} depth={dims.get('depth')}")

    # Save Markdown
    out_dir = REPO_ROOT / f"platform/5_deliver/results/delivered/{ct_label}"
    slug = topic[:15].replace("/", "_").replace("\\", "_")
    fm = f'---\ntitle: "{topic}"\ncontent_type: {ct_label}\nscore: {total}\naction: {action}\n---\n\n'
    save_md(out_dir / f"{ct_label}_{slug}_{total:.0f}.md", fm, md)
    print(f"[OUTPUT] {out_dir}")

    return {"type": ct_label, "score": total, "action": action,
            "topic": topic, "markdown_len": len(md)}


if __name__ == "__main__":
    results = []
    results.append(run_pipeline("量子计算突破：Google Willow芯片的科学意义", "science_research"))
    results.append(run_pipeline("2026年中国新能源汽车行业深度分析", "deep_industry_report"))

    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print("=" * 60)
    for r in results:
        print(f"  {r['type']:25s} score={r['score']:.1f}/100 action={r['action']:8s} {r['topic'][:35]}")
    print("\nALL DONE")
