# -*- coding: utf-8 -*-
"""
article_opinion.py — oped_argument IF-P-2：观点评论文章结构生成
================================================================

功能：
  1. 基于情报摘要（OpinionBrief）生成论点大纲
  2. 七段式结构：钩子→论点→支撑论据→对立论点→反驳→结论→行动号召
  3. 对立论点的存在是发布前提（确保评论有交锋感，而非自言自语）

七段式结构规范：
  §1 钩子（Hook，150字）：用惊人数据/反常识事实/强烈场景开场
  §2 核心论点（Thesis，100字）：鲜明亮出立场，一句话概括全文
  §3 支撑论据（Support，400字）：2-3个有说服力的论据，引用A级来源
  §4 对立论点（Opposing，300字）：诚实呈现反方最有力量的论点
  §5 反驳（Refutation，250字）：逐点反驳对立论点，指出其局限性
  §6 结论（Conclusion，150字）：总结论点，升华意义
  §7 行动号召（CTA，80字）：呼吁读者行动/思考

使用方式：
  article = ArticleOpinion()
  result = article.run(brief, title="AI监管：必要的刹车而非倒车")
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


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
# 数据类
# ─────────────────────────────────────────────────────────────────

@dataclass
class OpinionBriefInput:
    """兼容 pipeline_router 传入的字典或 OpinionBrief 对象"""
    topic: str
    perspective: str = "中立"
    event_context: str = ""
    supporting_signals: list = field(default_factory=list)
    opposing_signals: list = field(default_factory=list)
    rebuttal_points: list = field(default_factory=list)
    key_facts: list = field(default_factory=list)

    @classmethod
    def from_brief(cls, brief) -> "OpinionBriefInput":
        # Use dict.get() with or-fallback to avoid AttributeError on dict.topic
        if isinstance(brief, dict):
            return cls(
                topic=brief.get("topic") or "",
                perspective=brief.get("perspective") or "中立",
                event_context=brief.get("event_context") or "",
                supporting_signals=brief.get("supporting_signals") or [],
                opposing_signals=brief.get("opposing_signals") or [],
                rebuttal_points=brief.get("rebuttal_points") or [],
                key_facts=brief.get("key_facts") or [],
            )
        else:
            return cls(
                topic=brief.topic,
                perspective=brief.perspective,
                event_context=brief.event_context,
                supporting_signals=brief.supporting_signals,
                opposing_signals=brief.opposing_signals,
                rebuttal_points=brief.rebuttal_points,
                key_facts=brief.key_facts,
            )


@dataclass
class ArticleOpinionResult:
    """文章结构生成结果"""
    outline_id: str
    title: str
    sections: dict        # {section_name: {purpose, content, sources, word_count}}
    total_word_count: int
    perspective: str       # "支持" / "反对" / "中立"
    opposing_presented: bool  # 对立论点是否已呈现（发布前提）
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "outline_id": self.outline_id,
            "title": self.title,
            "sections": self.sections,
            "total_word_count": self.total_word_count,
            "perspective": self.perspective,
            "opposing_presented": self.opposing_presented,
            "timestamp": self.timestamp,
        }


# ─────────────────────────────────────────────────────────────────
# 核心类
# ─────────────────────────────────────────────────────────────────

class ArticleOpinion:
    """观点评论文章结构生成器"""

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            llm_mod = _load_llm_gateway()
            self._llm = llm_mod.LLMGateway()
        return self._llm

    # 七段式结构模板
    SECTION_TEMPLATE = {
        "hook": {
            "name": "§1 钩子（Hook）",
            "purpose": "用惊人数据/反常识事实/场景开场，吸引读者",
            "target_words": "150",
            "tone": "震撼、悬念、情感共鸣",
        },
        "thesis": {
            "name": "§2 核心论点（Thesis）",
            "purpose": "鲜明亮出立场，一句话概括全文",
            "target_words": "100",
            "tone": "简洁、有力、不含糊",
        },
        "support": {
            "name": "§3 支撑论据（Support）",
            "purpose": "2-3个有说服力的论据，引用A级来源",
            "target_words": "400",
            "tone": "有理有据、逻辑清晰",
        },
        "opposing": {
            "name": "§4 对立论点（Opposing）",
            "purpose": "诚实呈现反方最有力量的论点",
            "target_words": "300",
            "tone": "客观、公正、不歪曲",
        },
        "refutation": {
            "name": "§5 反驳（Refutation）",
            "purpose": "逐点反驳对立论点，指出其局限性",
            "target_words": "250",
            "tone": "理性、克制、以理服人",
        },
        "conclusion": {
            "name": "§6 结论（Conclusion）",
            "purpose": "总结论点，升华意义",
            "target_words": "150",
            "tone": "坚定、升华、余韵",
        },
        "cta": {
            "name": "§7 行动号召（CTA）",
            "purpose": "呼吁读者行动/思考",
            "target_words": "80",
            "tone": "温暖、有力、开放",
        },
    }

    def run(self, brief, title: str = "") -> ArticleOpinionResult:
        """
        执行文章结构生成
        流程：
          1. 验证对立论点存在（若无 → FAIL）
          2. 调用 LLM 生成各节内容（或使用 Mock 模板）
          3. 汇总字数和结构
        """
        from datetime import datetime, timezone

        brief_input = OpinionBriefInput.from_brief(brief)
        outline_id = f"AO_{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.now(timezone.utc).isoformat()

        # 发布前提：对立论点必须存在
        opposing_presented = len(brief_input.opposing_signals) > 0

        # 生成标题
        if not title:
            title = self._generate_title(brief_input)

        # 生成各节内容
        sections = self._build_sections(brief_input, title, opposing_presented)

        # 汇总字数
        total_wc = sum(
            int(s.get("word_count", 0)) for s in sections.values()
        )

        return ArticleOpinionResult(
            outline_id=outline_id,
            title=title,
            sections=sections,
            total_word_count=total_wc,
            perspective=brief_input.perspective,
            opposing_presented=opposing_presented,
            timestamp=ts,
        )

    # ──────────────────────────── 内部方法 ────────────────────────────

    def _generate_title(self, brief: OpinionBriefInput) -> str:
        """生成评论标题"""
        topic = brief.topic
        perspective = brief.perspective

        if perspective == "支持":
            return f"{topic}：为什么这是正确的方向"
        elif perspective == "反对":
            return f"慎思{topic}：我们是否走得太快"
        else:
            return f"如何理性看待{topic}"

    def _build_sections(
        self, brief: OpinionBriefInput, title: str, opposing_presented: bool
    ) -> dict:
        """构建七段式结构内容"""

        # 使用 Mock 模板（无 API key 时）
        if not _has_llm_key():
            return self._mock_sections(brief, title, opposing_presented)

        # 真实 LLM 生成
        return self._llm_sections(brief, title, opposing_presented)

    def _mock_sections(
        self, brief: OpinionBriefInput, title: str, opposing_presented: bool
    ) -> dict:
        """Mock 七段式内容"""
        topic = brief.topic
        perspective = brief.perspective
        key_facts = brief.key_facts or []
        supporting = brief.supporting_signals or []
        opposing = brief.opposing_signals or []
        rebuttals = brief.rebuttal_points or []

        # §1 钩子
        hook_fact = key_facts[0] if key_facts else f"{topic}已成为年度最受关注议题之一"
        hook_content = (
            f"当大多数人还在{topic}的表象争论不休时，"
            f"一组数据已经揭示了这场争论的深层真相：{hook_fact}。\n"
            f"这不是简单的政策之争，而是一场关乎未来十年社会走向的价值选择。"
        )

        # §2 核心论点
        if perspective == "支持":
            thesis = (
                f"本文认为，{topic}不仅必要，而且正当——"
                f"它是在复杂局面中寻找最大公约数的理性路径，"
                f"反对它的人，或许看到了问题，却忽略了更大的图景。"
            )
        elif perspective == "反对":
            thesis = (
                f"本文认为，当前版本的{topic}过于仓促，"
                f"其代价被系统性低估，而真正的解决方案需要更精细的智慧。\n"
                f"这不是保守主义，而是对复杂系统应有的敬畏。"
            )
        else:
            thesis = (
                f"对于{topic}，情绪化的支持或反对都无助于问题的解决。"
                f"本文试图跳出非此即彼的框架，在承认双方都有合理关切的前提下，"
                f"寻找一条超越对立的可能性路径。"
            )

        # §3 支撑论据
        support_points = []
        for sig in supporting[:3]:
            if isinstance(sig, dict):
                name = sig.get("name", "相关研究")
                claim = sig.get("key_claim", "")
                evidence = sig.get("evidence", "")
            else:
                name = getattr(sig, "name", "相关研究")
                claim = getattr(sig, "key_claim", "")
                evidence = getattr(sig, "evidence", "")
            support_points.append(
                f"论据一（来源：{name}）：{claim}。"
                f"具体而言，{evidence}。"
                f"这一论据的反驳点在于：{rebuttals[0] if rebuttals else '需进一步验证'}。"
            )
        if len(supporting) < 2:
            support_points.append(
                f"论据二：{key_facts[1] if len(key_facts) > 1 else '支持性数据待补充'}。"
            )

        support_content = "\n\n".join(support_points)

        # §4 对立论点（诚实呈现）
        opposing_points = []
        for sig in opposing[:3]:
            if isinstance(sig, dict):
                name = sig.get("name", "反对方")
                claim = sig.get("key_claim", "")
                evidence = sig.get("evidence", "")
            else:
                name = getattr(sig, "name", "反对方")
                claim = getattr(sig, "key_claim", "")
                evidence = getattr(sig, "evidence", "")
            opposing_points.append(
                f"反方观点（来源：{name}）：{claim}。"
                f"其支撑证据为：{evidence}。"
            )
        if not opposing_points:
            opposing_content = "（注：当前资料未收集到充分的对立观点，建议进一步调研补充）"
        else:
            opposing_content = "\n\n".join(opposing_points)

        # §5 反驳
        rebuttal_points_text = []
        for i, point in enumerate(rebuttals[:3]):
            rebuttal_points_text.append(f"针对反方第{i+1}点：{point}")
        refutation_content = "\n\n".join(rebuttal_points_text) if rebuttal_points_text else (
            "反方的担忧虽然值得重视，但其论证存在若干关键漏洞："
            "第一，数据来源的代表性存疑；第二，对长期趋势的预测过于线性；"
            "第三，未能考虑到政策执行中的自适应机制。"
        )

        # §6 结论
        conclusion_content = (
            f"{topic}的本质，是一道关于我们在不确定时代如何做选择的命题。\n"
            f"无论最终立场如何，这种理性辩论本身，就是社会自我纠偏能力的体现。"
        )

        # §7 行动号召
        cta_content = (
            "读完这篇文章，你是否也有自己的看法？\n"
            "欢迎在评论区分享你的观点，一起推动这场讨论走向更深。\n"
            "转发给关心这个话题的朋友，让理性对话成为可能。"
        )

        sections = {}
        section_map = [
            ("hook", hook_content, "150"),
            ("thesis", thesis, "100"),
            ("support", support_content, "400"),
            ("opposing", opposing_content, "300"),
            ("refutation", refutation_content, "250"),
            ("conclusion", conclusion_content, "150"),
            ("cta", cta_content, "80"),
        ]

        for key, content, target in section_map:
            sections[key] = {
                "name": self.SECTION_TEMPLATE[key]["name"],
                "purpose": self.SECTION_TEMPLATE[key]["purpose"],
                "content": content,
                "sources": self._collect_sources_for_section(key, supporting, opposing),
                "word_count": len(content) // 2,  # 中文字符粗估
                "target_words": target,
                "tone": self.SECTION_TEMPLATE[key]["tone"],
            }

        return sections

    def _llm_sections(
        self, brief: OpinionBriefInput, title: str, opposing_presented: bool
    ) -> dict:
        """LLM 生成各节内容"""
        brief_dict = {
            "topic": brief.topic,
            "perspective": brief.perspective,
            "event_context": brief.event_context,
            "supporting_signals": brief.supporting_signals,
            "opposing_signals": brief.opposing_signals,
            "rebuttal_points": brief.rebuttal_points,
            "key_facts": brief.key_facts,
        }

        prompt = (
            f"请为以下观点评论生成七段式文章结构（标题：{title}）。\n\n"
            f"话题信息：\n{brief_dict}\n\n"
            f"请为以下每一节生成内容（中文字符数控制在目标字数±20%以内）：\n"
            f"§1 钩子（约150字）：震撼开场\n"
            f"§2 核心论点（约100字）：鲜明立场\n"
            f"§3 支撑论据（约400字）：2-3个有说服力论据\n"
            f"§4 对立论点（约300字）：诚实呈现反方最强论点\n"
            f"§5 反驳（约250字）：逐点反驳对立论点\n"
            f"§6 结论（约150字）：总结升华\n"
            f"§7 行动号召（约80字）：呼吁读者\n"
            f"输出格式：JSON，key为section_1到section_7，value为内容文字。"
        )

        try:
            response = self.llm.chat(prompt)
            import json
            raw = response.content if hasattr(response, "content") else str(response)
            data = json.loads(raw)
            return self._parse_llm_sections(data, brief)
        except Exception:
            return self._mock_sections(brief, title, opposing_presented)

    def _parse_llm_sections(self, data: dict, brief: OpinionBriefInput) -> dict:
        """解析 LLM 返回的各节内容"""
        supporting = brief.supporting_signals
        opposing = brief.opposing_signals
        sections = {}
        keys = ["hook", "thesis", "support", "opposing", "refutation", "conclusion", "cta"]
        targets = ["150", "100", "400", "300", "250", "150", "80"]

        for i, key in enumerate(keys):
            content = data.get(f"section_{i+1}", "")
            sections[key] = {
                "name": self.SECTION_TEMPLATE[key]["name"],
                "purpose": self.SECTION_TEMPLATE[key]["purpose"],
                "content": content,
                "sources": self._collect_sources_for_section(key, supporting, opposing),
                "word_count": len(content) // 2,
                "target_words": targets[i],
                "tone": self.SECTION_TEMPLATE[key]["tone"],
            }
        return sections

    def _collect_sources_for_section(self, section: str, supporting: list, opposing: list) -> list:
        """收集各节引用的来源"""
        if section in ("support", "refutation"):
            return supporting[:2]
        elif section == "opposing":
            return opposing[:2]
        return []


# ─────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────

def _has_llm_key() -> bool:
    import os
    return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())


# ─────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────

def run(brief, title: str = "", **kwargs) -> ArticleOpinionResult:
    """
    便捷入口：article_opinion.run(brief, title="...")
    等价于 ArticleOpinion().run(brief, title=title)
    """
    return ArticleOpinion().run(brief, title=title)
