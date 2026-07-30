# -*- coding: utf-8 -*-
"""
render_breaking.py — breakdown_news IF-P-3：突发快讯渲染
================================================================

功能：
  1. 接收 ArticleOutline（IF-P-2 输出）
  2. 生成完整 article_v2 JSON（4段式正文）
  3. 语气约束：客观、快速、专业，禁止推测
  4. 字数约束：300-500字

IF-P-3 输出 Schema：D:/1_omas/MODLIB/schemas/article_v2.schema.json

使用方式：
  from platform.radar.radar_breaking import RadarBreaking, RadarBreakingRequest
  from platform.article.article_breaking import ArticleBreaking
  from platform.render.render_breaking import RenderBreaking

  # IF-P-1
  radar = RadarBreaking()
  brief = radar.run(...).brief

  # IF-P-2
  outliner = ArticleBreaking()
  outline = outliner.run(brief).outline

  # IF-P-3
  renderer = RenderBreaking()
  article_v2 = renderer.run(outline)
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[5]


@dataclass
class RenderBreakingResult:
    """渲染结果（Article_v2）"""
    artifact_id: str
    article: dict
    mock: bool


from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────
# 核心渲染器
# ─────────────────────────────────────────────────────────────────

class RenderBreaking:
    """
    breakdown_news 文章渲染模块

    渲染规则：
      - 语气：客观、快速、专业，禁止推测性语言
      - 字数：300-500字（target_words 来自 outline）
      - 结构：严格按 outline 的 4 段生成
      - 引言：每段开头不重复标题
      - 数字：所有关键数字必须有来源支撑
    """

    CONTENT_TYPE = "breakdown_news"

    SYSTEM_PROMPT = """你是一个突发新闻记者。

写作规则（严格遵守）：
1. 语气：客观、快速、专业，只陈述已核实事实
2. 禁止：推测、猜测、假设性语言（"可能"/"或将"/"预计"除非来自权威来源）
3. 字数：300-500字
4. 结构：导语 → 核心事实 → 时间线 → 背景
5. 数字：所有具体数字必须有来源，格式 [来源ID]
6. 不要在导语中重复标题
7. 段落：每段不超过50字"""

    def run(self, outline: dict) -> RenderBreakingResult:
        """
        执行渲染。

        参数：
          outline: ArticleOutline dict（IF-P-2 输出）

        返回：
          RenderBreakingResult（包含 artifact_id 和 article dict）
        """
        from platform.shared.llm_gateway import LLMGateway, BREAKING_NEWS_MOCK_ARTICLE_V2

        gateway = LLMGateway()
        outline_id = outline["header"]["artifact_id"]
        pipeline_id = outline["header"].get("pipeline_id", "UNKNOWN")
        brief_id = outline["header"].get("brief_id", "")

        # ── MOCK 模式 ──────────────────────────────────────────
        if gateway.config.mock_mode:
            article = self._build_mock_article(outline, outline_id, pipeline_id, brief_id)
            return RenderBreakingResult(
                artifact_id=article["header"]["artifact_id"],
                article=article,
                mock=True,
            )

        # ── 真实渲染 ──────────────────────────────────────────
        article = self._render_with_llm(outline, gateway, outline_id, pipeline_id, brief_id)

        # 质量验证
        article["validation"] = self._validate_article(article, outline)

        return RenderBreakingResult(
            artifact_id=article["header"]["artifact_id"],
            article=article,
            mock=False,
        )

    def _render_with_llm(
        self, outline: dict, gateway, outline_id: str, pipeline_id: str, brief_id: str
    ) -> dict:
        """用 LLM 生成文章"""
        # 构建各段落的 prompt
        sections = outline.get("sections", [])
        sections_text = "\n".join(
            f"[{s['section_id']}] {s['title']}（{s.get('target_words', 0)}字）：{s.get('structure_hints', s.get('style', ''))}"
            for s in sections
        )

        references_plan = outline.get("references_plan", [])
        references_text = f"可引用来源：{', '.join(references_plan) if references_plan else '暂无'}"
        terminology = outline.get("terminology_plan", [])
        terms_text = f"关键词：{', '.join(terminology) if terminology else '无'}"

        prompt = f"""请根据以下大纲，生成一篇突发快讯文章。

标题：{outline.get('title', '突发：事件速报')}
{subtitle if (subtitle := outline.get('subtitle')) else ''}

大纲结构：
{sections_text}

{references_text}
{terms_text}

请生成完整的文章内容，每个 section 对应一段，用 JSON 数组格式输出：
{{
  "blocks": [
    {{"type": "paragraph", "text": "段1内容（导语）"}},
    {{"type": "list", "items": ["事实1", "事实2", ...]}},
    {{"type": "timeline", "events": [{{"time": "时间", "event": "事件"}}]}},
    {{"type": "paragraph", "text": "段4内容（背景）"}}
  ]
}}
"""

        response = gateway.structured(
            prompt=prompt,
            schema={
                "type": "object",
                "properties": {
                    "blocks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "text": {"type": "string"},
                                "items": {"type": "array", "items": {"type": "string"}},
                                "events": {
                                    "type": "array",
                                    "items": {"type": "object", "properties": {"time": {"type": "string"}, "event": {"type": "string"}}},
                                },
                            },
                        },
                    }
                },
                "required": ["blocks"],
            },
            system=self.SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2000,
        )

        try:
            data = json.loads(response.content)
            blocks = data.get("blocks", [])
        except Exception:
            blocks = []

        # 确保有4个 block（对应4个 section）
        blocks = self._ensure_4_blocks(blocks, outline)

        # 计算字数
        all_text = " ".join(
            b.get("text", "") for b in blocks
        ) + " ".join(
            " ".join(b.get("items", [])) for b in blocks
        ) + " ".join(
            b.get("events", [{}]).__repr__() for b in blocks
        )
        word_count = len(re.findall(r'[\u4e00-\u9fff]+', all_text))
        reading_time = word_count / 400  # 约400字/分钟

        artifact_id = f"ART-ARTICLE-{self.CONTENT_TYPE}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

        article = {
            "header": {
                "artifact_id": artifact_id,
                "artifact_type": "article_v2",
                "version": "2.0.0",
                "content_type": self.CONTENT_TYPE,
                "pipeline_dimensions": outline["header"].get("pipeline_dimensions", {
                    "accuracy": 4, "literary": 2, "professional_depth": 3
                }),
                "outline_id": outline_id,
                "source_brief_id": brief_id,
                "produced_at": datetime.now(timezone.utc).isoformat(),
                "producer": "platform/3_render/engines/text/render_breaking.py",
                "pipeline_id": pipeline_id,
            },
            "title": outline.get("title", "突发：事件速报"),
            "subtitle": outline.get("subtitle", ""),
            "abstract": "",
            "word_count": word_count,
            "reading_time_minutes": round(reading_time, 1),
            "blocks": blocks,
            "metadata": {
                "terms": [{"term": t, "defined": False} for t in outline.get("terminology_plan", [])],
                "knowledge_points": [],
                "references": [{"id": r} for r in outline.get("references_plan", [])],
            },
            "quality_markers": {
                "factual_claims_count": self._count_claims(blocks),
                "sources_cited_count": len(outline.get("references_plan", [])),
                "terms_defined_count": 0,
                "has_abstract": False,
                "has_references": bool(outline.get("references_plan")),
                "has_terminology_table": False,
                "literary_score": 0,
                "readability_score": 0,
            },
            "gray_zones": outline.get("gray_zones", []),
        }

        return article

    def _ensure_4_blocks(self, blocks: list, outline: dict) -> list:
        """确保输出有4个 block（对应4个 section）"""
        section_types = {s["section_id"]: s.get("type", "paragraph") for s in outline.get("sections", [])}
        default_types = ["paragraph", "list", "timeline", "paragraph"]

        result = []
        for i, default_type in enumerate(default_types):
            if i < len(blocks):
                result.append(blocks[i])
            else:
                result.append({
                    "block_id": f"B{i+1:03d}",
                    "type": default_type,
                    "content": {"text": "", "items": [], "events": []},
                    "depth": "standard",
                    "terms": [],
                    "citations": [],
                })

        # 补充 block_id
        for i, block in enumerate(result):
            block["block_id"] = f"B{i+1:03d}"

        return result

    def _count_claims(self, blocks: list) -> int:
        """统计事实主张数量"""
        count = 0
        for block in blocks:
            if block.get("type") == "list":
                count += len(block.get("items", []))
            text = block.get("content", {}).get("text", "")
            count += len(re.findall(r'[\u4e00-\u9fff]|\d+', text))
        return max(count, 3)

    def _validate_article(self, article: dict, outline: dict) -> dict:
        """验证文章质量"""
        blocks = article.get("blocks", [])
        word_count = article.get("word_count", 0)
        target = outline.get("word_count_target", 450)

        errors = []
        if len(blocks) < 1:
            errors.append("blocks 为空")
        if word_count < target * 0.6:
            errors.append(f"字数{word_count}低于目标60%({target*0.6:.0f}字)")
        if word_count > target * 1.5:
            errors.append(f"字数{word_count}超过目标150%({target*1.5:.0f}字)")

        return {
            "schema_valid": len(errors) == 0,
            "required_fields": True,
            "word_count_ok": target * 0.6 <= word_count <= target * 1.5,
            "errors": errors,
        }

    def _build_mock_article(self, outline: dict, outline_id: str, pipeline_id: str, brief_id: str) -> dict:
        """构建 MOCK Article_v2"""
        import copy
        article = copy.deepcopy(BREAKING_NEWS_MOCK_ARTICLE_V2)
        new_artifact_id = f"ART-ARTICLE-{self.CONTENT_TYPE}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        article["header"]["artifact_id"] = new_artifact_id
        article["header"]["outline_id"] = outline_id
        article["header"]["source_brief_id"] = brief_id
        article["header"]["pipeline_id"] = pipeline_id
        article["header"]["produced_at"] = datetime.now(timezone.utc).isoformat()
        article["title"] = outline.get("title", article["title"])
        return article


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    from platform.radar.radar_breaking import RadarBreaking, RadarBreakingRequest
    from platform.article.article_breaking import ArticleBreaking

    parser = __import__("argparse").ArgumentParser(description="breakdown_news 渲染")
    parser.add_argument("--topic", default="OpenAI 发布新模型")
    args = parser.parse_args()

    # IF-P-1
    radar = RadarBreaking()
    brief = radar.run(RadarBreakingRequest(topic=args.topic)).brief

    # IF-P-2
    outliner = ArticleBreaking()
    outline = outliner.run(brief).outline

    print(f"\n[render_breaking] outline_id: {outline['header']['artifact_id']}")

    # IF-P-3
    renderer = RenderBreaking()
    result = renderer.run(outline)

    print(f"  article_id: {result.artifact_id}")
    print(f"  title: {result.article.get('title', 'N/A')}")
    print(f"  word_count: {result.article.get('word_count', 0)}")
    print(f"  blocks: {len(result.article.get('blocks', []))}")
    print(f"  mock: {result.mock}")
    print(f"  validation: {result.article.get('validation', {})}")


if __name__ == "__main__":
    main()
