# -*- coding: utf-8 -*-
"""
PT-047 社科智能体创作平�?· Gradio 重构�?v2.0
================================================
基于 UIUX SOP v2.0 DAGO 方法�?· S6 古典高端风（墨韵金韵�?
DAGO 推导路径：Dims(D1=form-create+immersive,D2=end_user,D5=medium,D6=creation)
             �?Architectural(L4居中表单向导 + S6 Luxury Premium)
             �?Generative(完整Token体系：金�?墨底/Noto Serif SC)
             �?Operational(墨滴加载/张力曲线/分部确认/Word导出)

技术栈：Gradio 6.x + 自定义墨韵主�?+ LLM客户端复�?
启动：python gui_gradio.py（端�?860�?
"""

from __future__ import annotations
import sys, os, time, json
from typing import Optional

# ════════════════════════════════════════════════════════════════════
# 路径配置
# ════════════════════════════════════════════════════════════════════
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)

os.environ.setdefault("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")
os.environ.setdefault("QWEN_API_KEY", "YOUR_QWEN_API_KEY")
os.environ.setdefault("PYTHONPATH", _ROOT)

# ════════════════════════════════════════════════════════════════════
# CSS 注入（墨韵金�?S6 古典高端风）
# ════════════════════════════════════════════════════════════════════
_CSS_PATH = os.path.join(_ROOT, "styles", "ink_gold.css")
_CSS = open(_CSS_PATH, encoding="utf-8").read() if os.path.exists(_CSS_PATH) else ""

# ════════════════════════════════════════════════════════════════════
# Gradio 墨韵主题（DAGO G层：S6 Luxury Premium 色阶�?
# Gradio 6.x: gr.themes.Color(c50..c950, �?0�?
# ════════════════════════════════════════════════════════════════════
def _build_ink_gold_theme():
    """构建墨韵金韵 S6 主题（DAGO G�?Token 推导�?""
    import gradio as gr

    # S6 Primary Gold �?暖金色系（temperature=0.1, brand=sophisticated�?
    gold = gr.themes.Color(
        c50="#1a1a10",
        c100="#252215",
        c200="#302a18",
        c300="#6b5c2a",
        c400="#8a7235",
        c500="#d4af37",
        c600="#e0c050",
        c700="#e0c468",
        c800="#f0d080",
        c900="#f8e4a8",
        c950="#fcf4d0",
    )

    # Neutral Stone �?石墨中性色（暖灰）
    stone = gr.themes.Color(
        c50="#131318",
        c100="#181820",
        c200="#222230",
        c300="#222230",
        c400="#2e2e3c",
        c500="#3e3e50",
        c600="#525268",
        c700="#6e6e82",
        c800="#9a9ab0",
        c900="#c8c8d8",
        c950="#e8e4dc",
    )

    # Secondary Plum �?墨紫色点缀（AI 元素�?
    plum = gr.themes.Color(
        c50="#100d18",
        c100="#18142a",
        c200="#201c38",
        c300="#342e5a",
        c400="#4a3e78",
        c500="#7c5cbf",
        c600="#9474d0",
        c700="#ac90e0",
        c800="#c8b4f0",
        c900="#e0d4ff",
        c950="#f0ecff",
    )

    theme = gr.themes.Default(
        primary_hue=gold,
        secondary_hue=plum,
        neutral_hue=stone,
    )
    # 设置墨韵金韵主题（只使用 Gradio 6.15.0 中存在的属性）
    theme.set(
        background_fill_primary="#131318",
        background_fill_secondary="#181820",
        body_background_fill="#131318",
        body_text_color="#ddd8d0",
        body_text_color_subdued="#9898a8",
        color_accent="#d4af37",
        color_accent_soft="#3a2e18",
        block_background_fill="#1c1c26",
        block_border_color="rgba(212,175,55,0.28)",
        block_border_width="1px",
        block_radius="10px",
        block_shadow="0 8px 32px rgba(0,0,0,0.5)",
        block_padding="20px",
        block_label_background_fill="#262630",
        block_label_border_color="rgba(212,175,55,0.20)",
        block_label_border_width="1px",
        block_label_text_color="#b8b4ac",
        button_primary_background_fill="#d4af37",
        button_primary_background_fill_hover="#e0c050",
        button_primary_border_color="#d4af37",
        button_primary_text_color="#131318",
        button_secondary_background_fill="#262630",
        button_secondary_background_fill_hover="#222230",
        button_secondary_border_color="#d4af37",
        button_secondary_text_color="#d4af37",
        button_medium_radius="8px",
        button_medium_padding="12px 20px",
        input_background_fill="#222230",
        input_border_color="rgba(212,175,55,0.32)",
        input_border_color_focus="#d4af37",
        input_radius="6px",
        input_padding="10px 14px",
        input_text_size="14px",
        border_color_accent="#d4af37",
        border_color_accent_subdued="rgba(212,175,55,0.38)",
        border_color_primary="#d4af37",
        slider_color="#d4af37",
        error_border_color="#b54a4a",
        error_background_fill="#b54a4a",
        container_radius="12px",
        embed_radius="8px",
        panel_background_fill="#181820",
        panel_border_color="rgba(212,175,55,0.16)",
    )
    return theme


# ════════════════════════════════════════════════════════════════════
# LLM 客户�?
# ════════════════════════════════════════════════════════════════════
def _get_llm():
    from shared.tools.llm_clients import get_llm_client as _g
    return _g()


def _llm_chat(prompt: str, temperature: float = 0.5,
              max_tokens: int = 4096, timeout: int = 60) -> str:
    llm = _get_llm()
    resp = llm.chat(prompt, temperature=temperature,
                    max_tokens=max_tokens, timeout=timeout)
    return resp.content if hasattr(resp, "content") else str(resp)


# ════════════════════════════════════════════════════════════════════
# Wizard 状态（Gradio State 组件会序列化�?
# ════════════════════════════════════════════════════════════════════
class WizardState:
    """向导状�?�?所有字段必须为 JSON 可序列化类型"""
    def __init__(self):
        self.step: int = 0
        # 用户输入
        self.topic: str = ""
        self.description: str = ""
        self.characters: str = ""
        self.themes: str = ""
        self.target_length: int = 15000
        self.purpose: str = "一般通俗写作"
        self.ref_works: str = ""
        # 方案
        self.schemes: list = []          # list[dict] from BookDesignGenerator
        self.selected_scheme_id: str = ""
        # 取材
        self.suggested_materials: dict = {}
        self.selected_events: list = []
        self.selected_figures: list = []
        self.selected_themes: list = []
        # 预览
        self.unified: dict = {}          # unified preview result
        self.chapter_contents: list = []  # generated chapters
        self.generation_status: str = ""   # "idle" | "generating" | "done"
        self.generation_progress: float = 0.0
        self.error: str = ""

    def reset(self):
        self.__init__()

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "topic": self.topic,
            "selected_scheme_id": self.selected_scheme_id,
            "chapter_count": len(self.chapter_contents),
            "generation_progress": self.generation_progress,
        }


# ════════════════════════════════════════════════════════════════════
# LLM 生成函数（复�?progressive_guide/ 模块�?
# ════════════════════════════════════════════════════════════════════
def _build_user_input(state: WizardState) -> dict:
    char_list = [c.strip() for c in state.characters.split("/") if c.strip()]
    theme_list = [t.strip() for t in state.themes.split("/") if t.strip()]
    return {
        "chapter_title": state.topic.strip(),
        "description": state.description.strip(),
        "characters": char_list,
        "themes": theme_list,
        "target_length": state.target_length,
        "purpose": state.purpose,
        "ref_works": [w.strip() for w in state.ref_works.split("/") if w.strip()],
    }


def _generate_schemes(state: WizardState) -> tuple[list, str]:
    """生成3套全书设计方�?""
    from progressive_guide.book_design import BookDesignGenerator
    ui = _build_user_input(state)
    llm = _get_llm()
    gen = BookDesignGenerator(llm)
    bd = gen.generate(ui, num_schemes=3)
    schemes = []
    for s in bd.schemes:
        chapters = []
        for ch in s.chapters:
            chapters.append({
                "chapter": ch.chapter,
                "title": ch.title,
                "subtitle": ch.subtitle,
                "tension": ch.tension_level,
                "tension_label": ch.tension_label,
                "estimated_chars": ch.word_target,
            })
        schemes.append({
            "scheme_id": s.scheme_id,
            "scheme_title": s.scheme_title,
            "structure_type": s.structure_type,
            "perspective": s.perspective,
            "main_arc": s.main_arc,
            "highlight": s.highlight,
            "chapters": chapters,
        })
    return schemes, ""


def _generate_materials(state: WizardState) -> dict:
    """AI 推荐取材"""
    topic = state.topic or "未知主题"
    desc = state.description or ""
    chars = state.characters or ""
    prompt = (
        f"你是一位历史通俗作品创作顾问。请为以下主题推荐核心取材。\n"
        f"主题：{topic}\n描述：{desc}\n人物：{chars}\n\n"
        f"请严格输�?JSON（无 markdown 标记）：\n"
        f'{{"events":[{{"name":"事件名称","reason":"推荐理由�?0字内�?,"mandatory":true}}],'
        f'"figures":[{{"name":"人物名称","reason":"推荐理由�?0字内�?,"mandatory":false}}],'
        f'"topics":["主题�?","主题�?"]}}\n\n只输出纯 JSON 对象�?
    )
    raw = _llm_chat(prompt, temperature=0.3, max_tokens=800, timeout=30)
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"events": [], "figures": [], "topics": []}


def _build_unified(state: WizardState) -> dict:
    """根据选中�?scheme 构建 unified 预览结构"""
    for scheme in state.schemes:
        if scheme.get("scheme_id") == state.selected_scheme_id:
            return {
                "theme": state.topic,
                "style_label": "通俗叙事",
                "chapter_outline": scheme.get("chapters", []),
                "structure_type": scheme.get("structure_type", ""),
                "perspective": scheme.get("perspective", ""),
                "main_arc": scheme.get("main_arc", ""),
            }
    return {}


def _generate_chapter_content(
    state: WizardState,
    chapter_num: int,
    outline: dict,
) -> str:
    """生成单个章节正文"""
    # 素材汇�?
    mats = {
        "events": state.selected_events,
        "figures": state.selected_figures,
        "themes": state.selected_themes,
    }
    events_str = " / ".join(mats.get("events", [])[:3])
    figures_str = " / ".join(mats.get("figures", [])[:3])

    # 张力指引
    directive_map = {
        1: "开篇，引入背景，奠定基调。叙事舒缓，为后续积蓄张力�?,
        2: "矛盾积累。人物面临困境或内心挣扎，叙事节奏渐紧�?,
        3: "上升发展。冲突推进，高潮铺垫，张力持续攀升�?,
        4: "高潮前奏。氛围进一步紧张，情绪到达临界点�?,
        5: "高潮时刻。核心冲突爆发，情感达到顶点�?,
    }
    total_chapters = len(state.unified.get("chapter_outline", []))
    if chapter_num >= total_chapters * 0.7:
        directive = "高潮与收束。情感要有爆发力，结尾有余韵�?
    else:
        directive = directive_map.get(chapter_num, "发展叙事，承上启下�?)

    prompt = (
        f"你是一位历史通俗作品作家。请写出**第{chapter_num}�?*的完整正文。\n\n"
        f"【书名】《{state.topic}》\n"
        f"【风格】通俗叙事\n"
        f"【章节】第{chapter_num}章「{outline.get('title', '未知')}」—�?{outline.get('subtitle', '')}\n"
        f"【张力】{outline.get('tension', 0.5):.0%}（{outline.get('tension_label', '发展�?)}）\n"
        f"【预估字数】约 {outline.get('estimated_chars', 800)} 字\n"
        f"【素材】事件：{events_str} | 人物：{figures_str}\n"
        f"【章节指引】{directive}\n"
        f"【要求】约 {outline.get('estimated_chars', 800)} 字，人物对话符合时代身份，有具体场景描写。直接输出正文，不要加章节标题前缀�?
    )
    return _llm_chat(prompt, temperature=0.75, max_tokens=4096, timeout=90)


# ════════════════════════════════════════════════════════════════════
# HTML 渲染函数（DAGO G层：视觉组件�?
# ════════════════════════════════════════════════════════════════════
def _step_indicator(current: int) -> str:
    """步骤指示器（5步）"""
    labels = [
        ("✍️", "创作意图"),
        ("📋", "选择方案"),
        ("🎯", "确认取材"),
        ("📖", "章节预览"),
        ("📚", "全书生成"),
    ]
    icons = [
        "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z",
        "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 9h-2v6h2v-6zm-4 6H5v-2h2v2zm8-2V5h-4v4h4z",
        "M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z",
        "M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z",
        "M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z",
    ]
    html = '<div class="ink-step-indicator">'
    for i, (emoji, label) in enumerate(labels):
        if i < current:
            cls = "completed"
            icon_svg = f'<svg class="ink-step-icon" viewBox="0 0 24 24"><path fill="currentColor" d="{icons[i]}"/></svg>'
        elif i == current:
            cls = "active"
            icon_svg = f'<svg class="ink-step-icon" viewBox="0 0 24 24"><path fill="currentColor" d="{icons[i]}"/></svg>'
        else:
            cls = "pending"
            icon_svg = f'<svg class="ink-step-icon" viewBox="0 0 24 24"><path fill="currentColor" d="{icons[i]}"/></svg>'
        connector = (
            f'<div class="ink-step-connector">'
            f'<div class="ink-step-connector-fill" style="background:{"#d4af37" if i < current else "rgba(212,175,55,0.24)"}"></div>'
            f'</div>'
            if i < len(labels) - 1 else ""
        )
        html += (
            f'<div class="ink-step {cls}">'
            f'<div class="ink-step-dot">{icon_svg}</div>'
            f'<div class="ink-step-label">{emoji} {label}</div>'
            f'</div>{connector}'
        )
    html += '</div>'
    return html


def _scheme_card(scheme: dict, selected_id: str) -> str:
    """方案卡片 HTML"""
    sid = scheme["scheme_id"]
    is_sel = sid == selected_id
    sel_border = "border-color:#d4af37; box-shadow:0 0 30px rgba(212,175,55,0.28), 0 8px 32px rgba(0,0,0,0.5);" if is_sel else ""
    sel_bg = "background:linear-gradient(135deg,#1a1a26,#161620);" if is_sel else ""
    sel_badge = '<span class="ink-badge ink-badge-selected">�?已选中</span>' if is_sel else ""

    # 章节列表（最多显�?章）
    chapters_html = ""
    for ch in scheme["chapters"][:4]:
        pct = int(ch.get("tension", 0.5) * 100)
        chapters_html += (
            f'<div class="scheme-chapter-row">'
            f'<span class="scheme-chapter-num">第{ch["chapter"]}�?/span>'
            f'<div class="scheme-tension-track"><div class="scheme-tension-fill" style="width:{pct}%"></div></div>'
            f'<span class="scheme-tension-pct">{pct}%</span>'
            f'</div>'
        )
    more = f'<div class="scheme-more-chapters">+ 还有 {len(scheme["chapters"])-4} 章…�?/div>' if len(scheme["chapters"]) > 4 else ""

    return (
        f'<div class="scheme-card{" selected" if is_sel else ""}" '
        f'style="{sel_border}{sel_bg}" data-scheme-id="{sid}">'
        f'<div class="scheme-card-header">'
        f'<div class="scheme-id-badge">{sid}</div>'
        f'<div class="scheme-title-group">'
        f'<div class="scheme-title">{scheme["scheme_title"]}</div>'
        f'<div class="scheme-meta">{scheme.get("structure_type","")} · {scheme.get("perspective","")} {sel_badge}</div>'
        f'</div></div>'
        f'<div class="scheme-arc">「{scheme.get("main_arc","")}�?/div>'
        f'<div class="scheme-chapters">{chapters_html}{more}</div>'
        f'<div class="scheme-highlight">�?{scheme.get("highlight","")}</div>'
        f'</div>'
    )


def _chapter_card(ch: dict, index: int) -> str:
    """章节预览卡片"""
    pct = int(ch.get("tension", 0.5) * 100)
    return (
        f'<div class="chapter-card">'
        f'<div class="chapter-card-top">'
        f'<div class="chapter-card-title">第{ch.get("chapter",index+1)}�?· {ch.get("title","未知")}</div>'
        f'<div class="ink-badge ink-badge-gold">{pct}% {ch.get("tension_label","")}</div>'
        f'</div>'
        f'<div class="chapter-card-subtitle">{ch.get("subtitle","")}</div>'
        f'<div class="tension-track"><div class="tension-fill" style="width:{pct}%"></div></div>'
        f'<div class="chapter-card-footer">�?{ch.get("estimated_chars",800):,} �?/div>'
        f'</div>'
    )


def _loading_ink(text: str = "墨韵构思中，请稍候…�?) -> str:
    """墨滴扩散加载动画"""
    return (
        f'<div class="ink-loading">'
        f'<div class="ink-drop-anim">'
        f'<div class="ink-ring ink-ring-1"></div>'
        f'<div class="ink-ring ink-ring-2"></div>'
        f'<div class="ink-ring ink-ring-3"></div>'
        f'<div class="ink-core"></div>'
        f'</div>'
        f'<div class="ink-loading-text">{text}</div>'
        f'</div>'
    )


# ════════════════════════════════════════════════════════════════════
# Gradio 应用构建（O层：操作层）
# ════════════════════════════════════════════════════════════════════
def _build_app():

    import gradio as gr

    theme = _build_ink_gold_theme()

    with gr.Blocks(
        title="墨韵金声 · 社科智能体创作平�?,
    ) as demo:

        # ── 状态组�?──────────────────────────────────────
        state = gr.State(WizardState())
        # 用于刷新方案的辅助状�?
        scheme_refresh = gr.State(0)

        # ══════════════════════════════════════�?
        # 全局 Logo �?
        # ══════════════════════════════════════�?
        gr.HTML(
            '<div class="ink-logo">'
            '<div class="ink-logo-main">墨韵金声</div>'
            '<div class="ink-logo-sub">PT-047 社科智能体创作平�?/div>'
            '<div class="ink-logo-tag">'
            '<span class="ink-badge ink-badge-gold">S6 古典高端�?/span>'
            '<span class="ink-badge ink-badge-plum">DAGO v2.0</span>'
            '<span class="ink-badge ink-badge-muted">Gradio</span>'
            '</div>'
            '</div>',
        )

        # 步骤指示器（动态）
        step_html = gr.HTML(_step_indicator(0), elem_id="step-indicator")

        gr.HTML('<div class="ink-divider"></div>')

        # ══════════════════════════════════════�?
        # 步骤0：创作意�?
        # ══════════════════════════════════════�?
        with gr.Group(visible=True) as step0:
            gr.Markdown(
                '<div class="ink-section-title">'
                '<span class="ink-step-num">01</span>'
                '<span>创作意图</span>'
                '<div class="ink-title-underline"></div>'
                '</div>'
            )
            gr.Markdown(
                '<div class="ink-hint">'
                '填写以下信息，AI 将为你生成完整的全书设计方案�?
                '所有字段均可随时修改，下一步开始前支持重新生成�?
                '</div>'
            )

            topic = gr.Textbox(
                label="📖 作品主题",
                placeholder="例如：苏东坡创作《黄州寒食帖》的故事",
                value="苏东坡创作《黄州寒食帖》的故事",
                lines=1,
                info="作品标题或核心主题，将决定全书叙事主�?,
            )
            desc = gr.TextArea(
                label="📝 创作描述",
                placeholder="描述你的作品想要讲述的故事背景、核心冲突等…�?,
                value="苏轼被贬黄州第三年的寒食节，写下被誉为天下第三行书的经历",
                lines=3,
                info="描述你的创作意图和故事背�?,
            )
            chars = gr.Textbox(
                label="👤 核心人物（斜�?/ 分隔�?,
                placeholder="例如：苏�?/ 王巩 / 朝云",
                value="苏轼 / 王巩",
                lines=1,
                info="涉及的主要历史人物，AI 将据此推荐更多相关人�?,
            )
            themes = gr.Textbox(
                label="🏷 主题词（斜杠 / 分隔，可选）",
                placeholder="例如：贬�?/ 书法 / 精神涅槃",
                value="贬谪 / 书法 / 精神成长",
                lines=1,
                info="作品的核心主题维度，帮助 AI 把握叙事基调",
            )
            words = gr.Slider(
                label="📏 目标字数",
                minimum=1000, maximum=80000, value=15000, step=500,
                info="建议 10000�?0000 字为�?,
            )
            purpose = gr.Dropdown(
                label="🎯 写作目的",
                choices=[
                    "一般通俗写作",
                    "艺考备考练�?,
                    "参赛作品投稿",
                    "学术论文附录材料",
                ],
                value="一般通俗写作",
                info="目的不同，叙事风格和取材侧重点会有所不同",
            )
            ref_works = gr.Textbox(
                label="🏛 参考作品（斜杠 / 分隔，可选）",
                placeholder="例如：《明朝那些事儿�?/ 《苏东坡传�?,
                value="",
                lines=1,
                info="你想借鉴风格的标杆作�?,
            )

            gr.HTML('<div class="ink-form-sep"></div>')
            start_btn = gr.Button(
                "�?开启创作旅�?,
                variant="primary",
                scale=1,
            )

        # ══════════════════════════════════════�?
        # 步骤1：方案选择
        # ══════════════════════════════════════�?
        with gr.Group(visible=False) as step1:
            gr.Markdown(
                '<div class="ink-section-title">'
                '<span class="ink-step-num">02</span>'
                '<span>全书设计方案 · 请选择一�?/span>'
                '<div class="ink-title-underline"></div>'
                '</div>'
            )
            gr.Markdown(
                '<div class="ink-hint">'
                '三套方案各有特色：点击选中 �?查看详情 �?确认后进入取材�?
                '可多次重新生成，直到满意为止�?
                '</div>'
            )

            topic_summary = gr.Markdown("", visible=True)

            scheme_loading = gr.HTML(
                _loading_ink("✦AI 正在构�?3 套差异化方案……约需 30~50 �?),
                visible=True,
            )

            # 方案展示区（HTML 渲染，带金色边框高亮�?
            scheme_container = gr.HTML("", visible=False)
            scheme_error = gr.HTML("", visible=False)

            # 方案单选（Gradio 原生交互组件�?
            scheme_radio = gr.Radio(
                choices=[],
                label="请选择一套方案（点击即可选中�?,
                info="选中后下方将展示方案详情",
                interactive=True,
            )

            gr.Markdown("---")
            with gr.Row():
                regen_btn = gr.Button("🔄 重新生成方案", variant="secondary", scale=0)
                confirm_btn = gr.Button("�?确认方案，进入取�?, variant="primary", scale=1, visible=False)

        # ══════════════════════════════════════�?
        # 步骤2：取材确�?
        # ══════════════════════════════════════�?
        with gr.Group(visible=False) as step2:
            gr.Markdown(
                '<div class="ink-section-title">'
                '<span class="ink-step-num">03</span>'
                '<span>AI 推荐取材 · 请确�?/span>'
                '<div class="ink-title-underline"></div>'
                '</div>'
            )
            gr.HTML(
                '<div class="ink-hint">'
                '�?核心骨架（不可取消）&nbsp;&nbsp;�?丰富层次（可按需勾选）&nbsp;&nbsp;'
                '也可直接在下方文本框中补充素�?
                '</div>'
            )
            gr.HTML(
                '<div style="font-size:12px; color:#8880a0; margin-bottom:16px;">'
                '提示：AI 推荐的事件为骨架层，建议全部保留；人物和主题词可按需调整�?
                '</div>'
            )

            mat_loading = gr.HTML(
                _loading_ink("✦AI 正在根据你的主题推荐历史取材…�?),
                visible=True,
            )
            mat_error = gr.HTML("", visible=False)

            # 取材 CheckboxGroup（加载后显示�?
            event_cb = gr.CheckboxGroup(
                choices=[],
                label="📌 历史事件（核心骨架，不可取消�?,
                info="AI 推荐的核心事件，建议全部保留",
                interactive=True,
                visible=False,
            )
            figure_cb = gr.CheckboxGroup(
                choices=[],
                label="👤 历史人物",
                info="可取消不相关的人�?,
                interactive=True,
                visible=False,
            )
            theme_cb = gr.CheckboxGroup(
                choices=[],
                label="🏷 主题�?,
                info="可补充或取消主题�?,
                interactive=True,
                visible=False,
            )

            # 自定义取材输�?
            gr.Markdown("#### �?补充素材（可选）")
            custom_events = gr.Textbox(
                label="补充事件（斜杠分隔）",
                placeholder="例如：安史之�?/ 乌台诗案",
                lines=1,
            )
            custom_figures = gr.Textbox(
                label="补充人物（斜杠分隔）",
                placeholder="例如：颜真卿 / 柳宗�?,
                lines=1,
            )
            custom_themes = gr.Textbox(
                label="补充主题词（斜杠分隔�?,
                placeholder="例如：文人风�?/ 汉字美学",
                lines=1,
            )

            gr.HTML('<div class="ink-form-sep"></div>')
            with gr.Row():
                regen_mat_btn = gr.Button("🔄 重新生成推荐", variant="secondary", scale=0)
                preview_btn = gr.Button("�?生成章节框架预览", variant="primary", scale=1)

        # ══════════════════════════════════════�?
        # 步骤3：章节框架预�?
        # ══════════════════════════════════════�?
        with gr.Group(visible=False) as step3:
            gr.Markdown(
                '<div class="ink-section-title">'
                '<span class="ink-step-num">04</span>'
                '<span>章节框架预览</span>'
                '<div class="ink-title-underline"></div>'
                '</div>'
            )
            gr.Markdown(
                '<div class="ink-hint">'
                '每章标注了张力等级（低→高），反映了叙事的节奏起伏�?
                '确认框架后，AI 将生成第1章草稿�?
                '</div>'
            )

            framework_container = gr.HTML("", visible=False)
            framework_loading = gr.HTML(
                _loading_ink("📖正在构建章节框架…�?),
                visible=False,
            )

            gr.HTML('<div class="ink-form-sep"></div>')
            gen_ch1_btn = gr.Button(
                "📖 确认框架，生成第1�?,
                variant="primary",
            )

        # ══════════════════════════════════════�?
        # 步骤4：第1章预�?
        # ══════════════════════════════════════�?
        with gr.Group(visible=False) as step4:
            gr.Markdown(
                '<div class="ink-section-title">'
                '<span class="ink-step-num">05</span>'
                '<span>�?章预�?/span>'
                '<div class="ink-title-underline"></div>'
                '</div>'
            )
            gr.Markdown(
                '<div class="ink-hint">'
                '阅读�?章草稿，如不满意可重新生成。确认后，AI 将自动生成后续章节�?
                '</div>'
            )

            ch1_meta = gr.HTML("", visible=True)

            ch1_loading = gr.HTML(
                _loading_ink("✦AI 正在挥毫……约需 60~90 �?),
                visible=True,
            )
            ch1_content = gr.Markdown("", visible=False)
            ch1_error = gr.HTML("", visible=False)

            gr.HTML('<div class="ink-form-sep"></div>')
            with gr.Row():
                regen_ch1_btn = gr.Button("🔄 重新生成", variant="secondary", scale=0)
                gen_full_btn = gr.Button(
                    "📚 确认�?章，生成全本",
                    variant="primary",
                    scale=1,
                )

        # ══════════════════════════════════════�?
        # 步骤5：全书生�?
        # ══════════════════════════════════════�?
        with gr.Group(visible=False) as step5:
            gr.Markdown(
                '<div class="ink-section-title">'
                '<span class="ink-step-num">06</span>'
                '<span>全书生成</span>'
                '<div class="ink-title-underline"></div>'
                '</div>'
            )

            gen_progress = gr.HTML("", visible=True)
            gen_ch_container = gr.HTML("", visible=False)

            gr.HTML('<div class="ink-form-sep"></div>')
            download_btn = gr.Button("�?导出 Word 文档", variant="primary")
            restart_btn = gr.Button("🔄 重新开�?, variant="secondary")

        # ══════════════════════════════════════�?
        # 事件绑定（O层核心）
        # ══════════════════════════════════════�?

        # ── 步骤0 �?步骤1（生成方案）──────────────
        def on_start(
            topic_v, desc_v, chars_v, themes_v, words_v, purpose_v, ref_v, st: WizardState
        ):
            st.topic = topic_v
            st.description = desc_v
            st.characters = chars_v
            st.themes = themes_v
            st.target_length = words_v
            st.purpose = purpose_v
            st.ref_works = ref_v
            st.step = 1
            st.schemes = []
            st.selected_scheme_id = ""
            st.error = ""

            summary = (
                f"**📖 {topic_v}** &nbsp;|&nbsp; "
                f"**{words_v:,} �?* &nbsp;|&nbsp; "
                f"目的：{purpose_v}"
            )
            # 同步生成方案（Gradio 不支�?Group.change()，合并到这里�?
            try:
                schemes, _ = _generate_schemes(st)
                st.schemes = schemes
                cards = "".join(_scheme_card(s, st.selected_scheme_id) for s in schemes)
                return (
                    {step0: gr.update(visible=False),
                     step1: gr.update(visible=True),
                     step_html: gr.update(value=_step_indicator(1)),
                     topic_summary: gr.update(value=summary, visible=True),
                     scheme_loading: gr.update(visible=False),
                     scheme_container: gr.update(visible=True, value=cards),
                     scheme_radio: gr.update(
                         choices=[s["scheme_id"] for s in schemes],
                         value=None,
                     ),
                     scheme_error: gr.update(visible=False),
                     confirm_btn: gr.update(visible=False),
                     }
                )
            except Exception as e:
                st.error = str(e)
                return (
                    {step0: gr.update(visible=False),
                     step1: gr.update(visible=True),
                     step_html: gr.update(value=_step_indicator(1)),
                     topic_summary: gr.update(value=summary, visible=True),
                     scheme_loading: gr.update(visible=False),
                     scheme_container: gr.update(visible=False, value=""),
                     scheme_error: gr.update(
                         visible=True,
                         value=f'<div class="ink-alert ink-alert-error">方案生成失败：{e}</div>',
                     ),
                     scheme_radio: gr.update(choices=[], value=None),
                     confirm_btn: gr.update(visible=False),
                     }
                )

        start_btn.click(
            on_start,
            inputs=[topic, desc, chars, themes, words, purpose, ref_works, state],
            outputs=[
                step0, step1, step_html,
                topic_summary, scheme_loading, scheme_container,
                scheme_radio, scheme_error, confirm_btn,
            ],
        )

        # ── 重新生成方案 ──────────────────────
        def on_regen_schemes(st: WizardState):
            st.schemes = []
            st.selected_scheme_id = ""
            try:
                schemes, _ = _generate_schemes(st)
                st.schemes = schemes
                cards = "".join(_scheme_card(s, st.selected_scheme_id) for s in schemes)
                return {
                    scheme_loading: gr.update(visible=False),
                    scheme_container: gr.update(visible=True, value=cards),
                    scheme_radio: gr.update(choices=[s["scheme_id"] for s in schemes], value=None),
                    scheme_error: gr.update(visible=False),
                    confirm_btn: gr.update(visible=False),
                }
            except Exception as e:
                st.error = str(e)
                return {
                    scheme_loading: gr.update(visible=False),
                    scheme_error: gr.update(
                        visible=True,
                        value=f'<div class="ink-alert ink-alert-error">方案生成失败：{e}</div>',
                    ),
                    scheme_radio: gr.update(choices=[], value=None),
                    confirm_btn: gr.update(visible=False),
                }

        regen_btn.click(
            on_regen_schemes,
            inputs=[state],
            outputs=[scheme_loading, scheme_container, scheme_radio, scheme_error, confirm_btn],
        )

        # ── 方案 Radio 选择 ─────────────────────────────────
        def on_scheme_selected(scheme_id: str, st: WizardState):
            """用户点击 Radio �?高亮卡片 + 显示确认按钮"""
            if not scheme_id:
                return {
                    scheme_container: gr.update(value=""),
                    confirm_btn: gr.update(visible=False),
                }
            st.selected_scheme_id = scheme_id
            # 用选中态重新渲染所有卡�?
            cards = "".join(_scheme_card(s, scheme_id) for s in st.schemes)
            # 找到选中方案的关键信�?
            for s in st.schemes:
                if s["scheme_id"] == scheme_id:
                    sel_scheme = s
                    break
            else:
                sel_scheme = st.schemes[0] if st.schemes else {}
            sel_cards = (
                f'<div class="ink-alert ink-alert-success" style="margin-bottom:12px;">'
                f'�?已选中方案 <strong>{sel_scheme.get("scheme_title","")}</strong>'
                f'（{sel_scheme.get("structure_type","")} · {len(sel_scheme.get("chapters",[]))}章节�?
                f'</div>'
                + cards
            )
            return {
                scheme_container: gr.update(value=sel_cards),
                confirm_btn: gr.update(visible=True),
            }

        scheme_radio.change(
            on_scheme_selected,
            inputs=[scheme_radio, state],
            outputs=[scheme_container, confirm_btn],
        )

        # ── 确认方案 �?步骤2（生成取材）──────────
        def on_confirm_scheme(st: WizardState):
            if not st.selected_scheme_id:
                return {}
            st.step = 2
            st.suggested_materials = {}
            st.selected_events = []
            st.selected_figures = []
            st.selected_themes = []
            try:
                sugg = _generate_materials(st)
                st.suggested_materials = sugg
                evts = [e["name"] for e in sugg.get("events", [])]
                figs = [f["name"] for f in sugg.get("figures", [])]
                tops = sugg.get("topics", [])
                st.selected_events = evts
                st.selected_figures = figs
                st.selected_themes = tops
                return (
                    {step1: gr.update(visible=False),
                     step2: gr.update(visible=True),
                     step_html: gr.update(value=_step_indicator(2)),
                     mat_loading: gr.update(visible=False),
                     mat_error: gr.update(visible=False),
                     event_cb: gr.update(choices=evts, value=evts, visible=True),
                     figure_cb: gr.update(choices=figs, value=figs, visible=True),
                     theme_cb: gr.update(choices=tops, value=tops, visible=True),
                     }
                )
            except Exception as e:
                st.error = str(e)
                return (
                    {step1: gr.update(visible=False),
                     step2: gr.update(visible=True),
                     step_html: gr.update(value=_step_indicator(2)),
                     mat_loading: gr.update(visible=False),
                     mat_error: gr.update(
                         visible=True,
                         value=f'<div class="ink-alert ink-alert-error">取材生成失败：{e}</div>',
                     ),
                     event_cb: gr.update(visible=False),
                     figure_cb: gr.update(visible=False),
                     theme_cb: gr.update(visible=False),
                     }
                )

        confirm_btn.click(
            on_confirm_scheme,
            inputs=[state],
            outputs=[
                step1, step2, step_html,
                mat_loading, mat_error,
                event_cb, figure_cb, theme_cb,
            ],
        )

        # ── 重新生成取材 ──────────────────────
        def on_regen_materials(st: WizardState):
            st.suggested_materials = {}
            try:
                sugg = _generate_materials(st)
                st.suggested_materials = sugg
                evts = [e["name"] for e in sugg.get("events", [])]
                figs = [f["name"] for f in sugg.get("figures", [])]
                tops = sugg.get("topics", [])
                st.selected_events = evts
                st.selected_figures = figs
                st.selected_themes = tops
                return {
                    mat_loading: gr.update(visible=False),
                    mat_error: gr.update(visible=False),
                    event_cb: gr.update(choices=evts, value=evts, visible=True),
                    figure_cb: gr.update(choices=figs, value=figs, visible=True),
                    theme_cb: gr.update(choices=tops, value=tops, visible=True),
                }
            except Exception as e:
                st.error = str(e)
                return {
                    mat_loading: gr.update(visible=False),
                    mat_error: gr.update(
                        visible=True,
                        value=f'<div class="ink-alert ink-alert-error">取材生成失败：{e}</div>',
                    ),
                    event_cb: gr.update(visible=False),
                    figure_cb: gr.update(visible=False),
                    theme_cb: gr.update(visible=False),
                }

        regen_mat_btn.click(
            on_regen_materials,
            inputs=[state],
            outputs=[mat_loading, mat_error, event_cb, figure_cb, theme_cb],
        )

        # ── 取材确认 �?步骤3 ─────────────────
        def on_confirm_materials(
            evts: list, figs: list, tops: list,
            ce: str, cf: str, ct: str,
            st: WizardState
        ):
            # 取材来源：AI推荐（CheckboxGroup�? 用户自定义（Textbox�?
            selected_evts = list(evts) if evts else []
            selected_figs = list(figs) if figs else []
            selected_tops = list(tops) if tops else []
            if ce:
                selected_evts = list(set(selected_evts + [e.strip() for e in ce.split("/") if e.strip()]))
            if cf:
                selected_figs = list(set(selected_figs + [f.strip() for f in cf.split("/") if f.strip()]))
            if ct:
                selected_tops = list(set(selected_tops + [t.strip() for t in ct.split("/") if t.strip()]))
            st.selected_events = selected_evts
            st.selected_figures = selected_figs
            st.selected_themes = selected_tops
            st.step = 3
            st.unified = _build_unified(st)
            chapters_html = "".join(
                _chapter_card(ch, i) for i, ch in enumerate(st.unified.get("chapter_outline", []))
            )
            # 素材汇总提�?
            mats_summary = (
                f'<div class="ink-alert ink-alert-info" style="margin-bottom:16px;">'
                f'已�?{len(selected_evts)} 个事�?· {len(selected_figs)} 个人�?· {len(selected_tops)} 个主题词'
                f'</div>'
            )
            framework_value = (
                f'<div class="ink-book-meta">'
                f'<div class="ink-book-title">📖《{st.topic}�?/div>'
                f'<div class="ink-book-info">'
                f'<span class="ink-badge ink-badge-gold">{st.unified.get("style_label","通俗叙事")}</span>'
                f'<span class="ink-badge ink-badge-muted">{len(st.unified.get("chapter_outline",[]))} 章节</span>'
                f'<span class="ink-badge ink-badge-plum">{st.unified.get("structure_type","")}</span>'
                f'</div>'
                f'<div class="ink-book-arc">「{st.unified.get("main_arc","")}�?/div>'
                f'</div>'
                f'{mats_summary}'
                f'<div class="chapter-list">{chapters_html}</div>'
            )
            return {
                step2: gr.update(visible=False),
                step3: gr.update(visible=True),
                step_html: gr.update(value=_step_indicator(3)),
                framework_container: gr.update(visible=True, value=framework_value),
            }

        preview_btn.click(
            on_confirm_materials,
            inputs=[event_cb, figure_cb, theme_cb, custom_events, custom_figures, custom_themes, state],
            outputs=[step2, step3, step_html, framework_container],
        )

        # ── 确认框架 �?步骤4（生成第1章）────────
        def on_confirm_framework(st: WizardState):
            st.step = 4
            st.chapter_contents = []
            st.error = ""
            outline = st.unified.get("chapter_outline", [{}])[0]
            ch1_meta_val = (
                f'<div class="ink-ch1-meta">'
                f'<div class="ink-ch1-title">📖 �?�?· {outline.get("title","未知")}</div>'
                f'<div class="ink-ch1-subtitle">{outline.get("subtitle","")}</div>'
                f'<div class="ink-ch1-meta-badges">'
                f'<span class="ink-badge ink-badge-gold">{int(outline.get("tension",0.1)*100)}% {outline.get("tension_label","")}</span>'
                f'<span class="ink-badge ink-badge-muted">�?{outline.get("estimated_chars",800):,} �?/span>'
                f'</div>'
                f'</div>'
            )
            # 生成�?章（合并到这里，避免 step4.change() 不存在的问题�?
            try:
                content = _generate_chapter_content(st, 1, outline)
                st.chapter_contents.append({
                    "chapter": 1,
                    "title": outline.get("title", "�?�?),
                    "content": content,
                    "char_count": len(content),
                })
                md_content = f"<div class='ink-chapter-text'>{content}</div>"
                return (
                    {step3: gr.update(visible=False),
                     step4: gr.update(visible=True),
                     step_html: gr.update(value=_step_indicator(4)),
                     ch1_meta: gr.update(value=ch1_meta_val, visible=True),
                     ch1_loading: gr.update(visible=False),
                     ch1_content: gr.update(visible=True, value=md_content),
                     ch1_error: gr.update(visible=False),
                     }
                )
            except Exception as e:
                st.error = str(e)
                return (
                    {step3: gr.update(visible=False),
                     step4: gr.update(visible=True),
                     step_html: gr.update(value=_step_indicator(4)),
                     ch1_meta: gr.update(value=ch1_meta_val, visible=True),
                     ch1_loading: gr.update(visible=False),
                     ch1_content: gr.update(visible=False, value=""),
                     ch1_error: gr.update(
                         visible=True,
                         value=f'<div class="ink-alert ink-alert-error">生成失败：{e}</div>',
                     ),
                     }
                )

        gen_ch1_btn.click(
            on_confirm_framework,
            inputs=[state],
            outputs=[step3, step4, step_html, ch1_meta, ch1_loading, ch1_content, ch1_error],
        )

        # ── 重新生成�?�?────────────────────
        def on_regen_ch1(st: WizardState):
            st.chapter_contents = []
            outline = st.unified.get("chapter_outline", [{}])[0]
            try:
                content = _generate_chapter_content(st, 1, outline)
                st.chapter_contents.append({
                    "chapter": 1,
                    "title": outline.get("title", "�?�?),
                    "content": content,
                    "char_count": len(content),
                })
                md_content = f"<div class='ink-chapter-text'>{content}</div>"
                return {
                    ch1_loading: gr.update(visible=False),
                    ch1_content: gr.update(visible=True, value=md_content),
                    ch1_error: gr.update(visible=False),
                }
            except Exception as e:
                st.error = str(e)
                return {
                    ch1_loading: gr.update(visible=False),
                    ch1_error: gr.update(
                        visible=True,
                        value=f'<div class="ink-alert ink-alert-error">生成失败：{e}</div>',
                    ),
                }

        regen_ch1_btn.click(
            on_regen_ch1,
            inputs=[state],
            outputs=[ch1_loading, ch1_content, ch1_error],
        )

        # ── 确认�?�?�?步骤5 ────────────────
        def on_confirm_ch1_and_gen(st: WizardState):
            st.step = 5
            total = len(st.unified.get("chapter_outline", []))
            progress_html = (
                f'<div class="ink-progress-section">'
                f'<div class="ink-progress-header">'
                f'<div>全书生成进度</div>'
                f'<div class="ink-progress-pct">0 / {total} �?/div>'
                f'</div>'
                f'<div class="ink-progress-track">'
                f'<div class="ink-progress-fill" style="width:0%"></div>'
                f'</div>'
                f'<div class="ink-progress-hint">全书生成中，预计需�?{total * 90 // 60}～{total * 120 // 60} 分钟…�?/div>'
                f'</div>'
            )
            return {
                step4: gr.update(visible=False),
                step5: gr.update(visible=True),
                step_html: gr.update(value=_step_indicator(4)),
                gen_progress: gr.update(value=progress_html, visible=True),
                gen_ch_container: gr.update(visible=True, value="<div class='ink-chapter-list'></div>"),
            }

        gen_full_btn.click(
            on_confirm_ch1_and_gen,
            inputs=[state],
            outputs=[step4, step5, step_html, gen_progress, gen_ch_container],
        )

        # ── 重新开�?──────────────────────────
        def on_restart():
            return {
                step0: gr.update(visible=True),
                step1: gr.update(visible=False),
                step2: gr.update(visible=False),
                step3: gr.update(visible=False),
                step4: gr.update(visible=False),
                step5: gr.update(visible=False),
                step_html: gr.update(value=_step_indicator(0)),
            }

        restart_btn.click(
            on_restart,
            outputs=[step0, step1, step2, step3, step4, step5, step_html],
        )

    return demo, theme


def _render_materials(st: WizardState) -> str:
    """渲染取材列表 HTML"""
    sugg = st.suggested_materials
    html = ""

    # 事件
    if sugg.get("events"):
        html += '<div class="mat-section">'
        html += '<div class="mat-section-title">📌 历史事件（骨架层�?/div>'
        for evt in sugg["events"]:
            mand = evt.get("mandatory", False)
            checked = evt["name"] in st.selected_events
            check_cls = "checked" if checked else ""
            mand_icon = "�? if mand else "�?
            html += (
                f'<div class="mat-item{" mat-mandatory" if mand else ""}">'
                f'<div class="mat-check {check_cls}" data-type="event" data-name="{evt["name"]}">'
                f'<div class="mat-check-box">{"�? if checked else ""}</div></div>'
                f'<div class="mat-content">'
                f'<div class="mat-name">{mand_icon} {evt["name"]}</div>'
                f'<div class="mat-reason">{evt.get("reason","")}</div>'
                f'</div></div>'
            )
        html += '</div>'

    # 人物
    if sugg.get("figures"):
        html += '<div class="mat-section">'
        html += '<div class="mat-section-title">👤 历史人物</div>'
        for fig in sugg["figures"]:
            mand = fig.get("mandatory", False)
            checked = fig["name"] in st.selected_figures
            check_cls = "checked" if checked else ""
            mand_icon = "�? if mand else "�?
            html += (
                f'<div class="mat-item">'
                f'<div class="mat-check {check_cls}" data-type="figure" data-name="{fig["name"]}">'
                f'<div class="mat-check-box">{"�? if checked else ""}</div></div>'
                f'<div class="mat-content">'
                f'<div class="mat-name">{mand_icon} {fig["name"]}</div>'
                f'<div class="mat-reason">{fig.get("reason","")}</div>'
                f'</div></div>'
            )
        html += '</div>'

    # 主题�?
    if sugg.get("topics"):
        html += '<div class="mat-section">'
        html += '<div class="mat-section-title">🏷 主题�?/div>'
        html += '<div class="mat-topics">'
        for topic in sugg["topics"]:
            checked = topic in st.selected_themes
            html += (
                f'<div class="mat-topic-chip{" checked" if checked else ""}">'
                f'{"�? if checked else "�?} {topic}'
                f'</div>'
            )
        html += '</div></div>'

    return html


# ════════════════════════════════════════════════════════════════════
# 启动
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 58)
    print("  PT-047 社科智能体创作平�?· Gradio 重构�?v2.0")
    print("  墨韵金声 · S6 古典高端�?· UIUX SOP v2.0 DAGO")
    print("  端口：http://127.0.0.1:7860")
    print("=" * 58)

    demo, theme = _build_app()
    demo.launch(
        server_port=7860,
        server_name="127.0.0.1",
        share=False,
        show_error=True,
        theme=theme,
        css=_CSS,
        head=(
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;600&display=swap" rel="stylesheet">'
        ),
    )
