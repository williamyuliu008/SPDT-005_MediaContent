# -*- coding: utf-8 -*-
"""
article_breaking.py — breakdown_news IF-P-2：突发快讯结构化
================================================================

功能：
  1. 接收 IntelligenceBrief（IF-P-1 输出）
  2. 生成4段式文章大纲（导语 + 核心事实 + 时间线 + 背景）
  3. 输出 ArticleOutline（符合 IF-P-2 schema）

IF-P-2 输出 Schema：D:/1_omas/MODLIB/schemas/article_outline.schema.json

使用方式：
  from platform.shared.llm_gateway import LLMGateway
  from platform.radar.radar_breaking import RadarBreaking, RadarBreakingRequest

  # IF-P-1
  radar = RadarBreaking()
  brief_result = radar.run(RadarBreakingRequest(topic="OpenAI 发布"))
  brief = brief_result.brief

  # IF-P-2
  outliner = ArticleBreaking()
  outline = outliner.run(brief)
  # outline["header"]["artifact_id"]
  # outline["sections"]

规范参考：
  - governance/SPDT-005_SOP.md
  - docs/pipeline_module_matrix.md（breakdown_news Structure 规范）
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
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
class ArticleBreakingResult:
    """结构化结果（ArticleOutline）"""
    artifact_id: str
    outline: dict
    mock: bool


# ─────────────────────────────────────────────────────────────────
# 核心大纲生成器
# ─────────────────────────────────────────────────────────────────

class ArticleBreaking:
    """
    breakdown_news 文章结构化模块

    4段式大纲（固定结构）：
      SEC-001 导语（Lead）：80-120字，事件核心一句话
      SEC-002 核心事实（Key Facts）：5个要点，数据+事件+影响
      SEC-003 时间线（Timeline）：按时间排列关键节点
      SEC-004 背景（Context）：为什么重要，100-150字

    目标字数：300-500字
    """

    CONTENT_TYPE = "breakdown_news"
    TARGET_WORDS = 450

    # 固定4段结构（breakdown_news 不需要灵活编排）
    STRUCTURE_TEMPLATE = [
        {
            "section_id": "SEC-001",
            "type": "paragraph",
            "title": "导语",
            "order": 1,
            "target_words": 100,
            "min_words": 60,
            "max_words": 150,
            "style": "客观快速",
            "structure_hints": "一句话交代Who/What/When/Where，新闻六要素优先",
        },
        {
            "section_id": "SEC-002",
            "type": "list",
            "title": "核心事实",
            "order": 2,
            "target_words": 150,
            "min_words": 100,
            "max_words": 250,
            "style": "事实密集",
            "structure_hints": "5个关键事实点，每点一句话，数字优先",
        },
        {
            "section_id": "SEC-003",
            "type": "timeline",
            "title": "事件时间线",
            "order": 3,
            "target_words": 80,
            "min_words": 50,
            "max_words": 150,
            "style": "时间线",
            "structure_hints": "时间点 + 事件描述，简明扼要",
        },
        {
            "section_id": "SEC-004",
            "type": "paragraph",
            "title": "背景",
            "order": 4,
            "target_words": 120,
            "min_words": 80,
            "max_words": 200,
            "style": "简洁背景",
            "structure_hints": "为什么重要、对行业/公众的影响",
        },
    ]

    def run(self, brief: dict) -> ArticleBreakingResult:
        """
        执行结构化。

        参数：
          brief: IntelligenceBrief dict（IF-P-1 输出）

        返回：
          ArticleBreakingResult（包含 artifact_id 和 outline dict）
        """
        _llm = _load_llm_gateway()
        LLMGateway = _llm.LLMGateway
        BREAKING_NEWS_MOCK_ARTICLE_OUTLINE = _llm.BREAKING_NEWS_MOCK_ARTICLE_OUTLINE

        gateway = LLMGateway()
        brief_id = brief["header"]["artifact_id"]
        pipeline_id = brief["header"].get("pipeline_id", "UNKNOWN")
        signals = brief.get("signals", [])
        sources = brief.get("sources", [])

        # ── MOCK 模式 ──────────────────────────────────────────
        if gateway.config.mock_mode:
            mock_outline = _llm.BREAKING_NEWS_MOCK_ARTICLE_OUTLINE
            outline = self._build_mock_outline(brief, brief_id, pipeline_id, mock_outline)
            return ArticleBreakingResult(
                artifact_id=outline["header"]["artifact_id"],
                outline=outline,
                mock=True,
            )

        # ── 真实生成 ──────────────────────────────────────────
        signals_text = "\n".join(
            f"- [{s.get('signal_id')}] {s.get('text')} (confidence={s.get('confidence', 0):.2f})"
            for s in signals[:5]
        )

        prompt = f"""你是一个突发新闻编辑。请根据以下情报简报，生成突发快讯的4段式大纲。

情报信号：
{signals_text}

要求：
1. 生成4个固定章节：导语(SEC-001)、核心事实(SEC-002)、时间线(SEC-003)、背景(SEC-004)
2. 导语：60-150字，一句话交代核心事件
3. 核心事实：5个要点，每个要点20-30字，数字优先
4. 时间线：3-5个时间节点
5. 背景：80-200字，说明事件重要性
6. 总目标字数：约450字
7. 语气：客观、快速、专业，禁止推测性内容
8. 只引用 A/B 级来源

输出 JSON 格式：
{{
  "title": "文章标题（15-30字）",
  "subtitle": "副标题（可选，20-40字）",
  "sections": [
    {{"section_id": "SEC-001", "title": "导语", "order": 1, "target_words": 100, "style": "客观快速", "structure_hints": "..."}},
    ...
  ],
  "word_count_target": 450,
  "references_plan": ["source_id列表"],
  "terminology_plan": ["关键词1", "关键词2"],
  "visual_elements_plan": ["timeline"]
}}
"""
        response = gateway.structured(
            prompt=prompt,
            schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "subtitle": {"type": "string"},
                    "sections": {"type": "array"},
                    "word_count_target": {"type": "integer"},
                    "references_plan": {"type": "array"},
                    "terminology_plan": {"type": "array"},
                },
                "required": ["title", "sections", "word_count_target"],
            },
            temperature=0.4,
            max_tokens=1500,
        )

        try:
            data = json.loads(response.content)
        except Exception:
            data = {}

        # 合并 LLM 生成与固定结构
        outline = self._build_outline_from_data(
            brief, data, brief_id, pipeline_id
        )

        return ArticleBreakingResult(
            artifact_id=outline["header"]["artifact_id"],
            outline=outline,
            mock=False,
        )

    def _build_outline_from_data(
        self, brief: dict, data: dict, brief_id: str, pipeline_id: str
    ) -> dict:
        """将 LLM 输出与固定结构合并"""
        # 补充固定 sections（LLM 可能生成不完整的 sections）
        llm_sections = data.get("sections", [])
        section_ids = {s["section_id"] for s in llm_sections}

        for template_sec in self.STRUCTURE_TEMPLATE:
            if template_sec["section_id"] not in section_ids:
                # LLM 缺失的章节，用模板补充
                llm_sections.append(template_sec)

        # 按 order 排序
        llm_sections.sort(key=lambda s: s.get("order", 99))

        # 提取 references_plan
        source_ids = [s["source_id"] for s in brief.get("sources", [])]

        # 提取 terminology
        terms = set()
        for sig in brief.get("signals", []):
            terms.update(sig.get("entities", []))
            terms.update(sig.get("topics", []))

        artifact_id = f"ART-OUTLINE-{self.CONTENT_TYPE}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

        outline = {
            "header": {
                "artifact_id": artifact_id,
                "artifact_type": "article_outline",
                "brief_id": brief_id,
                "content_type": self.CONTENT_TYPE,
                "pipeline_dimensions": brief["header"].get("pipeline_dimensions", {
                    "accuracy": 4, "literary": 2, "professional_depth": 3
                }),
                "produced_at": datetime.now(timezone.utc).isoformat(),
                "producer": "platform/2_structure/article/article_breaking.py",
                "pipeline_id": pipeline_id,
            },
            "title": data.get("title", "突发：事件速报"),
            "subtitle": data.get("subtitle", ""),
            "sections": llm_sections,
            "word_count_target": data.get("word_count_target", self.TARGET_WORDS),
            "word_count_range": {"min": 300, "max": 600},
            # 保留完整来源对象（含 grade/source_id），供 render/adapt 读取
            "references_plan": [
                {"id": s.get("source_id", ""), **s}
                for s in brief.get("sources", [])
            ],
            "terminology_plan": list(terms)[:10],
            "visual_elements_plan": ["timeline"],
            "knowledge_graph": None,
            "gray_zones": brief.get("gray_zones", []),
        }

        return outline

    def _build_mock_outline(self, brief: dict, brief_id: str, pipeline_id: str, mock_outline_template: dict) -> dict:
        """构建 MOCK ArticleOutline"""
        import copy
        outline = copy.deepcopy(mock_outline_template)
        outline["header"]["artifact_id"] = f"ART-OUTLINE-{self.CONTENT_TYPE}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        outline["header"]["brief_id"] = brief_id
        outline["header"]["pipeline_id"] = pipeline_id
        outline["header"]["produced_at"] = datetime.now(timezone.utc).isoformat()
        # 用 brief 的第一条信号更新标题
        if brief.get("signals"):
            sig = brief["signals"][0]
            outline["title"] = f"突发：{sig.get('text', '事件速报')[:30]}"
        # 传入完整来源对象（含 grade），与真实路径一致
        outline["references_plan"] = [
            {"id": s.get("source_id", ""), **s}
            for s in brief.get("sources", [])
        ]
        return outline


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse
    from platform.radar.radar_breaking import RadarBreaking, RadarBreakingRequest

    parser = argparse.ArgumentParser(description="breakdown_news 结构化大纲生成")
    parser.add_argument("--topic", default="OpenAI 发布新模型")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    # IF-P-1
    radar = RadarBreaking()
    brief_result = radar.run(RadarBreakingRequest(topic=args.topic))
    brief = brief_result.brief

    print(f"\n[article_breaking] brief_id: {brief['header']['artifact_id']}")

    # IF-P-2
    outliner = ArticleBreaking()
    result = outliner.run(brief)

    print(f"  outline_id: {result.artifact_id}")
    print(f"  title: {result.outline.get('title', 'N/A')}")
    print(f"  sections: {len(result.outline.get('sections', []))}")
    print(f"  mock: {result.mock}")


if __name__ == "__main__":
    main()
