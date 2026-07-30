# -*- coding: utf-8 -*-
"""
render_opinion.py — oped_argument IF-P-3：观点评论渲染引擎
===========================================================

功能：
  1. 将文章结构（ArticleOpinionResult）渲染为完整 Markdown 文章
  2. 语气规范：鲜明立场、有理有据、不人身攻击
  3. 引用格式：【A】政策文件/学术 /【B】媒体报道 /【C】网络舆论
  4. 品牌规范：assertive（坚定自信但不傲慢）

语气规范：
  ✅ 允许：第一人称"笔者认为"、修辞问句、反问句
  ✅ 允许：点名引用数据和使用者（但需措辞中立）
  ❌ 禁止：人身攻击、情绪化泄愤、阴谋论断言
  ❌ 禁止："毫无疑问"、"绝对"、"必然"等绝对化表达

使用方式：
  renderer = RenderOpinion()
  result = renderer.run(article_result, brand_voice="assertive")
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[4]  # → platform/ → repo root
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
class RenderOpinionRequest:
    """渲染请求"""
    title: str
    sections: dict          # article_opinion.py 的 sections 结构
    perspective: str = "中立"
    brand_voice: str = "assertive"  # "assertive" / "scholarly" / "accessible"
    max_words: int = 2000    # 最大字数限制


@dataclass
class RenderOpinionResult:
    """渲染结果"""
    content_id: str
    markdown: str            # 完整 Markdown 内容
    word_count: int          # 实际字数
    sections_summary: dict   # 各节字数分布
    citations: list[str]     # 引用列表
    tone_check: dict         # 语气检查结果
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "content_id": self.content_id,
            "markdown": self.markdown,
            "word_count": self.word_count,
            "sections_summary": self.sections_summary,
            "citations": self.citations,
            "tone_check": self.tone_check,
            "timestamp": self.timestamp,
        }


# ─────────────────────────────────────────────────────────────────
# 语气规范
# ─────────────────────────────────────────────────────────────────

TONE_RULES = {
    "assertive": {
        "allowed": ["笔者认为", "本文主张", "值得深思", "这一选择关乎"],
        "banned": ["毫无疑问", "绝对", "必然如此", "蠢", "坏", "恶", "汉奸", "卖国"],
        "structure": "七段式（钩子→论点→支撑→对立→反驳→结论→CTA）",
    },
    "scholarly": {
        "allowed": ["研究表明", "学术共识认为", "从X理论视角看"],
        "banned": ["毫无疑问", "绝对", "必然", "笔者认为"],
        "structure": "学术论证体（问题→文献→方法→发现→讨论）",
    },
    "accessible": {
        "allowed": ["简单来说", "举个例子", "就像", "打个比方"],
        "banned": ["毫无疑问", "绝对", "必然"],
        "structure": "通俗对话体（故事切入→逐步展开→回归日常）",
    },
}


# ─────────────────────────────────────────────────────────────────
# 核心类
# ─────────────────────────────────────────────────────────────────

class RenderOpinion:
    """观点评论渲染引擎"""

    def run(self, article_result, brand_voice: str = "assertive") -> RenderOpinionResult:
        """
        执行渲染
        流程：
          1. 验证 article_result 结构
          2. 渲染 Markdown（含标题、署名、七节内容）
          3. 语气检查
          4. 汇总引用
        """
        from datetime import datetime, timezone

        content_id = f"RO_{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.now(timezone.utc).isoformat()

        # 提取数据
        if hasattr(article_result, "to_dict"):
            data = article_result.to_dict()
        else:
            data = article_result

        title = data.get("title", "无题")
        sections = data.get("sections", {})
        perspective = data.get("perspective", "中立")

        # 渲染 Markdown
        if not _has_llm_key():
            markdown, sections_summary = self._render_mock(title, sections, perspective)
        else:
            markdown, sections_summary = self._render_llm(title, sections, perspective, brand_voice)

        # 语气检查
        tone_check = self._check_tone(markdown, brand_voice)

        # 提取引用
        citations = self._extract_citations(sections)

        # 字数
        word_count = len(markdown) // 2  # 中文字符粗估

        return RenderOpinionResult(
            content_id=content_id,
            markdown=markdown,
            word_count=word_count,
            sections_summary=sections_summary,
            citations=citations,
            tone_check=tone_check,
            timestamp=ts,
        )

    # ──────────────────────────── 渲染方法 ────────────────────────────

    def _render_mock(
        self, title: str, sections: dict, perspective: str
    ) -> tuple[str, dict]:
        """Mock 渲染：基于 sections 字典组装 Markdown"""
        lines = []

        # 标题
        lines.append(f"# {title}\n")
        lines.append(f"*立场：{perspective} | 类型：观点评论*\n")
        lines.append("---\n")

        # 各节内容
        section_order = ["hook", "thesis", "support", "opposing", "refutation", "conclusion", "cta"]
        sections_summary = {}

        for key in section_order:
            sec = sections.get(key, {})
            if not sec:
                continue

            name = sec.get("name", key)
            content = sec.get("content", "")
            sources = sec.get("sources", [])
            word_count = sec.get("word_count", len(content) // 2)
            sections_summary[name] = word_count

            lines.append(f"## {name}\n")
            lines.append(f"{content}\n")

            # 引用来源
            if sources:
                lines.append("*参考来源：*")
                for src in sources[:2]:
                    if isinstance(src, dict):
                        grade = src.get("grade", "B")
                        name_s = src.get("name", "来源")
                        url = src.get("url", "")
                    else:
                        grade = getattr(src, "grade", "B")
                        name_s = getattr(src, "name", "来源")
                        url = getattr(src, "url", "")
                    grade_label = f"【{grade}】"
                    link = f"[{name_s}]({url})" if url else name_s
                    lines.append(f"{grade_label} {link}")
                lines.append("")

        # 结尾
        lines.append("---\n")
        lines.append(f"*本文为观点评论，不代表平台立场。*\n")
        lines.append(f"*© SPDT-005 Media Content · 观点评论 · {perspective}*\n")

        return "\n".join(lines), sections_summary

    def _render_llm(
        self, title: str, sections: dict, perspective: str, brand_voice: str
    ) -> tuple[str, dict]:
        """LLM 渲染：生成高质量 Markdown"""
        llm = _load_llm_gateway()

        tone_config = TONE_RULES.get(brand_voice, TONE_RULES["assertive"])
        banned_str = "、".join(tone_config["banned"])

        sections_str = "\n".join([
            f"## {sec.get('name', k)}\n{sec.get('content', '')}"
            for k, sec in sections.items()
        ])

        prompt = (
            f"请将以下评论文章大纲渲染为完整、流畅的 Markdown 格式。\n\n"
            f"标题：{title}\n立场：{perspective}\n品牌语气：{brand_voice}\n\n"
            f"语气规范：\n"
            f"  允许使用：{'；'.join(tone_config['allowed'][:3])}\n"
            f"  禁止使用：{banned_str} 等绝对化或情绪化表达\n\n"
            f"结构要求：七段式（钩子→论点→支撑→对立→反驳→结论→CTA）\n\n"
            f"文章大纲：\n{sections_str}\n\n"
            f"输出要求：\n"
            f"1. 标题使用 H1，章节使用 H2\n"
            f"2. 引用来源格式：【A】来源名 或 【B】来源名\n"
            f"3. 结尾加分割线 --- 和平台免责条款\n"
            f"4. 全文应流畅、说服力强，不低于1200字\n"
            f"5. 只输出 Markdown 内容，不要额外解释"
        )

        try:
            response = llm.call_deepseek(prompt, model="deepseek-chat")
            sections_summary = {sec.get("name", k): sec.get("word_count", 0) for k, sec in sections.items()}
            return response, sections_summary
        except Exception:
            return self._render_mock(title, sections, perspective)

    # ──────────────────────────── 质量检查 ────────────────────────────

    def _check_tone(self, markdown: str, brand_voice: str) -> dict:
        """语气检查：检测绝对化表达和禁止词"""
        tone_config = TONE_RULES.get(brand_voice, TONE_RULES["assertive"])
        banned = tone_config["banned"]

        violations = []
        for word in banned:
            if word in markdown:
                violations.append(f"发现禁止词：{word}")

        # 检查绝对化表达
        absolute_patterns = [
            r"毫无疑问", r"绝对[地是]", r"必然如此", r"毫无疑问地",
            r"100%确定", r"毫无争议", r"举世公认",
        ]
        import re
        for pattern in absolute_patterns:
            if re.search(pattern, markdown):
                violations.append(f"发现绝对化表达：{pattern}")

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "brand_voice": brand_voice,
        }

    def _extract_citations(self, sections: dict) -> list[str]:
        """提取所有引用来源"""
        citations = []
        seen = set()
        for sec in sections.values():
            for src in sec.get("sources", []):
                if isinstance(src, dict):
                    name = src.get("name", "")
                    grade = src.get("grade", "B")
                else:
                    name = getattr(src, "name", "")
                    grade = getattr(src, "grade", "B")
                key = f"{grade}:{name}"
                if name and key not in seen:
                    seen.add(key)
                    citations.append(f"【{grade}】{name}")
        return citations


# ─────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────

def _has_llm_key() -> bool:
    import os
    return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())


# ─────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────

def run(article_result, brand_voice: str = "assertive", **kwargs) -> RenderOpinionResult:
    """
    便捷入口：render_opinion.run(article_result, brand_voice="assertive")
    等价于 RenderOpinion().run(article_result, brand_voice=brand_voice)
    """
    return RenderOpinion().run(article_result, brand_voice=brand_voice)
