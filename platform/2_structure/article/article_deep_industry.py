# -*- coding: utf-8 -*-
"""
article_deep_industry.py — deep_industry_report IF-P-2：深度行业报告结构化
============================================================================

功能：
  1. 将 IntelligenceBrief 转化为 ArticleOutline（IF-P-2）
  2. 标准六段式结构：摘要 → 背景 → 核心发现 → 深度分析 → 趋势预判 → 结论建议
  3. 知识节点提取、引注计划

大纲结构说明：
  - 摘要（Abstract）：核心观点 + 关键数据（100-200字）
  - 背景（Background）：行业规模、定义、政策环境
  - 核心发现（Core Findings）：3-5个关键发现，每个附数据支撑
  - 深度分析（Deep Analysis）：竞争格局、驱动因素、风险因素
  - 趋势预判（Trend Forecast）：3-5年趋势展望
  - 结论建议（Conclusion）：对读者（企业/投资者/从业者）的行动建议

使用方式：
  article = ArticleDeepIndustry()
  outline = article.run(brief)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
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
# 标准大纲模板（deep_industry_report 专用）
# ─────────────────────────────────────────────────────────────────

DEEP_INDUSTRY_OUTLINE_TEMPLATE = {
    "structure_type": "deep_industry_report",
    "sections": [
        {
            "section_id": "sec_abstract",
            "heading": "摘要",
            "type": "abstract",
            "description": "核心观点（3-5条）+ 关键数据，让读者快速了解报告结论",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_background",
            "heading": "行业背景",
            "type": "background",
            "description": "行业定义与边界、市场规模（GVM/增速）、政策环境、产业链全景",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_findings",
            "heading": "核心发现",
            "type": "findings",
            "description": "3-5个数据驱动的重要发现，每个发现含数据来源",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_analysis",
            "heading": "深度分析",
            "type": "analysis",
            "description": "竞争格局、驱动因素（技术/需求/政策）、主要风险因素",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_trends",
            "heading": "趋势预判",
            "type": "trends",
            "description": "未来3-5年行业走向，关键变量与不确定性",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_conclusion",
            "heading": "结论与建议",
            "type": "conclusion",
            "description": "对不同读者群体（企业/投资者/从业者）的具体行动建议",
            "knowledge_nodes": [],
        },
    ],
}


@dataclass
class ArticleDeepIndustryResult:
    """结构化结果"""
    outline: dict


class ArticleDeepIndustry:
    """
    深度行业报告结构化引擎。

    模式：
      - MOCK：标准六段式模板 + 知识节点提取
      - REAL：LLM 根据具体行业情报定制大纲
    """

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            llm_mod = _load_llm_gateway()
            self._llm = llm_mod.LLMGateway()
        return self._llm

    def run(self, brief: dict) -> ArticleDeepIndustryResult:
        """
        执行结构化。

        参数：
          brief: IntelligenceBrief（来自 radar_deep_industry）

        返回：ArticleDeepIndustryResult(outline=dict)
        """
        if self._is_mock_mode():
            return self._run_mock(brief)

        return self._run_real(brief)

    def _is_mock_mode(self) -> bool:
        import os
        return not bool(os.environ.get("DEEPSEEK_API_KEY"))

    def _run_mock(self, brief: dict) -> ArticleDeepIndustryResult:
        """Mock 模式：标准六段式模板"""
        outline = self._build_mock_outline(brief)
        return ArticleDeepIndustryResult(outline=outline)

    def _run_real(self, brief: dict) -> ArticleDeepIndustryResult:
        """Real 模式：LLM 生成定制大纲"""
        outline = self._build_outline_from_data(brief)
        return ArticleDeepIndustryResult(outline=outline)

    # ── Mock 大纲构建 ───────────────────────────────────────────

    def _build_mock_outline(self, brief: dict) -> dict:
        """从 brief 构建 Mock 大纲"""
        topic = brief.get("topic", "深度行业分析")
        industry = brief.get("industry", "")
        signals = brief.get("signals", [])
        sources = brief.get("sources", [])

        outline = json.loads(json.dumps(DEEP_INDUSTRY_OUTLINE_TEMPLATE))

        # 摘要
        outline["sections"][0]["knowledge_nodes"] = [
            f"{topic}市场正在快速增长",
            f"{industry or '该行业'}呈现结构性机会",
            "头部企业加速扩张，国产替代为主线",
        ]

        # 背景
        outline["sections"][1]["knowledge_nodes"] = [
            f"{industry or '行业'}的市场规模和增速",
            "产业链上中下游的核心环节",
            "当前政策环境和支持力度",
        ]

        # 核心发现
        outline["sections"][2]["knowledge_nodes"] = [
            f"{topic}领域的3-5个关键数据",
            "市场集中度和竞争格局变化",
            "技术路线和商业模式创新",
        ]

        # 深度分析
        outline["sections"][3]["knowledge_nodes"] = [
            "竞争格局：主要玩家及其市场份额",
            "驱动因素：技术/需求/政策三维度",
            "主要风险：技术路线不确定性/政策变化/供应链风险",
        ]

        # 趋势预判
        outline["sections"][4]["knowledge_nodes"] = [
            "未来3-5年的市场走向",
            "关键变量的情景分析",
            "可能的颠覆性因素",
        ]

        # 结论建议
        outline["sections"][5]["knowledge_nodes"] = [
            "对企业的战略建议：聚焦/扩张/转型",
            "对投资者的建议：关注指标和风险点",
            "对从业者的建议：技能储备和职业路径",
        ]

        outline["references_plan"] = sources
        outline.update({
            "status": "structured",
            "structure_type": "deep_industry_report",
            "content_spec": {
                "content_type": "deep_industry_report",
                "topic": topic,
                "industry": industry,
            },
            "knowledge_points": [node for sec in outline["sections"] for node in sec["knowledge_nodes"]],
        })

        return outline

    def _build_outline_from_data(self, brief: dict) -> dict:
        """Real 模式：LLM 生成大纲"""
        topic = brief.get("topic", "")
        industry = brief.get("industry", "")
        signals = brief.get("signals", [])
        sources = brief.get("sources", [])

        signal_texts = "\n".join([
            f"- [{s.get('importance', '')}] {s.get('text', '')}（数据：{s.get('key_data', '')}）"
            for s in signals[:5]
        ])

        system_prompt = """你是一位资深行业分析师，擅长撰写3000-8000字的深度行业报告。
你的输出必须是严格的JSON格式，不要包含任何其他文字。"""

        user_prompt = f"""请为以下行业研究报告设计结构化大纲。

主题：{topic}
行业：{industry or '未指定'}

情报信号：
{signal_texts}

要求：
1. 六段式结构：摘要 → 行业背景 → 核心发现 → 深度分析 → 趋势预判 → 结论建议
2. 每个章节提供 heading 和 description（200字以内的描述要点）
3. 提取每个章节的 knowledge_nodes（3-5个关键词/短语）
4. 所有数据声明必须可溯源到情报信号

JSON格式：
{{
  "sections": [
    {{"section_id": "...", "heading": "...", "type": "...", "description": "...", "knowledge_nodes": [...]}}
  ],
  "knowledge_points": []
}}"""

        try:
            response = self.llm.chat(user_prompt, system=system_prompt)
            data = self._extract_json(response)
            if data:
                data["references_plan"] = sources
                data["status"] = "structured"
                data["structure_type"] = "deep_industry_report"
                return data
        except Exception:
            pass

        return self._build_mock_outline(brief)

    def _extract_json(self, text: str) -> dict | None:
        import re, json
        match = re.search(r'\{[\s\S]*\}', text.strip())
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None
