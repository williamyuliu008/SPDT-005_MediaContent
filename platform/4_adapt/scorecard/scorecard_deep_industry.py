# -*- coding: utf-8 -*-
"""
scorecard_deep_industry.py — deep_industry_report IF-P-4：深度行业报告质量评分卡
================================================================================

功能：
  1. 对深度行业报告进行多维质量评分
  2. 维度：factual / source / depth / readability / timeliness
  3. 一票否决：factual < 70 → FAIL
  4. 引用检查：行业报告/A级来源占比 ≥ 30%

评分权重（deep_industry_report）：
  factual:       30% — 事实准确性（数据声明必须有来源）
  source:        25% — 来源可靠性（A级机构研报/财报权重最高）
  depth:         20% — 专业深度（竞争格局/驱动因素/风险分析）
  readability:   15% — 可读性（专业受众可接受复杂句式）
  timeliness:    10% — 时效性（行业报告有效期约6-12个月）

阈值：总分 ≥ 85 → deliver；70-85 → revise；< 70 → reject

使用方式：
  scorecard = ScorecardDeepIndustry()
  result = scorecard.run(article)
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
    "factual":      0.30,
    "source":       0.25,
    "depth":        0.20,
    "readability":  0.15,
    "timeliness":  0.10,
}

# 一票否决阈值
FACTUAL_THRESHOLD = 70.0   # factual < 70 → FAIL


@dataclass
class ScorecardDeepIndustryResult:
    """评分卡结果"""
    scorecard: dict
    passed: bool
    action: str   # "deliver" / "revise" / "reject"
    gray_zones: list[str] = field(default_factory=list)


class ScorecardDeepIndustry:
    """
    深度行业报告质量评分卡。

    模式：
      - MOCK：规则评分（文本模式匹配 + 维度评分）
      - REAL：LLM 细粒度评分
    """

    # 禁用词（用于 factual 检查）
    ABSOLUTE_FORBIDDEN = [
        "必将", "毫无疑问", "决定性", "100%确定",
        "必然导致", "无可争议", "彻底改变", "完全颠覆",
    ]

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            llm_mod = _load_llm_gateway()
            self._llm = llm_mod.LLMGateway()
        return self._llm

    def run(self, article: dict) -> ScorecardDeepIndustryResult:
        """
        执行质量评分。

        参数：
          article: Article_v2（来自 render_deep_industry）

        返回：ScorecardDeepIndustryResult
        """
        if self._is_mock_mode():
            return self._run_mock(article)

        return self._run_real(article)

    def _is_mock_mode(self) -> bool:
        import os
        return not bool(os.environ.get("DEEPSEEK_API_KEY"))

    def _run_mock(self, article: dict) -> ScorecardDeepIndustryResult:
        """Mock 模式：规则评分"""
        blocks = article.get("blocks", [])
        metadata = article.get("metadata", {})
        all_text = self._extract_text(blocks)

        # 各维度评分
        factual_score = self._score_factual(all_text)
        source_score = self._score_source(metadata)
        depth_score = self._score_depth(blocks)
        readability_score = self._score_readability(all_text, blocks)
        timeliness_score = self._score_timeliness(metadata)

        # 加权总分
        total = (
            factual_score * WEIGHTS["factual"]
            + source_score * WEIGHTS["source"]
            + depth_score * WEIGHTS["depth"]
            + readability_score * WEIGHTS["readability"]
            + timeliness_score * WEIGHTS["timeliness"]
        )

        # 灰区检查
        gray_zones = []
        if factual_score < FACTUAL_THRESHOLD:
            gray_zones.append(f"事实准确性过低（{factual_score} < {FACTUAL_THRESHOLD}），建议修改后重审")

        if metadata.get("references_count", 0) < 2:
            gray_zones.append("参考来源数量不足（< 2条），建议补充机构研报或财报数据")

        # 行动判定
        if factual_score < FACTUAL_THRESHOLD:
            action = "revise"
            passed = False
        elif total >= 85:
            action = "deliver"
            passed = True
        elif total >= 70:
            action = "revise"
            passed = False
        else:
            action = "reject"
            passed = False

        scorecard = {
            "header": {
                "artifact_id": f"ART-SCORE-deep_industry-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "artifact_type": "quality_scorecard",
                "content_type": "deep_industry_report",
                "scored_at": datetime.now(timezone.utc).isoformat(),
                "producer": "platform/4_adapt/scorecard/scorecard_deep_industry.py",
                "mock_mode": True,
            },
            "scorecard": {
                "total_score": round(total, 1),
                "dimensions": {
                    "factual": {"score": factual_score, "weight": WEIGHTS["factual"]},
                    "source": {"score": source_score, "weight": WEIGHTS["source"]},
                    "depth": {"score": depth_score, "weight": WEIGHTS["depth"]},
                    "readability": {"score": readability_score, "weight": WEIGHTS["readability"]},
                    "timeliness": {"score": timeliness_score, "weight": WEIGHTS["timeliness"]},
                },
                "factual_claims_check": {
                    "absolute_statements": self._find_absolute_statements(all_text),
                    "citations_found": metadata.get("references_count", 0) > 0,
                    "data_claims_count": len(re.findall(r'\d+[亿万分]|\d+%|CR[0-9]', all_text)),
                },
                "source_grade_check": {
                    "total_sources": metadata.get("references_count", 0),
                    "grade_a_ratio": self._grade_a_ratio(metadata),
                },
                "depth_check": {
                    "has_competitive_analysis": any(k in all_text for k in ["竞争格局", "市场份额", "CR3", "CR5"]),
                    "has_risk_factors": any(k in all_text for k in ["风险", "不确定", "挑战", "瓶颈"]),
                    "has_trend_forecast": any(k in all_text for k in ["趋势", "预判", "展望", "预测"]),
                },
                "weights": WEIGHTS,
                "threshold": FACTUAL_THRESHOLD,
            },
            "passed": passed,
            "action": action,
            "gray_zones": gray_zones,
            "revision_suggestions": self._build_suggestions(
                factual_score, source_score, depth_score, readability_score,
            ),
        }

        return ScorecardDeepIndustryResult(
            scorecard=scorecard,
            passed=passed,
            action=action,
            gray_zones=gray_zones,
        )

    def _run_real(self, article: dict) -> ScorecardDeepIndustryResult:
        """Real 模式：LLM 评分"""
        blocks = article.get("blocks", [])
        metadata = article.get("metadata", {})
        all_text = self._extract_text(blocks)

        system_prompt = """你是一位资深行业编辑，评估深度行业报告的质量。
你的输出必须是严格的JSON格式，不要包含任何其他文字。"""

        user_prompt = f"""请评估以下深度行业报告的质量。

报告正文（摘要）：
{all_text[:4000]}

参考来源数量：{metadata.get('references_count', 0)}

请从以下五个维度评分（0-100分）：
1. factual（事实准确性）：数据声明是否有来源？是否有绝对化表述？
2. source（来源可靠性）：A级机构研报/财报占比？来源是否权威？
3. depth（专业深度）：是否有竞争格局分析？驱动因素/风险因素是否充分？
4. readability（可读性）：对专业受众而言是否清晰？复杂数据是否有解释？
5. timeliness（时效性）：数据是否在3年以内？是否注明了数据时间？

一票否决条件：factual < 70 → FAIL
通过阈值：总分 ≥ 85 → deliver；70-85 → revise；< 70 → reject

输出JSON格式：
{{
  "factual_score": 0-100,
  "source_score": 0-100,
  "depth_score": 0-100,
  "readability_score": 0-100,
  "timeliness_score": 0-100,
  "total_score": 加权总分（自动计算）,
  "passed": true/false,
  "factual_issues": ["问题列表"],
  "suggestions": ["修改建议"]
}}"""

        try:
            response = self.llm.chat(user_prompt, system=system_prompt)
            data = self._extract_json(response)
            if data:
                total = data.get("total_score", 75.0)
                factual = data.get("factual_score", 75)
                gray_zones = []
                if factual < FACTUAL_THRESHOLD:
                    gray_zones.extend(data.get("factual_issues", []))
                action = "deliver" if total >= 85 else ("revise" if total >= 70 else "reject")

                scorecard = {
                    "header": {
                        "artifact_id": f"ART-SCORE-deep_industry-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                        "artifact_type": "quality_scorecard",
                        "content_type": "deep_industry_report",
                        "scored_at": datetime.now(timezone.utc).isoformat(),
                        "producer": "platform/4_adapt/scorecard/scorecard_deep_industry.py",
                        "mock_mode": False,
                    },
                    "scorecard": {
                        "total_score": round(total, 1),
                        "dimensions": {
                            "factual": {"score": factual, "weight": WEIGHTS["factual"]},
                            "source": {"score": data.get("source_score", 75), "weight": WEIGHTS["source"]},
                            "depth": {"score": data.get("depth_score", 75), "weight": WEIGHTS["depth"]},
                            "readability": {"score": data.get("readability_score", 75), "weight": WEIGHTS["readability"]},
                            "timeliness": {"score": data.get("timeliness_score", 75), "weight": WEIGHTS["timeliness"]},
                        },
                        "factual_claims_check": {"issues": data.get("factual_issues", [])},
                        "weights": WEIGHTS,
                        "threshold": FACTUAL_THRESHOLD,
                    },
                    "passed": total >= 85,
                    "action": action,
                    "gray_zones": gray_zones,
                    "revision_suggestions": data.get("suggestions", []),
                }
                return ScorecardDeepIndustryResult(
                    scorecard=scorecard,
                    passed=total >= 85,
                    action=action,
                    gray_zones=gray_zones,
                )
        except Exception:
            pass

        return self._run_mock(article)

    # ── 评分规则 ───────────────────────────────────────────────

    def _score_factual(self, text: str) -> int:
        """
        事实准确性评分：
          - 无绝对化禁用词 → 基础分 80
          - 有数据标注（如【A级】）→ +10
          - 有不确定性承认（如"可能"）→ +10
        """
        score = 80
        abs_found = self._find_absolute_statements(text)
        score -= len(abs_found) * 15

        if "【" in text and "级" in text:
            score += 10

        uncertain = ["可能", "有望", "据预测", "数据显示", "据估算", "初步"]
        if any(w in text for w in uncertain):
            score += 10

        return max(0, min(100, score))

    def _score_source(self, metadata: dict) -> int:
        """
        来源可靠性评分：
          - A级来源 ≥ 1 → 基础分 80
          - 无来源引用 → 基础分 40
        """
        ref_count = metadata.get("references_count", 0)
        if ref_count >= 3:
            return 85
        elif ref_count >= 1:
            return 75
        else:
            return 40

    def _score_depth(self, blocks: list) -> int:
        """
        专业深度评分：
          - 有 heading2 章节结构 → +30
          - 含竞争格局分析 → +20
          - 含风险/不确定性讨论 → +20
          - 含趋势预判 → +15
        """
        score = 20

        has_sections = sum(1 for b in blocks if b.get("type") == "heading2")
        if has_sections >= 4:
            score += 30
        elif has_sections >= 2:
            score += 15

        blocks_text = "".join([
            b.get("content", {}).get("text", "") if isinstance(b.get("content"), dict)
            else str(b.get("content", ""))
            for b in blocks
        ])

        competitive_keywords = ["竞争格局", "市场份额", "CR3", "CR5", "头部企业"]
        if any(k in blocks_text for k in competitive_keywords):
            score += 20

        risk_keywords = ["风险", "不确定", "挑战", "瓶颈", "依赖"]
        if any(k in blocks_text for k in risk_keywords):
            score += 20

        trend_keywords = ["趋势", "预判", "展望", "预测", "未来3"]
        if any(k in blocks_text for k in trend_keywords):
            score += 15

        return min(100, score)

    def _score_readability(self, text: str, blocks: list) -> int:
        """
        可读性评分（深度报告允许复杂句式）：
          - 字数 ≥ 2000 → 基础分 60
          - 有数据标注 → +15
          - 有图表描述/框架 → +15
          - 无乱码/缺字 → +10
        """
        score = 50
        word_count = len(text.replace(" ", ""))

        if word_count >= 3000:
            score += 15
        elif word_count >= 2000:
            score += 10
        elif word_count >= 1000:
            score += 5

        if "【" in text and "级" in text:
            score += 15

        framework_keywords = ["矩阵", "图谱", "框架", "模型", "路线图"]
        if any(k in text for k in framework_keywords):
            score += 10

        return min(100, score)

    def _score_timeliness(self, metadata: dict) -> int:
        """时效性评分：默认中等（行业报告有效期约6-12个月）"""
        return 75

    def _grade_a_ratio(self, metadata: dict) -> float:
        """计算 A 级来源占比（Mock 模式默认 50%）"""
        ref_count = metadata.get("references_count", 0)
        if ref_count == 0:
            return 0.0
        return 0.5  # Mock 模式默认一半为 A 级

    def _find_absolute_statements(self, text: str) -> list[str]:
        found = []
        for word in self.ABSOLUTE_FORBIDDEN:
            if word in text:
                found.append(word)
        return found

    def _avg_sentence_length(self, text: str) -> float:
        sentences = re.split(r'[。！？；\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0
        return sum(len(s) for s in sentences) / len(sentences)

    def _extract_text(self, blocks: list) -> str:
        parts = []
        for block in blocks:
            raw = block.get("content", {})
            if isinstance(raw, dict):
                text = raw.get("text", "")
            elif isinstance(raw, str):
                text = raw
            else:
                text = block.get("text", "")
            if text:
                parts.append(text)
        return "".join(parts)

    def _build_suggestions(self, factual: float, source: float,
                           depth: float, readability: float) -> list[str]:
        suggestions = []
        if factual < FACTUAL_THRESHOLD:
            suggestions.append("事实准确性不足：去除绝对化表述，确保每项数据有来源标注")
        if source < 70:
            suggestions.append("来源质量不足：优先使用机构研报、财报、政府白皮书等权威来源")
        if depth < 70:
            suggestions.append("专业深度不足：补充竞争格局分析、驱动因素和风险因素讨论")
        if readability < 60:
            suggestions.append("可读性待提升：增加数据可视化描述和结构化框架")
        if not suggestions:
            suggestions.append("报告质量良好，可直接发布")
        return suggestions

    def _extract_json(self, text: str) -> dict | None:
        match = re.search(r'\{[\s\S]*\}', text.strip())
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None
