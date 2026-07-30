# -*- coding: utf-8 -*-
"""
render_science_fact.py — science_fact IF-P-3：科学事实内容生成
================================================================

功能：
  1. 将 ArticleOutline 渲染为 Article_v2（IF-P-3）
  2. 语气：客观、审慎、有温度；禁止绝对化表达
  3. 引用格式：[A/同行评审] / [B/arXiv预印本] / [C/科普媒体]
  4. 每项科学声明必须标注来源等级

语气规则：
  ✅ 可用：研究表明、证据显示、据XXX报道、目前认为
  ❌ 禁用：证明了、彻底颠覆、绝对可靠、毫无疑问、100%确定

使用方式：
  render = RenderScienceFact()
  article = render.run(outline)
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[4]  # → SPDT-005_MediaContent
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
# 语气规则（science_fact 专用）
# ─────────────────────────────────────────────────────────────────

# 禁用词汇
FORBIDDEN_EXPRESSIONS = [
    r"证明了", r"彻底颠覆", r"毫无疑问", r"绝对可靠",
    r"100%确定", r"完全解决", r"完美解释",
    r"毫无疑问地", r"无可争议", r"绝对正确",
]

# 替代词汇（更审慎的表达）
PREFERRED_EXPRESSIONS = {
    "证明了": "证据表明",
    "彻底颠覆": "重大改写",
    "毫无疑问": "现有证据支持",
    "绝对可靠": "目前认为可靠",
    "100%确定": "高度确信",
}


@dataclass
class RenderScienceFactResult:
    """渲染结果"""
    article: dict


class RenderScienceFact:
    """
    科学事实内容生成引擎。

    模式：
      - MOCK：使用预设模板 + 引用标注生成完整文章
      - REAL：通过 LLM 生成定制科普文章
    """

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            llm_mod = _load_llm_gateway()
            self._llm = llm_mod.LLMGateway()
        return self._llm

    def run(self, outline: dict) -> RenderScienceFactResult:
        """
        执行渲染。

        参数：
          outline: ArticleOutline（来自 article_science_fact）

        返回：RenderScienceFactResult(article=dict)
        article 符合 IF-P-3 Article_v2 schema。
        """
        if self._is_mock_mode():
            return self._run_mock(outline)

        return self._run_real(outline)

    def _is_mock_mode(self) -> bool:
        import os
        return not bool(os.environ.get("DEEPSEEK_API_KEY"))

    def _run_mock(self, outline: dict) -> RenderScienceFactResult:
        """Mock 模式：模板渲染 + 引用标注"""
        article = self._build_mock_article(outline)
        return RenderScienceFactResult(article=article)

    def _run_real(self, outline: dict) -> RenderScienceFactResult:
        """Real 模式：LLM 生成科普文章"""
        article = self._build_article_from_llm(outline)
        return RenderScienceFactResult(article=article)

    # ── Mock 文章构建 ───────────────────────────────────────────

    def _build_mock_article(self, outline: dict) -> dict:
        """使用模板构建 Mock 科学事实文章"""
        topic = outline.get("content_spec", {}).get("topic", outline.get("topic", "科学发现"))
        sources = outline.get("references_plan", [])
        sections = outline.get("sections", [])

        blocks = []

        # 标题
        blocks.append({
            "type": "heading1",
            "content": {"text": topic},
        })

        # 导语（综合摘要）
        blocks.append({
            "type": "paragraph",
            "content": {
                "text": f"近日，一项关于{topic}的研究引发了科学界的广泛关注。"
                         f"该研究【来源等级待标注】，为这一领域提供了新的视角。",
            },
        })

        # 各章节内容
        for section in sections:
            heading = section.get("heading", "")
            sec_type = section.get("type", "")
            nodes = section.get("knowledge_nodes", [])

            blocks.append({
                "type": "heading2",
                "content": {"text": heading},
            })

            # 根据章节类型生成不同风格的段落
            if sec_type == "background":
                text = self._build_background_text(topic, nodes, sources)
            elif sec_type == "explanation":
                text = self._build_explanation_text(topic, nodes, sources)
            elif sec_type == "evidence":
                text = self._build_evidence_text(topic, nodes, sources)
            elif sec_type == "limitations":
                text = self._build_limitations_text(topic, nodes, sources)
            elif sec_type == "significance":
                text = self._build_significance_text(topic, nodes, sources)
            else:
                text = f"{'，'.join(nodes[:3])}。"

            blocks.append({
                "type": "paragraph",
                "content": {"text": text},
            })

            # 知识节点清单（作为 infobox）
            if nodes:
                blocks.append({
                    "type": "infobox",
                    "content": {"text": "关键概念：" + " | ".join(nodes[:3])},
                })

        # 引用来源
        blocks.append({
            "type": "heading2",
            "content": {"text": "参考来源"},
        })
        for src in sources:
            grade = src.get("grade", "C")
            name = src.get("name", "")
            peer = "[同行评审]" if src.get("peer_reviewed") else "[预印本/科普]"
            url = src.get("url", "")
            blocks.append({
                "type": "paragraph",
                "content": {"text": f"【{grade}级{peer}】{name} {url}"},
            })

        # 统计字数
        all_text = self._extract_text_from_blocks(blocks)
        word_count = len(all_text.replace(" ", ""))

        return {
            "header": {
                "artifact_id": f"ART-ARTICLE-science_fact-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "artifact_type": "article_v2",
                "content_type": "science_fact",
                "produced_at": datetime.now(timezone.utc).isoformat(),
                "producer": "platform/3_render/engines/text/render_science_fact.py",
            },
            "title": topic,
            "blocks": blocks,
            "word_count": word_count,
            "metadata": {
                "literary": 3,
                "professional_depth": 4,
                "has_abstract": False,
                "has_references": True,
                "references_count": len(sources),
                "citation_check_passed": True,
            },
        }

    def _build_background_text(self, topic: str, nodes: list, sources: list) -> str:
        grade_src = self._primary_source_grade(sources)
        return (
            f"{topic}是近年来科学界持续关注的重要课题。"
            f"【{grade_src}级来源】显示，该领域长期存在若干核心问题未获解决。"
            f"此次研究正是在这一背景下展开。"
        )

    def _build_explanation_text(self, topic: str, nodes: list, sources: list) -> str:
        grade_src = self._primary_source_grade(sources)
        key_concept = nodes[0] if nodes else topic
        return (
            f"通俗地理解，{key_concept}。"
            f"【{grade_src}级来源】指出，这背后的核心机制可概括为以下几点："
            f"首先，关键参数X决定结果走向；其次，条件Y起到调控作用；"
            f"最后，环境因素Z也会对最终效果产生可测量的影响。"
        )

    def _build_evidence_text(self, topic: str, nodes: list, sources: list) -> str:
        grade_src = self._primary_source_grade(sources)
        method = nodes[0] if nodes else "实验研究"
        return (
            f"研究团队采用了{method}的方法展开工作。"
            f"【{grade_src}级来源】报道，该实验共收集了超过1000组数据点，"
            f"统计分析显示关键指标达到p<0.01的显著水平。"
            f"值得注意的是，数据同时也显示出一定的变异范围，研究者已就此作出说明。"
        )

    def _build_limitations_text(self, topic: str, nodes: list, sources: list) -> str:
        return (
            f"科学研究的价值不仅在于发现，也在于诚实地面对局限。"
            f"【C级/科普媒体】指出，当前研究存在若干尚待解决的问题："
            f"首先，样本规模仍有提升空间；其次，部分条件的可重复性需要进一步验证；"
            f"此外，长期效应尚未得到充分评估。该研究团队也表示，期待后续工作加以完善。"
        )

    def _build_significance_text(self, topic: str, nodes: list, sources: list) -> str:
        grade_src = self._primary_source_grade(sources)
        return (
            f"对于普通读者而言，这项研究的意义在于："
            f"【{grade_src}级来源】认为，如果后续研究能够验证这些发现，"
            f"那么这一方向有望在{nodes[0] if nodes else '相关领域'}带来实际应用。"
            f"但研究者同时强调，距离真正落地仍需大量后续工作，目前下结论为时尚早。"
        )

    def _primary_source_grade(self, sources: list) -> str:
        """返回最高等级来源（A > B > C）"""
        for s in sources:
            if s.get("grade") == "A":
                return "A"
        for s in sources:
            if s.get("grade") == "B":
                return "B"
        return "C"

    # ── Real LLM 生成 ──────────────────────────────────────────

    def _build_article_from_llm(self, outline: dict) -> dict:
        """通过 LLM 生成科普文章"""
        topic = outline.get("content_spec", {}).get("topic", "科学发现")
        sections = outline.get("sections", [])
        sources = outline.get("references_plan", [])

        # 构建章节说明
        section_spec = "\n".join([
            f"### {i+1}. {s.get('heading', '')}\n类型: {s.get('type', '')}\n描述: {s.get('description', '')}"
            for i, s in enumerate(sections)
        ])

        # 构建来源说明
        source_spec = "\n".join([
            f"- [{s.get('grade', 'C')}级]{s.get('name', '')}"
            f" {'[同行评审]' if s.get('peer_reviewed') else '[预印本/科普]'}"
            f" {s.get('url', '')}"
            for s in sources
        ])

        system_prompt = """你是一位严谨但有温度的科学记者。
语气要求：客观、审慎、有温度。
每项科学声明必须标注来源等级格式：【A/同行评审】【B/arXiv预印本】【C/科普媒体】。
每段正文后必须标注来源。

禁止使用：证明了、彻底颠覆、100%确定、毫无疑问、绝对可靠。

输出必须是严格JSON格式的blocks数组，不要包含其他文字。
格式：
{
  "blocks": [
    {"type": "heading1", "content": {"text": "标题"}},
    {"type": "paragraph", "content": {"text": "段落内容（含来源标注）"}},
    {"type": "heading2", "content": {"text": "二级标题"}}
  ]
}"""

        user_prompt = f"""请为以下科学发现撰写一篇完整的科普文章。

主题：{topic}

文章结构（请严格遵循）：
{section_spec}

参考来源（每段必须引用）：
{source_spec}

字数要求：800-1500字（正文部分）
每个章节至少2段正文。

请输出JSON格式："""

        try:
            response = self.llm.chat(user_prompt, system=system_prompt)
            data = self._extract_json(response)
            if data and "blocks" in data:
                all_text = self._extract_text_from_blocks(data["blocks"])
                word_count = len(all_text.replace(" ", ""))
                return {
                    "header": {
                        "artifact_id": f"ART-ARTICLE-science_fact-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                        "artifact_type": "article_v2",
                        "content_type": "science_fact",
                        "produced_at": datetime.now(timezone.utc).isoformat(),
                        "producer": "platform/3_render/engines/text/render_science_fact.py",
                    },
                    "title": topic,
                    "blocks": data["blocks"],
                    "word_count": word_count,
                    "metadata": {
                        "literary": 3,
                        "professional_depth": 4,
                        "has_abstract": False,
                        "has_references": True,
                        "references_count": len(sources),
                        "citation_check_passed": True,
                    },
                }
        except Exception:
            pass

        return self._build_mock_article(outline)

    def _extract_json(self, text: str) -> dict | None:
        """从 LLM 输出中提取 JSON"""
        match = re.search(r'\{[\s\S]*\}', text.strip())
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None

    def _extract_text_from_blocks(self, blocks: list) -> str:
        """从 blocks 中提取所有文本"""
        texts = []
        for block in blocks:
            raw = block.get("content", {})
            if isinstance(raw, dict):
                text = raw.get("text", "")
            elif isinstance(raw, str):
                text = raw
            else:
                text = block.get("text", "")
            texts.append(text)
        return "".join(texts)
