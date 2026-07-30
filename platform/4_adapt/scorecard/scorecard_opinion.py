# -*- coding: utf-8 -*-
"""
scorecard_opinion.py — oped_argument IF-P-4：观点评论质量评分卡
=============================================================

功能：
  1. 对观点评论文章进行五维质量评分
  2. 维度：logic / factual / source / readability / brand
  3. 一票否决：factual < 65 或 logic < 50 → FAIL
  4. 引用检查：A/B级来源占比 ≥ 40%

评分权重（oped_argument）：
  logic:       30% — 逻辑严密性（论点链完整，反驳有力，无逻辑漏洞）
  factual:     25% — 事实准确性（数据声明必须有来源，事实错误零容忍）
  source:      15% — 来源可靠性（A级政策/学术/B级媒体报道权重最高）
  readability: 20% — 可读性（文字流畅、有说服力、节奏感）
  brand:       10% — 品牌规范（语气坚定但不傲慢，符合 assertiveness 标准）

阈值：总分 ≥ 80 → deliver；70-80 → revise；< 70 → reject

使用方式：
  scorecard = ScorecardOpinion()
  result = scorecard.run(render_result)
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
LLM_GATEWAY_PATH = REPO_ROOT / "platform" / "shared" / "llm_gateway.py"


def _load_llm_gateway():
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


# ─────────────────────────────────────────────────────────────────
# 评分维度权重（与 content_type_registry.yaml 一致）
# ─────────────────────────────────────────────────────────────────

WEIGHTS = {
    "logic":       0.30,
    "factual":     0.25,
    "source":      0.15,
    "readability": 0.20,
    "brand":       0.10,
}

# 一票否决阈值
FACTUAL_THRESHOLD = 65.0    # factual < 65 → FAIL
LOGIC_THRESHOLD = 50.0      # logic < 50 → FAIL（逻辑松散的评论危害最大）
QUALIFYING_SOURCE_RATIO = 0.40  # A/B级来源占比 ≥ 40%


@dataclass
class ScorecardOpinionResult:
    """评分卡结果"""
    scorecard: dict
    passed: bool
    action: str   # "deliver" / "revise" / "reject"
    gray_zones: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scorecard": self.scorecard,
            "passed": self.passed,
            "action": self.action,
            "gray_zones": self.gray_zones,
        }


# ─────────────────────────────────────────────────────────────────
# 核心类
# ─────────────────────────────────────────────────────────────────

class ScorecardOpinion:
    """观点评论质量评分卡"""

    def run(self, render_result) -> ScorecardOpinionResult:
        """
        执行评分
        流程：
          1. 提取得分数据（markdown + citations + tone_check）
          2. 五维评分（Mock 或 LLM）
          3. 一票否决检查
          4. 来源质量检查
          5. 汇总总分和 action
        """
        # 提取数据
        if hasattr(render_result, "to_dict"):
            data = render_result.to_dict()
        else:
            data = render_result

        markdown = data.get("markdown", "")
        citations = data.get("citations", [])
        tone_check = data.get("tone_check", {})
        word_count = data.get("word_count", 0)
        sections_summary = data.get("sections_summary", {})

        gray_zones = []

        # Mock 评分（无 API key 时）
        if not _has_llm_key():
            scores = self._score_mock(markdown, citations, tone_check, word_count, sections_summary)
        else:
            scores = self._score_llm(markdown, citations, tone_check, word_count, sections_summary)

        # 计算总分
        total_score = self._compute_weighted_score(scores)

        # 一票否决检查
        if scores["factual"] < FACTUAL_THRESHOLD:
            gray_zones.append(f"事实分 {scores['factual']:.1f} < 阈值 {FACTUAL_THRESHOLD}，一票否决")
            scores["_veto_reason"] = "factual"
        elif scores["logic"] < LOGIC_THRESHOLD:
            gray_zones.append(f"逻辑分 {scores['logic']:.1f} < 阈值 {LOGIC_THRESHOLD}，一票否决")
            scores["_veto_reason"] = "logic"

        # 来源质量检查
        source_ratio = self._check_source_ratio(citations)
        if source_ratio < QUALIFYING_SOURCE_RATIO:
            gray_zones.append(f"A/B级来源占比 {source_ratio:.0%} < {QUALIFYING_SOURCE_RATIO:.0%}，建议补充高质量来源")

        # 动作判定
        if scores.get("_veto_reason"):
            action = "reject"
            passed = False
        elif total_score >= 80:
            action = "deliver"
            passed = True
        elif total_score >= 70:
            action = "revise"
            passed = False
        else:
            action = "reject"
            passed = False

        scorecard = {
            "total_score": round(total_score, 1),
            "dimensions": {
                "logic": round(scores.get("logic", 0), 1),
                "factual": round(scores.get("factual", 0), 1),
                "source": round(scores.get("source", 0), 1),
                "readability": round(scores.get("readability", 0), 1),
                "brand": round(scores.get("brand", 0), 1),
            },
            "weights": WEIGHTS,
            "thresholds": {
                "factual_veto": FACTUAL_THRESHOLD,
                "logic_veto": LOGIC_THRESHOLD,
                "qualifying_source_ratio": QUALIFYING_SOURCE_RATIO,
                "deliver": 80,
                "revise": 70,
            },
            "source_ratio": round(source_ratio, 2),
            "veto_reason": scores.get("_veto_reason", None),
            "word_count": word_count,
        }

        return ScorecardOpinionResult(
            scorecard=scorecard,
            passed=passed,
            action=action,
            gray_zones=gray_zones,
        )

    # ──────────────────────────── 评分方法 ────────────────────────────

    def _score_mock(
        self, markdown: str, citations: list, tone_check: dict,
        word_count: int, sections_summary: dict
    ) -> dict:
        """Mock 五维评分（基于规则）"""
        scores = {}

        # 1. Logic（逻辑）：检查七段式结构完整性和反驳充分性
        section_keys = ["hook", "thesis", "support", "opposing", "refutation", "conclusion", "cta"]
        present_sections = [k for k in section_keys if k in markdown]
        structure_score = len(present_sections) / len(section_keys) * 60

        # 检查反驳是否充分（refutation 节长度）
        refutation_len = sections_summary.get("§5 反驳（Refutation）", 0) or 0
        if isinstance(refutation_len, int):
            pass  # 已是字数整数
        else:
            refutation_len = len(str(refutation_len))  # 兜底
        rebuttal_score = min(refutation_len / 150 * 40, 40)  # 150字满分

        scores["logic"] = min(structure_score + rebuttal_score, 100)

        # 2. Factual（事实）：检查数据引用和来源标注
        data_mentions = len(re.findall(r'\d+[年月日亿元万美元%个百分点]', markdown))
        has_citations = len(citations) > 0
        factual_base = 50
        if data_mentions > 0:
            factual_base += min(data_mentions * 5, 20)
        if has_citations:
            factual_base += 15
        if tone_check.get("violations"):
            factual_base -= 10
        scores["factual"] = min(max(factual_base, 0), 100)

        # 3. Source（来源）：A/B级来源占比
        grade_a_b = sum(1 for c in citations if c.startswith("【A】") or c.startswith("【B】"))
        ratio = grade_a_b / max(len(citations), 1)
        scores["source"] = ratio * 80 + 20  # 占比映射到 20-100

        # 4. Readability（可读性）：字数合理 + 无长段落 + 无乱码
        if 1200 <= word_count <= 2200:
            wc_score = 70
        elif word_count < 800:
            wc_score = 40
        else:
            wc_score = 55

        paragraph_count = markdown.count("\n\n")
        para_score = min(paragraph_count / 5 * 30, 30)  # 5段以上满分

        scores["readability"] = min(wc_score + para_score, 100)

        # 5. Brand（品牌）：语气检查通过 + 无绝对化表达
        if tone_check.get("passed", False):
            brand_score = 80
        else:
            violations = len(tone_check.get("violations", []))
            brand_score = max(80 - violations * 15, 40)
        scores["brand"] = brand_score

        return scores

    def _score_llm(
        self, markdown: str, citations: list, tone_check: dict,
        word_count: int, sections_summary: dict
    ) -> dict:
        """LLM 五维评分"""
        llm = _load_llm_gateway()

        citation_str = "\n".join(citations) or "无引用"
        tone_passed = "通过" if tone_check.get("passed") else f"失败，原因：{tone_check.get('violations')}"

        prompt = (
            f"请对以下观点评论文章进行五维质量评分（满分100分）。\n\n"
            f"评分维度：\n"
            f"1. logic（30%）：论点链完整，反驳有力，无逻辑漏洞\n"
            f"2. factual（25%）：数据声明有来源，事实错误零容忍\n"
            f"3. source（15%）：A/B级来源占比 ≥ 40%\n"
            f"4. readability（20%）：文字流畅、有说服力、节奏感\n"
            f"5. brand（10%）：语气坚定但不傲慢，符合assertiveness标准\n\n"
            f"文章字数：{word_count}\n"
            f"引用来源：{citation_str}\n"
            f"语气检查：{tone_passed}\n\n"
            f"文章内容（摘要）：\n{markdown[:3000]}\n\n"
            f"请输出JSON：{{\"logic\":分数, \"factual\":分数, \"source\":分数, "
            f"\"readability\":分数, \"brand\":分数, \"reasoning\":\"简要理由\"}}"
        )

        try:
            response = llm.call_deepseek(prompt, model="deepseek-chat")
            import json
            data = json.loads(response)
            scores = {k: float(v) for k, v in data.items() if k != "reasoning"}
            scores["reasoning"] = data.get("reasoning", "")
            return scores
        except Exception:
            return self._score_mock(markdown, citations, tone_check, word_count, sections_summary)

    def _compute_weighted_score(self, scores: dict) -> float:
        """计算加权总分"""
        total = 0.0
        for dim, weight in WEIGHTS.items():
            total += scores.get(dim, 0) * weight
        return round(total, 1)

    def _check_source_ratio(self, citations: list) -> float:
        """计算 A/B 级来源占比"""
        if not citations:
            return 0.0
        grade_a_b = sum(1 for c in citations if c.startswith("【A】") or c.startswith("【B】"))
        return grade_a_b / len(citations)


# ─────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────

def _has_llm_key() -> bool:
    import os
    return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())


# ─────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────

def run(render_result, **kwargs) -> ScorecardOpinionResult:
    """
    便捷入口：scorecard_opinion.run(render_result)
    等价于 ScorecardOpinion().run(render_result)
    """
    return ScorecardOpinion().run(render_result)
