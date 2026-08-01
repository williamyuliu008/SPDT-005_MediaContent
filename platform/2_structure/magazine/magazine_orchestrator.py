# -*- coding: utf-8 -*-
"""
magazine_orchestrator.py — 科学杂志管线编排器
==============================================

功能：
  1. 接收 MagazineBlueprint，编排 3 条管线并行执行
  2. 按角色门禁质量评分（每角色不同阈值）
  3. 汇总 policy_audit.jsonl 条目
  4. 输出 MagazineRunResult

使用方式：
  orchestrator = MagazineOrchestrator()
  result = orchestrator.run(blueprint)
  if result.all_passed:
      artifact = MagazineAssembler().assemble(result, fmt="docx")
"""

from __future__ import annotations

import json
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]  # → SPDT-005_MediaContent


def _load_llm_gateway():
    import importlib.util, sys
    cache_key = "_spdt_magazine_llm"
    if cache_key in sys.modules:
        return sys.modules[cache_key]
    spec = importlib.util.spec_from_file_location(
        cache_key,
        str(REPO_ROOT / "platform" / "shared" / "llm_gateway.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load llm_gateway")
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module


# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

@dataclass
class ArticleRunResult:
    """单篇文章运行结果"""
    article_role: str
    pipeline_type: str
    topic: str
    brief: dict
    outline: dict
    article: dict
    scorecard: dict
    action: str
    total_score: float
    passed: bool
    gray_zones: list
    policy_audit_entry: dict
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "article_role": self.article_role,
            "pipeline_type": self.pipeline_type,
            "topic": self.topic,
            "total_score": self.total_score,
            "action": self.action,
            "passed": self.passed,
            "gray_zones": self.gray_zones,
            "error": self.error,
        }


@dataclass
class MagazineRunResult:
    """杂志运行结果（Orchestrator 输出）"""
    blueprint_id: str
    spec: dict
    articles: dict          # role → ArticleRunResult
    policy_audit_entries: list[dict]
    all_passed: bool
    run_at: str = ""
    run_id: str = ""

    def __post_init__(self):
        if not self.run_at:
            self.run_at = datetime.now(timezone.utc).isoformat()
        if not self.run_id:
            self.run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

    def get_passed_count(self) -> int:
        return sum(1 for a in self.articles.values() if a.passed)

    def get_failed_count(self) -> int:
        return sum(1 for a in self.articles.values() if not a.passed)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "blueprint_id": self.blueprint_id,
            "run_at": self.run_at,
            "all_passed": self.all_passed,
            "spec": self.spec,
            "articles": {
                role: art.to_dict() for role, art in self.articles.items()
            },
            "audit_count": len(self.policy_audit_entries),
        }


# ─────────────────────────────────────────────────────────────────
# 管线执行器（单篇文章）
# ─────────────────────────────────────────────────────────────────

class _PipelineExecutor:
    """在独立线程中执行单条管线的 Runnable"""

    ROLE_MIN_SCORES = {
        "cover_story": 80,
        "explain":      75,
        "industry":     80,
        "news_brief":   70,
        "oped":         80,
    }

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = _load_llm_gateway().LLMGateway()
        return self._llm

    def execute(self, spec: "ArticleSpec") -> ArticleRunResult:
        """执行单条管线，返回 ArticleRunResult"""
        import importlib.util, sys

        role = spec.article_role
        pipeline_type = spec.pipeline_type
        constraints = spec.constraints
        topic = spec.topic

        run_ts = str(int(datetime.now().timestamp() * 1000))
        _audit_entry = {
            "run_id": run_ts,
            "article_role": role,
            "pipeline_type": pipeline_type,
            "topic": topic,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            if pipeline_type == "science_research":
                return self._run_science_research(run_ts, role, topic, constraints, _audit_entry)
            elif pipeline_type == "deep_industry_report":
                return self._run_deep_industry(run_ts, role, topic, constraints, _audit_entry)
            elif pipeline_type == "oped_argument":
                return self._run_oped(run_ts, role, topic, constraints, _audit_entry)
            else:
                return ArticleRunResult(
                    article_role=role, pipeline_type=pipeline_type, topic=topic,
                    brief={}, outline={}, article={}, scorecard={},
                    action="reject", total_score=0, passed=False,
                    gray_zones=[f"Unknown pipeline_type: {pipeline_type}"],
                    policy_audit_entry=_audit_entry,
                    error=f"Unknown pipeline: {pipeline_type}",
                )
        except Exception as e:
            return ArticleRunResult(
                article_role=role, pipeline_type=pipeline_type, topic=topic,
                brief={}, outline={}, article={}, scorecard={},
                action="reject", total_score=0, passed=False,
                gray_zones=[f"Pipeline execution error: {str(e)}"],
                policy_audit_entry=_audit_entry,
                error=str(e),
            )

    def _get_dict(self, obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dataclass_fields__"):
            from dataclasses import asdict
            return asdict(obj)
        return dict(obj) if obj else {}

    def _load_mod(self, key: str, path: Path):
        """Load a module by path. Uses stable key so Python's import system caches properly."""
        import importlib.util, sys
        cache_key = f"_spdt_mag_{key}"
        if cache_key in sys.modules:
            return sys.modules[cache_key]
        spec = importlib.util.spec_from_file_location(cache_key, str(path))
        m = importlib.util.module_from_spec(spec)
        sys.modules[cache_key] = m
        spec.loader.exec_module(m)
        return m

    def _extract_score(self, sc_dict: dict) -> tuple[float, dict, str]:
        sc = sc_dict.get("scorecard", sc_dict)
        inner = sc.get("scorecard", {}) if isinstance(sc, dict) else {}
        total = inner.get("total_score", sc.get("total_score", 0)) if isinstance(sc, dict) else 0
        dims = inner.get("dimensions", sc.get("dimensions", {})) if isinstance(sc, dict) else {}
        action = sc_dict.get("action", "?")
        return total, dims, action

    def _run_science_research(self, run_ts: str, role: str,
                              topic: str, constraints: dict,
                              audit: dict) -> ArticleRunResult:
        RADAR   = self._load_mod("sr1", REPO_ROOT / "platform/1_ingest/radar/radar_science_fact.py")
        ARTICLE = self._load_mod("sr2", REPO_ROOT / "platform/2_structure/article/article_science_fact.py")
        RENDER  = self._load_mod("sr3", REPO_ROOT / "platform/3_render/engines/text/render_science_fact.py")
        SCARD   = self._load_mod("sr4", REPO_ROOT / "platform/4_adapt/scorecard/scorecard_science_fact.py")

        # S1 — 只传递 RadarScienceFactRequest 接受的字段（其他字段由调用方通过 blueprint spec 传递）
        req = RADAR.RadarScienceFactRequest(
            topic=topic,
            channels=[],
            max_signals=constraints.get("max_signals", 5),
            min_confidence=0.5,
            research_type=None,
        )
        res1 = RADAR.RadarScienceFact().run(req)
        brief = self._get_dict(res1)
        if isinstance(res1, object) and hasattr(res1, "brief"):
            brief = self._get_dict(res1.brief)
        elif isinstance(res1, dict) and "brief" in res1:
            brief = res1["brief"]

        # S2
        res2 = ARTICLE.ArticleScienceFact().run(brief)
        outline = self._get_dict(res2)
        if isinstance(res2, object) and hasattr(res2, "outline"):
            outline = self._get_dict(res2.outline)
        elif isinstance(res2, dict) and "outline" in res2:
            outline = res2["outline"]
        if "outline" in outline and isinstance(outline["outline"], dict):
            outline = outline["outline"]

        # S3
        res3 = RENDER.RenderScienceFact().run(outline)
        article = self._get_dict(res3)
        if isinstance(res3, object) and hasattr(res3, "article"):
            article = self._get_dict(res3.article)

        # S4
        res4 = SCARD.ScorecardScienceFact().run(article if isinstance(article, dict) else {"markdown": article.get("markdown", ""), "header": article.get("header", {}), "blocks": article.get("blocks", [])})
        score_dict = self._get_dict(res4)
        total, dims, action = self._extract_score(score_dict)
        passed = total >= self.ROLE_MIN_SCORES.get(role, 75)

        audit.update({"stage": "science_research", "score": total, "action": action})

        return ArticleRunResult(
            article_role=role, pipeline_type="science_research",
            topic=topic, brief=brief, outline=outline, article=article,
            scorecard={"total_score": total, "dimensions": dims},
            action=action, total_score=total, passed=passed,
            gray_zones=score_dict.get("gray_zones", []),
            policy_audit_entry=audit,
        )

    def _run_deep_industry(self, run_ts: str, role: str,
                            topic: str, constraints: dict,
                            audit: dict) -> ArticleRunResult:
        RADAR   = self._load_mod("di1", REPO_ROOT / "platform/1_ingest/radar/radar_deep_industry.py")
        ARTICLE = self._load_mod("di2", REPO_ROOT / "platform/2_structure/article/article_deep_industry.py")
        RENDER  = self._load_mod("di3", REPO_ROOT / "platform/3_render/engines/text/render_deep_industry.py")
        SCARD   = self._load_mod("di4", REPO_ROOT / "platform/4_adapt/scorecard/scorecard_deep_industry.py")

        industry_name = constraints.get("industry", "行业")

        req = RADAR.RadarDeepIndustryRequest(
            topic=topic,
            industry=industry_name,
            max_signals=constraints.get("max_signals", 5),
            scope_years=3,
            priority="normal",
            custom_keywords=[],
        )
        res1 = RADAR.RadarDeepIndustry().run(req)
        brief = self._get_dict(res1)
        if isinstance(res1, object) and hasattr(res1, "brief"):
            brief = self._get_dict(res1.brief)
        elif isinstance(res1, dict) and "brief" in res1:
            brief = res1["brief"]

        res2 = ARTICLE.ArticleDeepIndustry().run(brief)
        outline = self._get_dict(res2)
        if isinstance(res2, object) and hasattr(res2, "outline"):
            outline = self._get_dict(res2.outline)
        elif isinstance(res2, dict) and "outline" in res2:
            outline = res2["outline"]
        if "outline" in outline and isinstance(outline["outline"], dict):
            outline = outline["outline"]

        res3 = RENDER.RenderDeepIndustry().run(outline)
        article = self._get_dict(res3)
        if isinstance(res3, object) and hasattr(res3, "article"):
            article = self._get_dict(res3.article)

        res4 = SCARD.ScorecardDeepIndustry().run(article if isinstance(article, dict) else {"markdown": article.get("markdown", ""), "header": article.get("header", {}), "blocks": article.get("blocks", [])})
        score_dict = self._get_dict(res4)
        total, dims, action = self._extract_score(score_dict)
        passed = total >= self.ROLE_MIN_SCORES.get(role, 80)

        audit.update({"stage": "deep_industry_report", "score": total, "action": action})

        return ArticleRunResult(
            article_role=role, pipeline_type="deep_industry_report",
            topic=topic, brief=brief, outline=outline, article=article,
            scorecard={"total_score": total, "dimensions": dims},
            action=action, total_score=total, passed=passed,
            gray_zones=score_dict.get("gray_zones", []),
            policy_audit_entry=audit,
        )

    def _run_oped(self, run_ts: str, role: str,
                   topic: str, constraints: dict,
                   audit: dict) -> ArticleRunResult:
        RADAR   = self._load_mod("op1", REPO_ROOT / "platform/1_ingest/radar/radar_opinion.py")
        ARTICLE = self._load_mod("op2", REPO_ROOT / "platform/2_structure/article/article_opinion.py")
        RENDER  = self._load_mod("op3", REPO_ROOT / "platform/3_render/engines/text/render_opinion.py")
        SCARD   = self._load_mod("op4", REPO_ROOT / "platform/4_adapt/scorecard/scorecard_opinion.py")

        req = RADAR.RadarOpinionRequest(
            topic=topic,
            perspective=constraints.get("perspective", "支持"),
            industry_focus=constraints.get("industry_focus", ""),
            max_signals=constraints.get("max_signals", 4),
            custom_keywords=[],
        )
        brief_obj = RADAR.RadarOpinion().run(req)
        brief = self._get_dict(brief_obj)
        if hasattr(brief_obj, "to_dict"):
            brief = brief_obj.to_dict()

        res2 = ARTICLE.ArticleOpinion().run(brief, title=topic)
        res2_d = self._get_dict(res2)

        res3 = RENDER.RenderOpinion().run(res2_d, brand_voice="assertive")

        res4 = SCARD.ScorecardOpinion().run(res3)

        brief_d = self._get_dict(brief)
        outline_d = self._get_dict(res2)
        article_d = self._get_dict(res3)
        score_d = self._get_dict(res4)

        sc = score_d.get("scorecard", score_d)
        dims = sc.get("dimensions", {}) if isinstance(sc, dict) else {}
        total = float(sc.get("total_score", 0)) if isinstance(sc, dict) else 0
        action = score_d.get("action", "?")
        passed = total >= self.ROLE_MIN_SCORES.get(role, 80)

        audit.update({"stage": "oped_argument", "score": total, "action": action})

        return ArticleRunResult(
            article_role=role, pipeline_type="oped_argument",
            topic=topic, brief=brief_d, outline=outline_d, article=article_d,
            scorecard={"total_score": total, "dimensions": dims},
            action=action, total_score=total, passed=passed,
            gray_zones=score_d.get("gray_zones", []),
            policy_audit_entry=audit,
        )


# ─────────────────────────────────────────────────────────────────
# MagazineOrchestrator
# ─────────────────────────────────────────────────────────────────

class MagazineOrchestrator:
    """
    杂志管线编排器。

    接收 MagazineBlueprint，并行执行各篇文章管线，
    汇总结果后输出 MagazineRunResult。
    """

    def __init__(self, max_workers: int = 5):
        self._executor = _PipelineExecutor()
        self._max_workers = max_workers

    def run(self, blueprint: "MagazineBlueprint") -> MagazineRunResult:
        """
        执行杂志蓝图中的所有管线。

        并行策略：
          - article_role = "news_brief" 需要 cover_story 的 signals 作为上下文，
            因此 cover_story 优先执行，news_brief 等待（串行依赖）
          - 其他文章之间完全并行
        """
        spec_dict = {
            "title": blueprint.spec.title,
            "domain_topic": blueprint.spec.domain_topic,
            "issue": blueprint.spec.issue,
            "audience": blueprint.spec.audience,
            "publication_date": blueprint.spec.publication_date,
        }

        # 分类：cover_story（先行）和其他
        cover_spec = blueprint.get_article("cover_story")
        other_specs = [a for a in blueprint.articles if a.article_role != "cover_story"]

        article_results: dict[str, ArticleRunResult] = {}
        audit_entries: list[dict] = []

        # Phase 1: cover_story 先执行（news_brief 依赖其信号）
        if cover_spec:
            result = self._executor.execute(cover_spec)
            article_results["cover_story"] = result
            audit_entries.append(result.policy_audit_entry)

        # Phase 2: 其余文章并行
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {
                pool.submit(self._executor.execute, spec): spec.article_role
                for spec in other_specs
            }
            for future in as_completed(futures):
                role = futures[future]
                try:
                    result = future.result()
                    article_results[role] = result
                    audit_entries.append(result.policy_audit_entry)
                except Exception as e:
                    spec = futures_to_spec = None
                    for spec in other_specs:
                        if spec.article_role == role:
                            break
                    article_results[role] = ArticleRunResult(
                        article_role=role,
                        pipeline_type=spec.pipeline_type if spec else "",
                        topic=spec.topic if spec else "",
                        brief={}, outline={}, article={}, scorecard={},
                        action="reject", total_score=0, passed=False,
                        gray_zones=[f"Thread execution error: {str(e)}"],
                        policy_audit_entry={"article_role": role, "error": str(e)},
                        error=str(e),
                    )

        all_passed = all(r.passed for r in article_results.values())

        result = MagazineRunResult(
            blueprint_id=blueprint.blueprint_id,
            spec=spec_dict,
            articles=article_results,
            policy_audit_entries=audit_entries,
            all_passed=all_passed,
        )

        # 追加 policy_audit.jsonl
        self._append_audit_log(result)

        return result

    def _append_audit_log(self, result: MagazineRunResult):
        """将 policy_audit 条目写入 JSONL 文件"""
        audit_dir = REPO_ROOT / "platform/5_deliver/checkpoint"
        audit_dir.mkdir(parents=True, exist_ok=True)
        log_path = audit_dir / "magazine_policy_audit.jsonl"
        entries = [json.dumps(e, ensure_ascii=False) for e in result.policy_audit_entries]
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n".join(entries) + "\n")
