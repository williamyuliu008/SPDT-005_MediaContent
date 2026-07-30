# -*- coding: utf-8 -*-
"""
article_science_fact.py — science_fact IF-P-2：科学事实文章结构化
================================================================

功能：
  1. 将 IntelligenceBrief 转化为 ArticleOutline（IF-P-2）
  2. 标准结构：背景 → 原理（通俗解释）→ 证据 → 局限 → 意义
  3. 核心知识节点提取
  4. 引注计划（references_plan）携带完整来源对象

使用方式：
  article = ArticleScienceFact()
  outline = article.run(brief)
"""

from __future__ import annotations

import json
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
# 标准大纲模板（science_fact 专用）
# ─────────────────────────────────────────────────────────────────

SCIENCE_FACT_OUTLINE_TEMPLATE = {
    "structure_type": "science_fact",
    "sections": [
        {
            "section_id": "sec_background",
            "heading": "研究背景：这个问题是什么？",
            "type": "background",
            "description": "介绍研究问题的来龙去脉，为什么重要",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_principle",
            "heading": "核心原理：它是怎么工作的？",
            "type": "explanation",
            "description": "用通俗语言解释核心机制/原理，避免过度技术化",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_evidence",
            "heading": "关键证据：研究怎么证明的？",
            "type": "evidence",
            "description": "介绍实验/计算方法、数据规模、关键发现",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_limitations",
            "heading": "研究局限：还不知道什么？",
            "type": "limitations",
            "description": "诚实讨论研究不足、不确定性、未来方向",
            "knowledge_nodes": [],
        },
        {
            "section_id": "sec_significance",
            "heading": "现实意义：普通人应该关心什么？",
            "type": "significance",
            "description": "从科普角度说明研究的实际意义和影响",
            "knowledge_nodes": [],
        },
    ],
}


@dataclass
class ArticleScienceFactResult:
    """结构化结果"""
    outline: dict


class ArticleScienceFact:
    """
    科学事实文章结构化引擎。

    模式：
      - MOCK：返回标准五段式模板 + 从 brief 中提取知识节点
      - REAL：通过 LLM 根据具体科学发现定制大纲
    """

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            llm_mod = _load_llm_gateway()
            self._llm = llm_mod.LLMGateway()
        return self._llm

    def run(self, brief: dict) -> ArticleScienceFactResult:
        """
        执行结构化。

        参数：
          brief: IntelligenceBrief（来自 radar_science_fact）

        返回：ArticleScienceFactResult(outline=dict)
        """
        if self._is_mock_mode():
            return self._run_mock(brief)

        return self._run_real(brief)

    def _is_mock_mode(self) -> bool:
        import os
        return not bool(os.environ.get("DEEPSEEK_API_KEY"))

    def _run_mock(self, brief: dict) -> ArticleScienceFactResult:
        """Mock 模式：标准五段式模板 + 知识节点提取"""
        outline = self._build_mock_outline(brief)
        return ArticleScienceFactResult(outline=outline)

    def _run_real(self, brief: dict) -> ArticleScienceFactResult:
        """Real 模式：LLM 生成定制大纲"""
        outline = self._build_outline_from_data(brief)
        return ArticleScienceFactResult(outline=outline)

    # ── Mock 大纲构建 ───────────────────────────────────────────

    def _build_mock_outline(self, brief: dict) -> dict:
        """从 brief 构建 Mock 大纲"""
        topic = brief.get("topic", "科学发现")
        signals = brief.get("signals", [])
        sources = brief.get("sources", [])

        # 填充知识节点
        outline = json.loads(json.dumps(SCIENCE_FACT_OUTLINE_TEMPLATE))
        outline["sections"][0]["knowledge_nodes"] = [
            f"{topic}的研究背景",
            "该领域此前的核心问题",
        ]
        outline["sections"][1]["knowledge_nodes"] = [
            f"{topic}的核心机制",
            "关键参数和条件",
        ]
        outline["sections"][2]["knowledge_nodes"] = [
            f"{topic}的实验/计算方法",
            "数据规模和关键指标",
        ]
        outline["sections"][3]["knowledge_nodes"] = [
            "当前研究的局限性",
            "未来需要解决的问题",
        ]
        outline["sections"][4]["knowledge_nodes"] = [
            f"{topic}的现实应用前景",
            "对普通人生活的潜在影响",
        ]

        # 填充引注计划（携带完整来源对象）
        outline["references_plan"] = sources

        outline.update({
            "status": "structured",
            "structure_type": "science_fact",
            "content_spec": {
                "content_type": "science_fact",
                "topic": topic,
            },
            "knowledge_points": [node for sec in outline["sections"] for node in sec["knowledge_nodes"]],
        })

        return outline

    def _build_outline_from_data(self, brief: dict) -> dict:
        """Real 模式：LLM 生成大纲"""
        topic = brief.get("topic", "")
        signals = brief.get("signals", [])
        sources = brief.get("sources", [])

        # 汇总信号文本
        signal_texts = "\n".join([
            f"- [{s.get('source_id', '')}] {s.get('text', '')}"
            for s in signals[:3]
        ])

        system_prompt = """你是一位科学记者，擅长将复杂的学术研究翻译成普通读者能理解的科普文章。
你的输出必须是严格的 JSON 格式，不要包含任何其他文字。"""

        user_prompt = f"""请为以下科学发现设计一篇科普文章的大纲。

主题：{topic}

相关研究发现摘要：
{signal_texts}

要求：
1. 标准五段式结构：背景 → 原理（通俗）→ 证据 → 局限 → 意义
2. 每个章节提供 heading（中文标题）和 description（200字以内的描述要点）
3. 提取每个章节的 knowledge_nodes（3-5个关键词）
4. 所有科学声明必须可溯源到原始研究

请输出 JSON 格式：
{{
  "sections": [
    {{"section_id": "...", "heading": "...", "type": "...", "description": "...", "knowledge_nodes": [...]}}
  ],
  "references_plan": [],  // 引注计划，在 references_plan 字段中不要添加条目，我会另行提供
  "knowledge_points": []
}}"""

        try:
            response = self.llm.chat(user_prompt, system=system_prompt)
            data = self._extract_json(response)
            if data:
                data["references_plan"] = sources
                data["status"] = "structured"
                data["structure_type"] = "science_fact"
                return data
        except Exception:
            pass

        return self._build_mock_outline(brief)

    def _extract_json(self, text: str) -> dict | None:
        """从 LLM 输出中提取 JSON"""
        import re
        text = text.strip()
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None
