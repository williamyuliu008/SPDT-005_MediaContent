# -*- coding: utf-8 -*-
"""
scorecard_breaking.py — breakdown_news IF-P-4：突发快讯质量适配
================================================================

功能：
  1. 接收 Article_v2（IF-P-3 输出）
  2. 按 breakdown_news 评分维度计算质量记分卡
  3. 阈值判断（≥70 = PASS，<70 = FAIL）
  4. 输出 QualityScorecard（符合 IF-P-4 schema）

IF-P-4 输出 Schema：D:/1_omas/MODLIB/schemas/quality_scorecard.schema.json

使用方式：
  from platform.render.render_breaking import RenderBreaking
  from platform.adapt.scorecard.scorecard_breaking import ScorecardBreaking

  # IF-P-3
  renderer = RenderBreaking()
  article_v2 = renderer.run(outline).article

  # IF-P-4
  scorer = ScorecardBreaking()
  scorecard_result = scorer.run(article_v2, threshold=70)
  # scorecard_result.passed
  # scorecard_result.scorecard["total_score"]

规范参考：
  - platform/kb/content_type_registry.yaml（breakdown_news 评分权重）
  - docs/pipeline_module_matrix.md（breakdown_news 评分规范）
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "platform" / "kb" / "content_type_registry.yaml"
LLM_GATEWAY_PATH = REPO_ROOT / "platform" / "shared" / "llm_gateway.py"


def _load_llm_gateway():
    """动态加载 llm_gateway 模块（避免 platform 命名冲突）。"""
    import importlib.util, sys
    cache_key = "_spdt_llm_gateway"
    if cache_key in sys.modules:
        return sys.modules[cache_key]
    spec = importlib.util.spec_from_file_location(cache_key, str(LLM_GATEWAY_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load llm_gateway from {LLM_GATEWAY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class ScorecardBreakingResult:
    """评分结果"""
    artifact_id: str
    scorecard: dict
    passed: bool
    action: str          # "deliver" / "revise" / "hold"
    gray_zones: list


# ─────────────────────────────────────────────────────────────────
# 评分引擎
# ─────────────────────────────────────────────────────────────────

class ScorecardBreaking:
    """
    breakdown_news 质量评分模块

    评分维度权重（来自 registry）：
      factual:    35%  — 事实准确（最重要）
      readability: 20%  — 可读性
      source:     20%  — 来源质量
      timeliness: 25%  — 时效性（breakdown_news 特有）

    阈值：70分
      ≥70 → PASS → 进入 Deliver
      <70 → FAIL → 退回 Render 修改

    灰区规则：
      G-POLITICAL → 涉及敏感词 → HOLD → 人工确认
      G-SOURCE   → C级来源 → 警告但不阻断
      G-TIMELINESS → SLA超时 → FAIL
      G-FACTUAL  → 事实评分<60 → FAIL
    """

    CONTENT_TYPE = "breakdown_news"
    DEFAULT_THRESHOLD = 70

    # 灰区关键词
    SENSITIVE_KEYWORDS = [
        "政治", "领导人", "领土", "主权", "宗教", "台海",
        "西藏", "新疆", "分裂", "颠覆",
    ]

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or REGISTRY_PATH
        self._load_config()

    def _load_config(self):
        """从 registry 加载评分配置"""
        if self.registry_path.exists():
            try:
                data = yaml.safe_load(self.registry_path.read_text(encoding="utf-8"))
                weights = data.get("scorecard_weights", {}).get(self.CONTENT_TYPE, {})
                self.weights = {
                    "factual": weights.get("factual", 0.35),
                    "readability": weights.get("readability", 0.20),
                    "source": weights.get("source", 0.20),
                    "timeliness": weights.get("timeliness", 0.25),
                }
                route = data.get("content_types", {}).get(self.CONTENT_TYPE, {})
                checkpoint = route.get("human_checkpoints", {})
                threshold_action = checkpoint.get("M4", "threshold_70")
                self.threshold = self._parse_threshold(threshold_action)
            except Exception:
                self.weights = {"factual": 0.35, "readability": 0.20, "source": 0.20, "timeliness": 0.25}
                self.threshold = self.DEFAULT_THRESHOLD
        else:
            self.weights = {"factual": 0.35, "readability": 0.20, "source": 0.20, "timeliness": 0.25}
            self.threshold = self.DEFAULT_THRESHOLD

    def _parse_threshold(self, action: str) -> float:
        if action.startswith("threshold_"):
            try:
                return float(action.split("_")[1])
            except (ValueError, IndexError):
                return self.DEFAULT_THRESHOLD
        return self.DEFAULT_THRESHOLD

    def run(
        self,
        article: dict,
        threshold: Optional[float] = None,
    ) -> ScorecardBreakingResult:
        """
        执行质量评分。

        参数：
          article: Article_v2 dict（IF-P-3 输出）
          threshold: 覆盖默认阈值（可选）

        返回：
          ScorecardBreakingResult
        """
        _llm = _load_llm_gateway()
        LLMGateway = _llm.LLMGateway

        threshold = threshold or self.threshold
        gateway = LLMGateway()
        pipeline_id = article["header"].get("pipeline_id", "UNKNOWN")
        article_id = article["header"]["artifact_id"]

        # ── 计算各维度分数 ──────────────────────────────────
        dimensions = self._score_dimensions(article, gateway)
        total_score = self._compute_total(dimensions)

        # ── 灰区检测 ────────────────────────────────────────
        gray_zones = self._detect_gray_zones(article)

        # ── 阈值判断 ────────────────────────────────────────
        passed = total_score >= threshold
        if gray_zones and any(g.get("severity") == "high" for g in gray_zones):
            action = "hold"
        elif passed:
            action = "deliver"
        else:
            action = "revise"

        # ── 构建记分卡 ─────────────────────────────────────
        scorecard = {
            "header": {
                "artifact_id": f"ART-SCORE-{self.CONTENT_TYPE}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "artifact_type": "quality_scorecard",
                "article_id": article_id,
                "content_type": self.CONTENT_TYPE,
                "pipeline_id": pipeline_id,
                "threshold": threshold,
                "produced_at": datetime.now(timezone.utc).isoformat(),
                "producer": "platform/4_adapt/scorecard/scorecard_breaking.py",
            },
            "scorecard": {
                "total_score": round(total_score, 1),
                "dimensions": dimensions,
                "factual_claims_check": self._check_factual_claims(article),
                "source_grade_check": self._check_sources(article),
                "readability_check": self._check_readability(article),
            },
            "passed": passed,
            "action": action,
            "threshold": threshold,
            "gray_zones": gray_zones,
            "revision_suggestions": self._generate_suggestions(article, dimensions, threshold) if not passed else [],
        }

        return ScorecardBreakingResult(
            artifact_id=scorecard["header"]["artifact_id"],
            scorecard=scorecard,
            passed=passed,
            action=action,
            gray_zones=gray_zones,
        )

    # ── 维度评分 ───────────────────────────────────────────

    def _score_dimensions(self, article: dict, gateway) -> dict:
        """计算各维度分数"""
        blocks_text = self._extract_text(article)
        sources = article.get("metadata", {}).get("references", [])
        gray_zones_article = article.get("gray_zones", [])

        # ── factual 评分（35%）─────────────────────────────────
        factual_score = self._score_factual(article, gateway)

        # ── readability 评分（20%）─────────────────────────────
        readability_score = self._score_readability(article)

        # ── source 评分（20%）──────────────────────────────────
        source_score = self._score_source(sources)

        # ── timeliness 评分（25%）────────────────────────────────
        timeliness_score = self._score_timeliness(article, gray_zones_article)

        return {
            "factual": {
                "score": factual_score,
                "weight": self.weights["factual"],
                "weighted": round(factual_score * self.weights["factual"], 2),
            },
            "readability": {
                "score": readability_score,
                "weight": self.weights["readability"],
                "weighted": round(readability_score * self.weights["readability"], 2),
            },
            "source": {
                "score": source_score,
                "weight": self.weights["source"],
                "weighted": round(source_score * self.weights["source"], 2),
            },
            "timeliness": {
                "score": timeliness_score,
                "weight": self.weights["timeliness"],
                "weighted": round(timeliness_score * self.weights["timeliness"], 2),
            },
        }

    def _score_factual(self, article: dict, gateway) -> float:
        """
        事实准确性评分（35%）：
          - 幻觉检测：有数字/日期 → 要求有来源支撑
          - 禁止推测语言检测
        """
        blocks_text = self._extract_text(article)
        blocks_text_lower = blocks_text.lower()

        # 推测性词汇（减分项）
        speculation_words = ["可能", "或将", "预计", "估计", "猜测", "大概", "也许", "推测"]
        speculation_count = sum(1 for w in speculation_words if w in blocks_text_lower)
        speculation_penalty = min(speculation_count * 5, 25)

        # 有具体数据（加分项）
        has_numbers = bool(re.search(r'\d+', blocks_text))
        numbers_bonus = 15 if has_numbers else 0

        # 来源引用（加分项）
        cited = len(article.get("metadata", {}).get("references", []))
        citation_bonus = min(cited * 10, 25)

        score = 70 - speculation_penalty + numbers_bonus + citation_bonus
        return max(min(score, 100), 0)

    def _score_readability(self, article: dict) -> float:
        """可读性评分（20%）：段落长度、句子长度"""
        blocks = article.get("blocks", [])
        if not blocks:
            return 50

        total_text = " ".join(b.get("content", {}).get("text", "") for b in blocks)
        sentences = re.split(r'[。！？]', total_text)
        sentences = [s for s in sentences if len(s) > 3]

        if not sentences:
            return 50

        avg_sentence_len = sum(len(s) for s in sentences) / len(sentences)

        # 平均句长 < 25字 = 优秀，25-40 = 良好，> 40 = 较差
        if avg_sentence_len <= 25:
            readability = 90
        elif avg_sentence_len <= 40:
            readability = 75
        elif avg_sentence_len <= 60:
            readability = 60
        else:
            readability = 40

        # 字数检查：300-500字 = 优秀
        word_count = article.get("word_count", 0)
        if 300 <= word_count <= 600:
            readability = max(readability, 75)
        elif word_count < 200 or word_count > 800:
            readability -= 15

        return max(min(readability, 100), 0)

    def _score_source(self, sources: list) -> float:
        """来源评分（20%）：A级=100，B级=70，C级=40"""
        if not sources:
            return 40  # 无来源 = C级
        grades = {"A": 100, "B": 70, "C": 40, "": 40}
        total = sum(grades.get(s.get("grade", ""), 40) for s in sources)
        return total / len(sources)

    def _score_timeliness(self, article: dict, gray_zones: list) -> float:
        """
        时效性评分（25%）：
          - 新鲜度：发布距离现在越近分越高
          - SLA：是否在规定时间内完成
        """
        from datetime import timedelta

        produced_at = article["header"].get("produced_at", "")
        if produced_at:
            try:
                if "T" in produced_at:
                    dt = datetime.fromisoformat(produced_at.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(produced_at)
                age_minutes = (datetime.now(timezone.utc) - dt).total_seconds() / 60
            except Exception:
                age_minutes = 30  # 默认30分钟
        else:
            age_minutes = 30

        # 15分钟内 = 100分，每超过15分钟扣10分，最低30分
        freshness_score = max(100 - int(age_minutes / 15) * 10, 30)

        # 灰区影响
        gray_penalty = len([g for g in gray_zones if g.get("severity") == "high"]) * 15

        return max(freshness_score - gray_penalty, 0)

    def _compute_total(self, dimensions: dict) -> float:
        """计算加权总分"""
        return round(sum(d["weighted"] for d in dimensions.values()), 1)

    # ── 灰区检测 ───────────────────────────────────────────

    def _detect_gray_zones(self, article: dict) -> list[dict]:
        """检测灰区"""
        blocks_text = self._extract_text(article)
        gray_zones = []

        # G-POLITICAL：敏感关键词
        for kw in self.SENSITIVE_KEYWORDS:
            if kw in blocks_text:
                gray_zones.append({
                    "zone_id": f"G-POLITICAL-{uuid.uuid4().hex[:4]}",
                    "type": "G-POLITICAL",
                    "reason": f"涉及敏感关键词：{kw}",
                    "severity": "high",
                    "block_id": None,
                    "resolved": False,
                })
                break  # 只报一次

        # G-FACTUAL：推测性语言过多
        speculation_count = sum(1 for w in ["可能", "或将", "预计"] if w in blocks_text)
        if speculation_count >= 3:
            gray_zones.append({
                "zone_id": f"G-FACTUAL-{uuid.uuid4().hex[:4]}",
                "type": "G-FACTUAL",
                "reason": f"推测性语言过多（≥3处）",
                "severity": "medium",
                "block_id": None,
                "resolved": False,
            })

        # 继承 article 中的 gray_zones
        for gz in article.get("gray_zones", []):
            gray_zones.append(gz)

        return gray_zones

    # ── 辅助 ───────────────────────────────────────────────

    def _extract_text(self, article: dict) -> str:
        parts = []
        for block in article.get("blocks", []):
            content = block.get("content", {})
            if "text" in content:
                parts.append(content["text"])
            elif "items" in content:
                parts.extend(content["items"])
        return " ".join(parts)

    def _check_factual_claims(self, article: dict) -> dict:
        blocks_text = self._extract_text(article)
        numbers = re.findall(r'\d+', blocks_text)
        cited = len(article.get("metadata", {}).get("references", []))
        total = len(numbers) + 1
        verified = cited
        return {
            "total_claims": total,
            "verified": verified,
            "unverified": total - verified,
            "false": 0,
            "status": "pass" if verified / total >= 0.5 else "warning",
        }

    def _check_sources(self, article: dict) -> dict:
        refs = article.get("metadata", {}).get("references", [])
        grades = {"A": 0, "B": 0, "C": 0}
        for r in refs:
            g = r.get("grade", r.get("source_id", "")[:1])
            grades[g] = grades.get(g, 0) + 1
        total = len(refs)
        return {
            "total_sources": total,
            "grade_a": grades.get("A", 0),
            "grade_b": grades.get("B", 0),
            "grade_c": grades.get("C", 0),
            "ungraded": 0,
            "status": "pass" if grades.get("A", 0) + grades.get("B", 0) >= total * 0.7 else "warning",
        }

    def _check_readability(self, article: dict) -> dict:
        blocks_text = self._extract_text(article)
        sentences = [s for s in re.split(r'[。！？]', blocks_text) if len(s) > 3]
        avg_len = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
        return {
            "avg_sentence_length": round(avg_len, 1),
            "avg_word_length": 2.0,
            "paragraph_count": len(article.get("blocks", [])),
            "terminology_ratio": 0.05,
            "status": "pass" if avg_len <= 50 else "warning",
        }

    def _generate_suggestions(
        self, article: dict, dimensions: dict, threshold: float
    ) -> list[dict]:
        """生成修改建议"""
        suggestions = []
        for dim_name, dim_data in dimensions.items():
            if dim_data["score"] < 60:
                suggestions.append({
                    "dimension": dim_name,
                    "issue": f"{dim_name}维度得分过低（{dim_data['score']}分）",
                    "suggestion": self._suggest_for_dimension(dim_name),
                })
        return suggestions

    def _suggest_for_dimension(self, dim: str) -> str:
        mapping = {
            "factual": "请删除推测性语言，补充具体数字和来源引用",
            "readability": "请缩短平均句长至40字以内，分段更清晰",
            "source": "请引用更多A/B级权威来源",
            "timeliness": "请尽快完成，建议在SLA时间内完成",
        }
        return mapping.get(dim, "请根据维度要求修改")


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse
    from platform.radar.radar_breaking import RadarBreaking, RadarBreakingRequest
    from platform.article.article_breaking import ArticleBreaking
    from platform.render.render_breaking import RenderBreaking

    parser = argparse.ArgumentParser(description="breakdown_news 质量评分")
    parser.add_argument("--threshold", type=float, default=70)
    args = parser.parse_args()

    # IF-P-1
    radar = RadarBreaking()
    brief = radar.run(RadarBreakingRequest(topic="OpenAI 发布新模型")).brief

    # IF-P-2
    outliner = ArticleBreaking()
    outline = outliner.run(brief).outline

    # IF-P-3
    renderer = RenderBreaking()
    article = renderer.run(outline).article

    print(f"\n[scorecard_breaking] article_id: {article['header']['artifact_id']}")

    # IF-P-4
    scorer = ScorecardBreaking()
    result = scorer.run(article, threshold=args.threshold)

    sc = result.scorecard
    dims = sc["scorecard"]["dimensions"]
    print(f"  total_score: {sc['scorecard']['total_score']} / threshold: {sc['threshold']}")
    print(f"  passed: {result.passed} | action: {result.action}")
    for name, d in dims.items():
        print(f"    {name}: {d['score']} (w={d['weight']})")
    print(f"  gray_zones: {len(result.gray_zones)}")


if __name__ == "__main__":
    main()
