"""
progressive_guide/book_design.py
================================
全书设计方案生成器（Phase 1 核心新模块）

功能：
  1. 定义 BookScheme / BookDesign 数据结构
  2. BookDesignGenerator：根据用户结构化输入，LLM 生成 3-4 套差异化的全书设计方案
  3. 每套方案含：全书主线 + 完整章节大纲 + 张力曲线 + 核心取材 + 文风调性

数据结构：
  BookScheme     — 单套全书设计方案
  BookDesign    — 包含多套方案的完整设计结果
  ChapterDesign — 方案中单个章节的详情
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# 数据结构
# ════════════════════════════════════════════════════════════════

@dataclass
class ChapterDesign:
    """方案中单个章节的详细信息"""
    chapter: int              # 章节序号（从 1 开始）
    title: str                # 章节标题
    subtitle: str             # 副标题/一句话概括
    chapter_arc: str          # 本章叙事弧（20-30字）
    tension_level: float       # 张力值 0.0~1.0
    tension_label: str        # 张力标签（如"开篇引入""高潮"）
    key_events: list[str]     # 本章核心事件（2-3个）
    key_figures: list[str]    # 本章核心人物（2-3个）
    style_modulation: str     # 本章文风调性描述（20字）
    word_target: int          # 目标字数
    part: int | None = None   # 所属部数（长篇时使用）
    part_title: str = ""      # 所属部的标题

    def to_dict(self) -> dict:
        d = {
            "chapter": self.chapter,
            "title": self.title,
            "subtitle": self.subtitle,
            "chapter_arc": self.chapter_arc,
            "tension_level": self.tension_level,
            "tension_label": self.tension_label,
            "key_events": self.key_events,
            "key_figures": self.key_figures,
            "style_modulation": self.style_modulation,
            "word_target": self.word_target,
        }
        if self.part is not None:
            d["part"] = self.part
            d["part_title"] = self.part_title
        return d

    @classmethod
    def from_dict(cls, d: dict) -> ChapterDesign:
        return cls(
            chapter=int(d.get("chapter", 1)),
            title=str(d.get("title", "")),
            subtitle=str(d.get("subtitle", "")),
            chapter_arc=str(d.get("chapter_arc", "")),
            tension_level=float(d.get("tension_level", 0.5)),
            tension_label=str(d.get("tension_label", "")),
            key_events=list(d.get("key_events", [])),
            key_figures=list(d.get("key_figures", [])),
            style_modulation=str(d.get("style_modulation", "")),
            word_target=int(d.get("word_target", 800)),
            part=int(d["part"]) if d.get("part") is not None else None,
            part_title=str(d.get("part_title", "")),
        )


@dataclass
class BookScheme:
    """
    单套全书设计方案

    差异化维度：
      - structure_type：章节组织方式（线性/双线/主题式/地理式）
      - perspective：叙事视角（主角/群像/旁观者/历史纪录片）
      - main_arc：全书叙事主线一句话概括
      - focus_angle：切入角度一句话概括
    """
    scheme_id: str            # 方案编号（A/B/C/D）
    scheme_title: str         # 方案标题（如"线性叙事：苏轼的心灵史"）
    structure_type: str       # 章节组织方式
    perspective: str          # 叙事视角
    main_arc: str             # 全书主线（60字以内）
    focus_angle: str           # 切入角度（20字以内）
    chapters: list[ChapterDesign] = field(default_factory=list)
    tension_arc: list[float] = field(default_factory=list)  # 全书张力曲线
    core_materials: list[str] = field(default_factory=list)  # 核心取材清单
    style_tone: str = ""      # 整体文风调性描述
    highlight: str = ""       # 本方案最大亮点（20字）
    estimated_words: int = 0   # 预估总字数

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    def tension_bar_chart(self) -> str:
        """生成 ASCII 张力曲线图"""
        bars = []
        for i, ch in enumerate(self.chapters):
            bar_len = int(ch.tension_level * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            bars.append(
                f"  第{ch.chapter}章 [{bar}] {ch.tension_level:.0%}  {ch.tension_label}"
            )
        return "\n".join(bars)

    def summary_for_card(self) -> dict:
        """卡片展示所需的摘要信息"""
        return {
            "scheme_id": self.scheme_id,
            "title": self.scheme_title,
            "structure": self.structure_type,
            "perspective": self.perspective,
            "main_arc": self.main_arc,
            "focus_angle": self.focus_angle,
            "chapter_count": self.chapter_count,
            "estimated_words": self.estimated_words,
            "tension_arc": self.tension_arc,
            "highlight": self.highlight,
            "core_materials": self.core_materials[:5],
            "chapters_preview": [
                {"chapter": ch.chapter, "title": ch.title, "arc": ch.chapter_arc}
                for ch in self.chapters[:3]
            ],
        }

    def to_dict(self) -> dict:
        return {
            "scheme_id": self.scheme_id,
            "scheme_title": self.scheme_title,
            "structure_type": self.structure_type,
            "perspective": self.perspective,
            "main_arc": self.main_arc,
            "focus_angle": self.focus_angle,
            "chapters": [ch.to_dict() for ch in self.chapters],
            "tension_arc": self.tension_arc,
            "core_materials": self.core_materials,
            "style_tone": self.style_tone,
            "highlight": self.highlight,
            "estimated_words": self.estimated_words,
        }

    @classmethod
    def from_dict(cls, d: dict) -> BookScheme:
        chapters = [ChapterDesign.from_dict(c) for c in d.get("chapters", [])]
        return cls(
            scheme_id=str(d.get("scheme_id", "A")),
            scheme_title=str(d.get("scheme_title", "")),
            structure_type=str(d.get("structure_type", "")),
            perspective=str(d.get("perspective", "")),
            main_arc=str(d.get("main_arc", "")),
            focus_angle=str(d.get("focus_angle", "")),
            chapters=chapters,
            tension_arc=[float(x) for x in d.get("tension_arc", [])],
            core_materials=list(d.get("core_materials", [])),
            style_tone=str(d.get("style_tone", "")),
            highlight=str(d.get("highlight", "")),
            estimated_words=int(d.get("estimated_words", 0)),
        )


@dataclass
class BookDesign:
    """
    包含多套方案的完整设计结果
    """
    schemes: list[BookScheme] = field(default_factory=list)
    selected_scheme_id: Optional[str] = None   # 用户选中的方案编号
    user_input_ref: dict = field(default_factory=dict)  # 原始用户输入引用

    @property
    def selected_scheme(self) -> Optional[BookScheme]:
        if not self.selected_scheme_id:
            return None
        for s in self.schemes:
            if s.scheme_id == self.selected_scheme_id:
                return s
        return None

    def to_dict(self) -> dict:
        return {
            "schemes": [s.to_dict() for s in self.schemes],
            "selected_scheme_id": self.selected_scheme_id,
        }


# ════════════════════════════════════════════════════════════════
# 全书设计方案生成器
# ════════════════════════════════════════════════════════════════

SCHEME_STRUCTURE_TYPES = [
    "线性时间流（按历史时间顺序）",
    "双线并行（两条叙事线交替）",
    "主题式递进（按主题块组织）",
    "地理空间串联（按地点变换组织）",
    "倒叙开篇（从结局切入再回溯）",
]

SCHEME_PERSPECTIVES = [
    "主人公内心视角",
    "历史群像视角",
    "旁观者/见证人视角",
    "历史纪录片式全知视角",
    "人物对话推进式",
]


def _calc_chapters_and_parts(target_words: int) -> tuple[int, int | None, str]:
    """
    根据目标字数，计算章节数和是否需要分"部"。
    返回：(chapter_count, part_count_or_None, guidance_text)
    part_count_or_None：长篇（>30000字）时分部数，否则 None
    """
    if target_words <= 3000:
        chapters = 3
        parts = None
        guidance = f"建议 {chapters} 章（短篇），每章约 {target_words // chapters} 字"
    elif target_words <= 8000:
        chapters = max(4, target_words // 1500)   # ~5-6章
        parts = None
        guidance = f"建议 {chapters} 章（中篇），每章约 {target_words // chapters} 字"
    elif target_words <= 20000:
        chapters = max(5, target_words // 2000)   # ~7-10章，温和增长
        parts = None
        guidance = f"建议 {chapters} 章（中长篇），每章约 {target_words // chapters} 字"
    elif target_words <= 40000:
        chapters = max(6, target_words // 2500)   # ~10-16章，不再是 1800/章
        parts = 2
        guidance = (
            f"建议 {chapters} 章，分为 {parts} 部（每部 {chapters // parts} 章），"
            f"每章约 {target_words // chapters} 字"
        )
    else:
        chapters = max(8, target_words // 3000)   # 最多约 20-27 章
        parts = 3 if chapters > 18 else 2
        guidance = (
            f"建议 {chapters} 章，分为 {parts} 部（每部 {chapters // parts} 章），"
            f"每章约 {target_words // chapters} 字"
        )
    return chapters, parts, guidance


def build_book_design_prompt(user_input: dict, num_schemes: int = 3) -> str:
    """构建全书设计方案生成的 LLM prompt（稳定版，无嵌套 f-string，无 JS 注释）"""

    topic = user_input.get("chapter_title", "")
    desc = user_input.get("description", "")
    purpose = user_input.get("purpose", "一般通俗写作")
    ref_works = user_input.get("ref_works", "")
    target_words = user_input.get("target_length", 15000)
    characters = user_input.get("characters", [])
    themes = user_input.get("themes", [])

    chapters, parts, chapters_note = _calc_chapters_and_parts(target_words)
    ref_note = "对标作品：" + ref_works + "。" if ref_works else ""
    tension_arc_example = _tension_arc_template(chapters)
    word_per_chapter = max(800, target_words // chapters)

    # ── 无 JS 注释、无嵌套 f-string，用普通列表拼接 ─────────────
    lines = []

    # 任务说明
    lines.append("你是一位历史通俗作品策划师。用户想写一本关于【" + topic + "】的书。")
    lines.append("写作目的：" + purpose + "。" + ref_note)
    lines.append("目标字数：约 " + str(target_words) + " 字，" + chapters_note + "。")
    if characters:
        lines.append("核心人物：" + "、".join(characters))
    lines.append("")
    lines.append("请为上述主题生成 " + str(num_schemes) + " 套差异化的全书设计方案（编号：A、B、C...）。")
    lines.append("每套方案须在结构类型、叙事视角、切入角度上有明显差异。")
    lines.append("")

    # 输出格式要求（纯文字，无 JS 注释）
    lines.append("=== 输出格式 ===")
    lines.append("直接输出纯 JSON，无 markdown 代码块包裹，无任何注释。")
    lines.append("顶层结构：{\"schemes\":[...]}")
    lines.append("tension_arc 数组长度 = " + str(chapters) + "，值为 0.0~1.0 浮点数，弧线规律：低→高→低。")
    if parts:
        lines.append("共分 " + str(parts) + " 部，每章需含 part（数字）和 part_title（字符串）字段。")
    lines.append("")

    # 给出完整的方案 A 作为示例参考
    lines.append("=== 方案 A 参考格式 ===")
    lines.append('{"schemes":[{"scheme_id":"A","scheme_title":"【主题】+ 方案A特色","structure_type":"线性时间流","perspective":"主人公内心视角","main_arc":"一句话概括全书叙事主线（60字以内）","focus_angle":"切入角度（20字以内）","highlight":"最大亮点（20字以内）","style_tone":"文风调性（20字以内）","estimated_words":' + str(target_words) + ',"tension_arc":' + str(tension_arc_example) + ',"core_materials":["取材一","取材二","取材三"],"chapters":[')

    # 生成 3 个完整章节示例（A 的前三章），用真实标题示范
    # 示例基于「玄武门兵变」主题 —— 替换为你的主题时请生成类似风格的具体标题
    example_titles = [
        "玄武门之变：黎明前的博弈",
        "东宫反击：暗流涌动",
        "秦王决断：一触即发",
        "兵变时刻：血染宫门",
        "贞观之治：盛世的序章",
    ]
    example_subtitles = [
        "武德九年，太子与秦王的矛盾白热化",
        "李建成拉拢后宫，李元吉暗中布局",
        "尉迟敬德力谏，李世民下定决心",
        "六月初四，玄武门伏兵，建成元吉殒命",
        "李世民登基，开创一代盛世",
    ]
    example_arcs = [
        "秦王功高震主，太子危机感日益加深",
        "太子一党步步紧逼，秦王府人人自危",
        "天策府众将齐聚，李世民拍板行动",
        "玄武门血光闪过，政变一夜成功",
        "禅让诏书颁布，天下易主",
    ]
    for ci in range(min(3, chapters)):
        arc_val = tension_arc_example[ci] if ci < len(tension_arc_example) else 0.5
        ch_label = ["开篇引入", "矛盾积累", "上升发展"][ci] if ci < 3 else "发展"
        ch_part = ',"part":1,"part_title":"第1部标题"' if parts else ""
        comma = "," if ci < min(3, chapters) - 1 else ""
        # 用真实示例标题，或通用主题时用占位符
        ex_idx = ci % len(example_titles)
        title_eg = example_titles[ex_idx]
        sub_eg = example_subtitles[ex_idx]
        arc_eg = example_arcs[ex_idx]
        lines.append('{"chapter":' + str(ci+1) + ',"title":"' + title_eg + '","subtitle":"' + sub_eg + '","chapter_arc":"' + arc_eg + '","tension_level":' + str(arc_val) + ',"tension_label":"' + ch_label + '","key_events":["关键事件A","关键事件B"],"key_figures":["核心人物A","核心人物B"],"style_modulation":"叙事流畅，情感饱满","word_target":' + str(word_per_chapter) + ch_part + '}' + comma)

    # 其余章节的生成指令（放在 JSON 外部，JSON 不含此行）
    if chapters > 3:
        lines.append("【第4章到第' + str(chapters) + '章请按同样格式自行生成完整的JSON对象，每个章节独立一个】")
    lines.append("]}")
    lines.append("")

    # 方案 B、C 要求（纯文字，无 JSON 注释）
    for i in range(1, num_schemes):
        sid = chr(ord("A") + i)
        struct_opts = ["双线并行结构", "主题式递进结构", "地理空间串联结构"]
        persp_opts = ["历史群像视角", "历史纪录片式全知视角", "旁观者见证人视角"]
        si = i - 1
        lines.append("=== 方案 " + sid + " 要求 ===")
        lines.append("结构类型：" + struct_opts[si % len(struct_opts)] + "，叙事视角：" + persp_opts[si % len(persp_opts)] + "。其余字段（scheme_title/main_arc/focus_angle/highlight/style_tone/tension_arc/chapters）请根据主题自行生成。")
        lines.append("tension_arc 必须为长度为 " + str(chapters) + " 的浮点数数组，弧线规律：低到高再到低。")
        lines.append("")

    lines.append("=== 最终输出要求 ===")
    lines.append("请将方案 A、B、C（或更多）整合为一个纯 JSON，顶层结构：{\"schemes\":[方案A的JSON, 方案B的JSON, ...]}。")
    lines.append("只输出纯 JSON，不要任何解释文字，不要 markdown 代码块包裹。")

    return "\n".join(lines)


def _tension_arc_template(n: int) -> list[float]:
    """生成 n 章的张力弧线模板（从低到高再低）"""
    if n <= 3:
        return [0.1, 0.6, 0.3]
    if n == 4:
        return [0.1, 0.4, 0.9, 0.4]
    if n == 5:
        return [0.1, 0.3, 0.7, 0.95, 0.4]
    if n == 6:
        return [0.1, 0.3, 0.6, 0.9, 0.6, 0.3]
    # n >= 7
    arc = [0.1] + [0.3 + 0.5 * (i / (n - 3)) for i in range(1, n - 2)] + [1.0, 0.6, 0.3]
    return [round(x, 2) for x in arc[:n]]


class BookDesignGenerator:
    """
    全书设计方案生成器

    使用 LLM 根据用户结构化输入生成 3-4 套差异化的全书设计方案。
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        self._cache: dict[str, BookDesign] = {}

    def generate(self, user_input: dict, num_schemes: int = 3) -> BookDesign:
        """
        生成全书设计方案（含重试 + fallback）

        Args:
            user_input: 用户输入字典（包含 chapter_title, description, purpose 等）
            num_schemes: 生成方案数量（默认 3，最多 4）

        Returns:
            BookDesign 对象，包含多套方案
        """
        import hashlib
        import json as _json

        # 生成缓存 key（基于用户输入的关键字段）
        cache_key_input = {
            "topic": user_input.get("chapter_title", ""),
            "desc": user_input.get("description", ""),
            "purpose": user_input.get("purpose", ""),
            "ref": user_input.get("ref_works", ""),
            "words": user_input.get("target_length", 0),
        }
        cache_key = hashlib.md5(
            _json.dumps(cache_key_input, ensure_ascii=True, sort_keys=True).encode()
        ).hexdigest()[:12]

        if cache_key in self._cache:
            logger.info(f"[BookDesignGenerator] Cache hit: {cache_key}")
            bd = self._cache[cache_key]
            bd.selected_scheme_id = None  # 重置选择
            return bd

        prompt = build_book_design_prompt(user_input, num_schemes=num_schemes)
        logger.info(f"[BookDesignGenerator] Generating {num_schemes} schemes for: {user_input.get('chapter_title', '')}")

        # ── 带重试的 LLM 调用 ─────────────────────────
        target_words = user_input.get("target_length", 15000)
        # 根据字数估算 token：每章约 300~400 tokens，3套方案需要充足 buffer
        chapters_est, _, _ = _calc_chapters_and_parts(target_words)
        # 每章~350tokens × 10章 × 3套 + scheme元数据 ≈ 4000 tokens 够用
        tokens_for_design = min(4500, 1000 + chapters_est * 350)  # 1000~4500 tokens

        raw = ""
        last_error = None

        for attempt in range(3):
            try:
                temperature = 0.5 if attempt == 0 else 0.3  # 第一次 0.5，不行再降
                resp = self.llm.chat(
                    prompt,
                    temperature=temperature,
                    max_tokens=tokens_for_design,
                    timeout=60,
                )
                raw = resp.content.strip() if hasattr(resp, "content") else str(resp)
                logger.info(f"[BookDesignGenerator] Attempt {attempt+1}: got {len(raw)} chars")
                # 有效响应：非空且包含 JSON 特征
                if raw and ("{" in raw or "[" in raw):
                    break
                # 空或纯文本 → 重试
                logger.warning(f"[BookDesignGenerator] Attempt {attempt+1}: empty or invalid response, retrying...")
            except Exception as e:
                last_error = e
                logger.warning(f"[BookDesignGenerator] Attempt {attempt+1} exception: {e}")
                continue

        # ── JSON 解析（多重策略）─────────────────────
        schemes = self._parse_schemes(raw, num_schemes, user_input)

        if not schemes:
            logger.warning("[BookDesignGenerator] LLM failed, using fallback schemes")
            schemes = self._build_fallback_schemes(user_input, num_schemes)

        bd = BookDesign(schemes=schemes, user_input_ref=user_input)
        self._cache[cache_key] = bd
        logger.info(f"[BookDesignGenerator] Generated {len(schemes)} schemes")
        return bd

    def _parse_schemes(self, raw: str, num_schemes: int, user_input: dict) -> list[BookScheme]:
        """多策略解析 LLM 返回的 JSON（含空输入保护）"""
        import json as _json

        if not raw or len(raw) < 10:
            logger.warning(f"[BookDesignGenerator] Empty or too-short raw response, skipping parse")
            return []

        # 清理常见 markdown 包裹
        cleaned = raw.strip()
        for marker in ["```json", "```JSON", "```", "【", "】"]:
            if marker in cleaned:
                parts = cleaned.split(marker)
                # 取最长一个包含 "schemes" 或 "{" 的片段
                best = max(parts, key=lambda p: (
                    ("schemes" in p or "{" in p) and len(p) > 50
                ))
                cleaned = best.strip() if ("{" in best or "schemes" in best) else cleaned

        # 尝试提取 JSON 对象（找第一个 { 到最后一个 }）
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        candidate = cleaned[start:end] if (start >= 0 and end > start) else cleaned

        # 策略列表（从最宽松到最严格）
        strategies = [
            ("direct", candidate),
            ("strip_quotes", cleaned.strip('"\'')),
            ("find_schemes", self._extract_schemes_block(cleaned)),
        ]

        for name, text in strategies:
            if not text or len(text) < 20:
                continue
            try:
                data = _json.loads(text)
                schemes = []
                for scheme_data in data.get("schemes", []):
                    try:
                        schemes.append(BookScheme.from_dict(scheme_data))
                    except Exception as e:
                        logger.warning(f"[BookDesignGenerator] Scheme parse error ({name}): {e}")
                        continue
                if schemes:
                    logger.info(f"[BookDesignGenerator] Parse success ({name}): {len(schemes)} schemes")
                    return schemes
            except (_json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"[BookDesignGenerator] Parse '{name}' failed: {e}")
                continue

        # 最终 fallback：尝试逐个提取 scheme 对象
        logger.info(f"[BookDesignGenerator] Attempting partial extraction from {len(raw)} chars")
        schemes = self._extract_partial_schemes(raw, num_schemes)
        if schemes:
            logger.info(f"[BookDesignGenerator] Partial extraction: {len(schemes)} schemes recovered")
            return schemes

        logger.warning(f"[BookDesignGenerator] All parse strategies failed. raw[:100]={repr(raw[:100])}")
        return []

    def _extract_schemes_block(self, text: str) -> str:
        """从文本中提取 schemes JSON 块（宽松匹配）"""
        import re
        # 找 {"schemes":[ ... ]} 或 schemes: [...]
        m = re.search(r'"schemes"\s*:\s*\[', text)
        if m:
            # 从 schemes 开头截取到最近的 ]
            tail = text[m.start():]
            depth = 0
            end = 0
            for i, c in enumerate(tail):
                if c == "[":
                    depth += 1
                elif c == "]":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > 0:
                return '{"schemes":' + tail[:end]
        return ""

    def _extract_partial_schemes(self, text: str, num_schemes: int) -> list[BookScheme]:
        """当 JSON 解析失败时，尝试逐个提取 scheme 对象"""
        import re, json as _json
        schemes = []
        # 找所有 scheme_id: "X" 位置
        for sid in [chr(ord("A") + i) for i in range(num_schemes)]:
            pattern = r'"scheme_id"\s*:\s*"' + sid + r'"'
            m = re.search(pattern, text)
            if not m:
                continue
            # 从这个位置开始，尝试找到一个完整的 scheme 对象
            start = m.start()
            # 往前找到最近的 {
            obj_start = text.rfind("{", 0, start)
            if obj_start < 0:
                continue
            # 从 { 开始尝试解析到合理的长度
            for end_offset in range(200, min(len(text) - obj_start + 1, 8000), 100):
                candidate = text[obj_start:obj_start + end_offset]
                # 补全可能的截断：用 } 结尾
                candidate = candidate.rstrip() + "}"
                try:
                    data = _json.loads(candidate)
                    if "scheme_id" in data and data["scheme_id"] == sid:
                        schemes.append(BookScheme.from_dict(data))
                        break
                except Exception:
                    continue
        return schemes

    def _build_fallback_schemes(self, user_input: dict, num_schemes: int) -> list[BookScheme]:
        """Fallback：当 LLM 完全失败时，根据字数和主题构建基础方案"""
        target_words = user_input.get("target_length", 15000)
        chapters, parts, _ = _calc_chapters_and_parts(target_words)
        topic = user_input.get("chapter_title", "未知主题")
        characters = user_input.get("characters", [])
        main_char = characters[0] if characters else topic.split("的")[0] if "的" in topic else "主人公"

        structure_options = [
            ("线性时间流", "主人公内心视角"),
            ("双线并行", "历史群像视角"),
            ("主题式递进", "历史纪录片式全知视角"),
        ]
        arc_options = [
            f"{main_char}的命运转折与精神成长",
            f"围绕{topic}的历史事件全景",
            f"以{topic}为核心的文化解读",
        ]

        schemes = []
        for i in range(num_schemes):
            sid = chr(ord("A") + i)
            struct, persp = structure_options[i % len(structure_options)]
            arc = arc_options[i % len(arc_options)]
            scheme_chapters = []
            arc_values = _tension_arc_template(chapters)

            tension_labels = ["开篇引入", "矛盾积累", "上升发展",
                            "高潮时刻", "回落收束", "结局"]
            # 为 fallback 生成有实质内容的章节标题（基于主题 + 叙事弧位置）
            if chapters == 3:
                ch_arcs = [
                    (f"{topic}的历史背景与核心人物登场",
                     f"乱世之中，{main_char}如何走向历史舞台的中央"),
                    (f"{topic}的矛盾激化与关键抉择",
                     f"各方势力角逐，{main_char}面临命运的十字路口"),
                    (f"{topic}的高潮与历史回响",
                     f"一切尘埃落定，历史从此改写"),
                ]
            elif chapters == 4:
                ch_arcs = [
                    (f"{topic}的时代背景",
                     f"风起青萍，历史酝酿巨变"),
                    (f"势力对垒：暗流涌动",
                     f"多方博弈，危机一触即发"),
                    (f"决定性时刻",
                     f"千钧一发，{main_char}做出关键抉择"),
                    (f"余波与历史定局",
                     f"尘埃落定，盛世的序章由此开启"),
                ]
            elif chapters == 5:
                ch_arcs = [
                    (f"{topic}的历史舞台",
                     f"时势造英雄，{main_char}登上历史前台"),
                    (f"矛盾初现",
                     f"表面平静，暗流已动"),
                    (f"冲突升级",
                     f"各方角力，白热化阶段来临"),
                    (f"转折与决战",
                     f"最关键的一步，命运在此分野"),
                    (f"结局与影响",
                     f"新的时代就此开启"),
                ]
            else:
                # 通用模板
                ch_arcs = [
                    (f"第一章：{topic}的序章",
                     f"{main_char}登场，历史的车轮开始转动"),
                    (f"第二章：风云际会",
                     f"矛盾交织，冲突的种子已然埋下"),
                    (f"第三章：局势激化",
                     f"各方势力公开对峙，危机逼近"),
                    (f"第四章：命运对决",
                     f"关键时刻来临，一切在此一搏"),
                    (f"第五章：尘埃落定",
                     f"结局揭晓，历史翻开新的一页"),
                    (f"第六章：余波与回响",
                     f"事件的深远影响与历史评价"),
                ]
            if parts:
                ch_per_part = chapters // parts
                for ci in range(chapters):
                    part_num = min(ci // ch_per_part + 1, parts)
                    arc_desc, arc_sub = ch_arcs[ci % len(ch_arcs)]
                    scheme_chapters.append(ChapterDesign(
                        chapter=ci + 1,
                        title=f"第{ci+1}章「{arc_desc[:12]}」",
                        subtitle=arc_sub,
                        chapter_arc=arc_desc,
                        tension_level=arc_values[ci] if ci < len(arc_values) else 0.5,
                        tension_label=tension_labels[min(ci, len(tension_labels)-1)],
                        key_events=[arc_desc[:10]],
                        key_figures=[main_char],
                        style_modulation="叙事流畅，情感饱满",
                        word_target=max(800, target_words // chapters),
                        part=part_num,
                        part_title=f"第{part_num}部",
                    ))
            else:
                for ci in range(chapters):
                    arc_desc, arc_sub = ch_arcs[ci % len(ch_arcs)]
                    scheme_chapters.append(ChapterDesign(
                        chapter=ci + 1,
                        title=f"第{ci+1}章「{arc_desc[:12]}」",
                        subtitle=arc_sub,
                        chapter_arc=arc_desc,
                        tension_level=arc_values[ci] if ci < len(arc_values) else 0.5,
                        tension_label=tension_labels[min(ci, len(tension_labels)-1)],
                        key_events=[arc_desc[:10]],
                        key_figures=[main_char],
                        style_modulation="叙事流畅，情感饱满",
                        word_target=max(800, target_words // chapters),
                    ))

            schemes.append(BookScheme(
                scheme_id=sid,
                scheme_title=f"方案{sid}：{struct}·{persp}",
                structure_type=struct,
                perspective=persp,
                main_arc=arc,
                focus_angle="深入浅出，兼顾可读性与学术性",
                chapters=scheme_chapters,
                tension_arc=[round(v, 2) for v in arc_values],
                core_materials=[main_char],
                style_tone="通俗流畅，兼具历史感",
                highlight="结构清晰，适合长篇叙事",
                estimated_words=target_words,
            ))
        return schemes


    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
