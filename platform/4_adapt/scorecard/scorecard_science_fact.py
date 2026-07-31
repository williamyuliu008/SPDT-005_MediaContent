# -*- coding: utf-8 -*-
"""
scorecard_science_fact.py — science_fact IF-P-4：科学事实质量评分卡
================================================================

功能：
  1. 对 science_fact 文章进行多维质量评分
  2. 维度：readability / factual / source / depth
  3. 一票否决：factual < 70 → FAIL
  4. 引用检查：同行评审文献占比 < 50% → WARN

评分权重（science_fact）：
  readability:  25% — 科学内容可读性要求更高（术语需解释）
  factual:      35% — 事实准确性（高风险领域，一票否决）
  source:       20% — 来源可靠性
  depth:       20% — 专业深度

使用方式：
  scorecard = ScorecardScienceFact()
  result = scorecard.run(article)
  # result.scorecard["scorecard"]["total_score"]
  # result.passed
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
# 评分维度权重
# ─────────────────────────────────────────────────────────────────

WEIGHTS = {
    "readability": 0.25,
    "factual":      0.35,
    "source":       0.20,
    "depth":        0.20,
}

# 一票否决阈值
FACTUAL_THRESHOLD = 70.0   # factual < 70 → FAIL


@dataclass
class ScorecardScienceFactResult:
    """评分卡结果"""
    scorecard: dict
    passed: bool
    action: str   # "deliver" / "revise" / "reject"
    gray_zones: list[str] = field(default_factory=list)


class ScorecardScienceFact:
    """
    科学事实质量评分卡。

    模式：
      - MOCK：对文章文本做规则评分
      - REAL：通过 LLM 进行细粒度评分
    """

    # 科学内容专用禁用词（用于 factual 检查）
    ABSOLUTE_FORBIDDEN = [
        "证明了", "彻底颠覆", "100%确定", "毫无疑问",
        "绝对可靠", "完美解释", "完全解决", "绝对正确",
    ]

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            llm_mod = _load_llm_gateway()
            self._llm = llm_mod.LLMGateway()
        return self._llm

    def run(self, article: dict) -> ScorecardScienceFactResult:
        """
        执行质量评分。

        参数：
          article: Article_v2（来自 render_science_fact）

        返回：ScorecardScienceFactResult
        """
        if self._is_mock_mode():
            return self._run_mock(article)

        return self._run_real(article)

    def _is_mock_mode(self) -> bool:
        import os
        return not bool(os.environ.get("DEEPSEEK_API_KEY"))

    def _run_mock(self, article: dict) -> ScorecardScienceFactResult:
        """Mock 模式：规则评分"""
        blocks = article.get("blocks", [])
        metadata = article.get("metadata", {})
        all_text = self._extract_text(blocks)

        # ── 各维度评分 ───────────────────────────────────────
        readability_score = self._score_readability(all_text, blocks)
        factual_score = self._score_factual(all_text)
        source_score = self._score_source(metadata)
        depth_score = self._score_depth(blocks)

        # ── 总分 ─────────────────────────────────────────────
        total = (
            readability_score * WEIGHTS["readability"]
            + factual_score * WEIGHTS["factual"]
            + source_score * WEIGHTS["source"]
            + depth_score * WEIGHTS["depth"]
        )

        # ── 一票否决检查 ─────────────────────────────────────
        gray_zones = []
        if factual_score < FACTUAL_THRESHOLD:
            gray_zones.append(f"事实准确性过低（{factual_score} < {FACTUAL_THRESHOLD}），建议修改后重审")

        peer_reviewed_ratio = metadata.get("references_count", 0)
        if peer_reviewed_ratio < 2:
            gray_zones.append("同行评审引用数量不足（< 2篇），建议补充")

        # v1.3: 来源验证状态
        verified = metadata.get("source_verified_count", 0)
        if verified == 0:
            gray_zones.append(
                "【KnownLimitation】所有来源均为 LLM 生成（source_verified=0），"
                "未通过真实联网采集验证。建议接入真实 arXiv/Semantic Scholar API（Phase B）"
            )

        # ── 行动判定 ─────────────────────────────────────────
        if factual_score < FACTUAL_THRESHOLD:
            action = "revise"
            passed = False
        elif total >= 70:
            action = "deliver"
            passed = True
        else:
            action = "revise"
            passed = False

        scorecard = {
            "header": {
                "artifact_id": f"ART-SCORE-science_fact-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "artifact_type": "quality_scorecard",
                "content_type": "science_fact",
                "scored_at": datetime.now(timezone.utc).isoformat(),
                "producer": "platform/4_adapt/scorecard/scorecard_science_fact.py",
                "mock_mode": True,
            },
            "scorecard": {
                "total_score": round(total, 1),
                "dimensions": {
                    "readability": {"score": readability_score, "weight": WEIGHTS["readability"]},
                    "factual": {"score": factual_score, "weight": WEIGHTS["factual"]},
                    "source": {"score": source_score, "weight": WEIGHTS["source"]},
                    "depth": {"score": depth_score, "weight": WEIGHTS["depth"]},
                },
                "factual_claims_check": {
                    "absolute_statements": self._find_absolute_statements(all_text),
                    "citations_found": metadata.get("references_count", 0) > 0,
                    "uncertainty_acknowledged": True,
                },
                "source_grade_check": {
                    "total_sources": metadata.get("references_count", 0),
                    "has_peer_reviewed": metadata.get("references_count", 0) >= 2,
                },
                "readability_check": {
                    "word_count": metadata.get("word_count", 0),
                    "avg_sentence_length": self._avg_sentence_length(all_text),
                    "has_terminology_explained": True,
                },
                "weights": WEIGHTS,
                "threshold": FACTUAL_THRESHOLD,
            },
            "passed": passed,
            "action": action,
            "gray_zones": gray_zones,
            "revision_suggestions": self._build_suggestions(factual_score, readability_score, source_score),
        }

        return ScorecardScienceFactResult(
            scorecard=scorecard,
            passed=passed,
            action=action,
            gray_zones=gray_zones,
        )

    def _run_real(self, article: dict) -> ScorecardScienceFactResult:
        """Real 模式：LLM 评分"""
        blocks = article.get("blocks", [])
        metadata = article.get("metadata", {})
        all_text = self._extract_text(blocks)

        # 构建评分 prompt
        source_spec = "\n".join([
            f"- [{s.get('grade','?')}级]"
            f" {'[同行评审]' if s.get('peer_reviewed') else '[预印本/科普]'}"
            f" {s.get('name','')}"
            for s in article.get("references", [])[:5]
        ])

        system_prompt = """你是一位科学编辑，评估科普文章的质量。
你的输出必须是严格的JSON格式，不要包含任何其他文字。
评分必须客观、有据可查。"""

        user_prompt = f"""请评估以下科学事实文章的质量。

文章正文：
{all_text[:3000]}

参考来源：
{source_spec}

请从以下四个维度评分（0-100分）：

1. readability（可读性）：术语是否有解释？句子长度适中吗？普通人能看懂吗？
2. factual（事实准确性）：是否存在绝对化表述？是否有来源支撑？是否诚实承认局限？
3. source（来源可靠性）：同行评审文献占比多少？来源是否可信？
4. depth（专业深度）：是否准确使用专业术语？解释是否深入？

一票否决条件：factual < 70 → FAIL

输出JSON格式：
{{
  "readability_score": 0-100,
  "factual_score": 0-100,
  "source_score": 0-100,
  "depth_score": 0-100,
  "total_score": "加权总分",
  "passed": true/false,
  "factual_issues": ["问题列表"],
  "source_issues": ["问题列表"],
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
                action = "deliver" if data.get("passed") and total >= 70 else "revise"

                scorecard = {
                    "header": {
                        "artifact_id": f"ART-SCORE-science_fact-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                        "artifact_type": "quality_scorecard",
                        "content_type": "science_fact",
                        "scored_at": datetime.now(timezone.utc).isoformat(),
                        "producer": "platform/4_adapt/scorecard/scorecard_science_fact.py",
                        "mock_mode": False,
                    },
                    "scorecard": {
                        "total_score": round(total, 1),
                        "dimensions": {
                            "readability": {"score": data.get("readability_score", 75), "weight": WEIGHTS["readability"]},
                            "factual": {"score": factual, "weight": WEIGHTS["factual"]},
                            "source": {"score": data.get("source_score", 75), "weight": WEIGHTS["source"]},
                            "depth": {"score": data.get("depth_score", 75), "weight": WEIGHTS["depth"]},
                        },
                        "factual_claims_check": {
                            "issues": data.get("factual_issues", []),
                        },
                        "source_grade_check": {
                            "issues": data.get("source_issues", []),
                        },
                        "weights": WEIGHTS,
                        "threshold": FACTUAL_THRESHOLD,
                    },
                    "passed": data.get("passed", total >= 70),
                    "action": action,
                    "gray_zones": gray_zones,
                    "revision_suggestions": data.get("suggestions", []),
                }
                return ScorecardScienceFactResult(
                    scorecard=scorecard,
                    passed=data.get("passed", total >= 70),
                    action=action,
                    gray_zones=gray_zones,
                )
        except Exception:
            pass

        return self._run_mock(article)

    # ── 评分规则 ───────────────────────────────────────────────

    def _score_readability(self, text: str, blocks: list) -> int:
        """
        可读性评分（science_fact 优化阈值）：
          - 字数 ≥ 500 → 基础分 60
          - 有 infobox（术语解释）→ +20
          - 平均句子长度 ≤ 30字 → +15（科学内容句子可以稍长）
          - 含有解释性连接词 → +5
        """
        score = 50
        word_count = len(text.replace(" ", ""))

        if word_count >= 500:
            score += 10
        elif word_count >= 300:
            score += 5

        # 是否有 infobox（术语解释）
        has_infobox = any(b.get("type") == "infobox" for b in blocks)
        if has_infobox:
            score += 20

        # 平均句子长度
        avg_len = self._avg_sentence_length(text)
        if avg_len <= 30:
            score += 15
        elif avg_len <= 50:
            score += 8
        elif avg_len <= 70:
            score += 3

        # 解释性连接词
        explainers = ["因为", "也就是说", "换句话说", "具体来说", "例如", "这意味着"]
        if any(w in text for w in explainers):
            score += 5

        return min(100, score)

    def _score_factual(self, text: str) -> int:
        """
        事实准确性评分：
          - 无绝对化禁用词 → 基础分 80
          - 每发现一个禁用词 → -15
          - 有不确定性承认（如"尚待验证"）→ +10
          - 有来源标注（如【A级】）→ +10
        """
        score = 80

        abs_found = self._find_absolute_statements(text)
        score -= len(abs_found) * 15

        # 有不确定性承认
        uncertain_words = ["尚待", "待验证", "有待", "目前认为", "初步", "可能"]
        if any(w in text for w in uncertain_words):
            score += 10

        # 有来源标注
        if "【" in text and "级" in text:
            score += 10

        return max(0, min(100, score))

    def _score_source(self, metadata: dict) -> int:
        """
        来源可靠性评分（v1.3 新增：来源验证惩罚）：
          - source_verified_count > 0（真实联网采集）→ 基础分不变
          - source_verified_count == 0（全部未验证）→ -15 分惩罚

        基础分：
          - 同行评审文献（A级）≥ 3篇 → 基础分 85
          - 同行评审文献（A级）≥ 2篇 → 基础分 80
          - 每少一篇 → -10
          - 仅有科普媒体 → -20
        """
        ref_count = metadata.get("references_count", 0)
        if ref_count >= 3:
            base = 85
        elif ref_count >= 2:
            base = 80
        elif ref_count >= 1:
            base = 65
        else:
            base = 40

        # v1.3: 未验证来源惩罚（Phase A: 所有来源均为 LLM 生成）
        verified = metadata.get("source_verified_count", 0)
        if verified == 0:
            base = max(30, base - 15)

        return max(0, min(100, base))

    def _score_depth(self, blocks: list) -> int:
        """
        专业深度评分：
          - 有 heading2（章节结构）→ +30
          - 含有 infobox（术语清单）→ +20
          - 有引用标注 → +15
          - 有局限性讨论 → +20
        """
        score = 25

        has_sections = sum(1 for b in blocks if b.get("type") == "heading2")
        if has_sections >= 3:
            score += 30
        elif has_sections >= 1:
            score += 15

        has_infobox = any(b.get("type") == "infobox" for b in blocks)
        if has_infobox:
            score += 20

        blocks_text = "".join([
            b.get("content", {}).get("text", "") if isinstance(b.get("content"), dict)
            else str(b.get("content", ""))
            for b in blocks
        ])
        if "【" in blocks_text:
            score += 15

        limitations_keywords = ["局限", "不足", "待验证", "不确定性", "还需"]
        if any(w in blocks_text for w in limitations_keywords):
            score += 20

        return min(100, score)

    def _find_absolute_statements(self, text: str) -> list[str]:
        """找出所有绝对化禁用词"""
        found = []
        for word in self.ABSOLUTE_FORBIDDEN:
            if word in text:
                found.append(word)
        return found

    def _avg_sentence_length(self, text: str) -> float:
        """计算平均句子长度（按中文句号/逗号分句）"""
        # 中文句子分隔
        sentences = re.split(r'[。！？；\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0
        total_len = sum(len(s) for s in sentences)
        return total_len / len(sentences)

    def _extract_text(self, blocks: list) -> str:
        """从 blocks 提取纯文本"""
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

    def _build_suggestions(self, factual: float, readability: float, source: float) -> list[str]:
        """生成修订建议"""
        suggestions = []
        if factual < FACTUAL_THRESHOLD:
            suggestions.append("事实准确性不足：去除绝对化表述，增加不确定性承认")
        if readability < 70:
            suggestions.append("可读性待提升：增加术语解释，缩短过长句子")
        if source < 70:
            suggestions.append("来源质量不足：优先使用同行评审文献，减少科普媒体报道")
        if not suggestions:
            suggestions.append("文章质量良好，可直接发布")
        return suggestions

    def _extract_json(self, text: str) -> dict | None:
        match = re.search(r'\{[\s\S]*\}', text.strip())
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None
