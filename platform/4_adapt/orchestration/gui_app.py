r"""
gui_app.py �?PT-047 渐进式引�?GUI
====================================
基于 Streamlit 的简�?Web 界面，完整验�?渐进式输�?+ 用户确认"流程�?

运行方式:
    cd D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent
    set DEEPSEEK_API_KEY=YOUR_DEEPSEEK_API_KEY
    streamlit run gui_app.py --server.port 8501

访问 http://localhost:8501
"""
from __future__ import annotations
import os, sys, time, logging
from pathlib import Path

# ── 路径设置 ─────────────────────────────────────────────
_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

# ── 环境变量 ─────────────────────────────────────────────
os.environ.setdefault("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Streamlit ─────────────────────────────────────────────
import streamlit as st

# 强制清缓存，确保每次启动都加载最新代�?
try:
    st.cache_data.clear()
    st.cache_resource.clear()
except Exception:
    pass

st.set_page_config(
    page_title="PT-047 社科创作平台",
    page_icon="�?,
    layout="wide",
    initial_sidebar_state="collapsed",
)

_INK_GOLD_CSS = r"""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;600&display=swap');

/* ── 全局背景 & 字体 ── */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: #f8f4eb !important;
    font-family: 'Noto Sans SC', 'PingFang SC', sans-serif !important;
}

/* Streamlit 主容�?*/
[data-testid="stMainBlockContainer"] {
    background: transparent !important;
    padding-top: 0 !important;
    max-width: 1100px !important;
}

/* ── 侧栏 ── */
[data-testid="stSidebar"] {
    background: #f0ebe0 !important;
    border-right: 1px solid #d4c4a8 !important;
}

/* ── 标题字体 ── */
h1, h2, h3, h4, .main-header {
    font-family: 'Noto Serif SC', 'SimSun', 'STSong', serif !important;
}

/* ── 主标题区（page_input 顶部�?── */
.main-header {
    font-family: 'Noto Serif SC', serif !important;
    font-size: 1.85em;
    font-weight: 700;
    color: #523427;
    letter-spacing: 0.05em;
    padding: 20px 0 16px;
    margin-bottom: 24px;
    border-bottom: 2px solid #d4c4a8;
    position: relative;
}
.main-header::after {
    content: '';
    position: absolute;
    bottom: -2px; left: 0;
    width: 80px; height: 2px;
    background: linear-gradient(90deg, #967c46, #c49a47);
}

/* ── 步骤进度条（横向�?── */
.step-progress-wrap {
    display: flex;
    align-items: flex-start;
    gap: 0;
    margin: 20px 0 28px;
    padding: 16px 20px;
    background: #fffdf8;
    border: 1px solid #d4c4a8;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(82,58,39,0.06);
}
.step-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;
}
.step-node:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 13px; left: calc(50% + 14px); width: calc(100% - 28px);
    height: 2px;
    background: #e8dcc8;
    z-index: 0;
}
.step-node.done:not(:last-child)::after {
    background: linear-gradient(90deg, #967c46, #c49a47);
}
.step-circle {
    width: 26px; height: 26px;
    border-radius: 50%;
    border: 2px solid #d4c4a8;
    background: #faf8f5;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
    color: #b0a090;
    position: relative; z-index: 1;
    transition: all 0.3s ease;
    font-family: 'Noto Serif SC', serif;
}
.step-node.done .step-circle {
    background: linear-gradient(135deg, #967c46, #c49a47);
    border-color: #967c46;
    color: #fff;
    box-shadow: 0 2px 8px rgba(150,124,70,0.35);
}
.step-node.active .step-circle {
    border-color: #967c46;
    color: #fff;
    background: linear-gradient(135deg, #967c46, #c49a47);
    box-shadow: 0 0 0 4px rgba(150,124,70,0.15);
}
.step-label {
    font-size: 10.5px;
    color: #9a8a78;
    margin-top: 6px;
    text-align: center;
    line-height: 1.3;
    font-family: 'Noto Sans SC', sans-serif;
    padding: 0 2px;
}
.step-node.done .step-label { color: #967c46; font-weight: 500; }
.step-node.active .step-label { color: #523427; font-weight: 600; }

/* ── 表单区域 ── */
.stForm {
    background: #fff;
    border: 1px solid #d4c4a8;
    border-radius: 8px;
    padding: 28px 32px;
    box-shadow: 0 2px 8px rgba(82,58,39,0.07);
}

/* ── 表单字段区（两列布局�?── */
.form-grid {
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    gap: 20px 28px;
    margin-bottom: 20px;
}
.form-section-label {
    font-family: 'Noto Serif SC', serif;
    font-size: 12px;
    font-weight: 600;
    color: #967c46;
    letter-spacing: 0.12em;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #d4c4a8;
}

/* ── 输入�?/ textarea ── */
.st-cn, .st-cj, textarea, input[type="text"],
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #fdfcf9 !important;
    border: 1px solid #d4c4a8 !important;
    border-radius: 4px !important;
    color: #3d3020 !important;
    font-size: 14px !important;
    font-family: 'Noto Sans SC', sans-serif !important;
    box-shadow: inset 0 1px 3px rgba(82,58,39,0.05) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
textarea:focus, input:focus,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #967c46 !important;
    box-shadow: 0 0 0 3px rgba(150,124,70,0.12), inset 0 1px 3px rgba(82,58,39,0.04) !important;
    outline: none !important;
}
textarea::placeholder, input::placeholder {
    color: #b0a090 !important;
}

/* ── Selectbox / MultiSelect ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] {
    background: #fdfcf9 !important;
    border-color: #d4c4a8 !important;
    border-radius: 4px !important;
    color: #3d3020 !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stMultiSelect"] [data-baseweb="select"] {
    background: #fdfcf9 !important;
}

/* ── Slider ── */
.st-ir input[type="range"] { accent-color: #967c46 !important; }
.st-c5 .st-ir .css-1q8juvz { color: #967c46 !important; }

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid #d4c4a8 !important;
    margin: 22px 0 !important;
}

/* ── 表单标签 ── */
.st-c4 label, label, .st-ci,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label {
    color: #745836 !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    font-family: 'Noto Sans SC', sans-serif !important;
}

/* ── 信息框（Alert�?── */
.st-d8, div[data-testid="stAlert"] {
    border-radius: 6px !important;
    border-left-width: 3px !important;
    font-size: 13.5px !important;
}
[data-testid="stAlert"][data-testid="stAlert-success"] {
    background: rgba(93,138,74,0.07) !important;
    border-color: #5d8a4a !important;
    color: #4a7a3a !important;
}
[data-testid="stAlert"][data-testid="stAlert-info"] {
    background: rgba(90,122,138,0.07) !important;
    border-color: #5a7a8a !important;
    color: #4a6a7a !important;
}
[data-testid="stAlert"][data-testid="stAlert-warning"] {
    background: rgba(196,145,58,0.07) !important;
    border-color: #c4913a !important;
    color: #a07830 !important;
}
[data-testid="stAlert"][data-testid="stAlert-error"] {
    background: rgba(163,74,58,0.07) !important;
    border-color: #a34a3a !important;
    color: #8a3a2a !important;
}

/* ── Tabs ── */
.st-bh button {
    color: #9a8a78 !important;
    border-bottom: 2px solid transparent !important;
    font-family: 'Noto Sans SC', sans-serif !important;
    font-size: 13.5px !important;
    transition: color 0.2s !important;
}
.st-bh button:hover { color: #745836 !important; }
.st-bh button[data-testid="stTab"][aria-selected="true"] {
    color: #967c46 !important;
    border-bottom-color: #967c46 !important;
    font-weight: 600 !important;
}

/* ── Progress bar ── */
.st-cb .st-cs .st-gz { background: rgba(150,124,70,0.15) !important; }
.st-cb .st-cs .st-ha {
    background: linear-gradient(90deg,#967c46,#c49a47) !important;
    border-radius: 3px;
}

/* ── Checkbox ── */
[data-testid="stCheckbox"] label {
    color: #523427 !important;
    font-size: 13.5px !important;
}

/* ── 通用按钮 & 表单提交按钮 ── */
.stButton > button,
[data-testid="stMainContainer"] button {
    border-radius: 4px !important;
    font-family: 'Noto Sans SC', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
}
.stFormSubmitButton button {
    background: linear-gradient(135deg, #967c46, #c49a47) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    font-family: 'Noto Sans SC', sans-serif !important;
    padding: 0.55em 1.8em !important;
    box-shadow: 0 2px 8px rgba(150,124,70,0.25) !important;
    transition: all 0.2s ease !important;
}
.stFormSubmitButton button:hover {
    box-shadow: 0 4px 14px rgba(150,124,70,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── Markdown 正文 ── */
p, .st-ce, .st-cf, [data-testid="stMarkdownContainer"] p {
    color: #3d3020 !important;
    font-size: 14px !important;
    line-height: 1.75 !important;
}
.st-ce { color: #3d3020 !important; }
h1, h2, h3, h4 {
    color: #523427 !important;
    font-family: 'Noto Serif SC', serif !important;
}

/* ── 方案卡片（scheme-card-box�?── */
.scheme-card-box {
    background: #fff;
    border: 1.5px solid #d4c4a8;
    border-radius: 8px;
    padding: 22px 26px;
    margin-bottom: 18px;
    transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
    box-shadow: 0 1px 4px rgba(82,58,39,0.06);
}
.scheme-card-box:hover {
    border-color: #c49a47;
    box-shadow: 0 4px 16px rgba(82,58,39,0.12), 0 1px 4px rgba(82,58,39,0.06);
    transform: translateY(-2px);
}
.scheme-card-box.selected {
    border-color: #967c46;
    border-width: 2px;
    background: #fffdf8;
    box-shadow: 0 3px 12px rgba(150,124,70,0.18);
}

/* ── 章节卡片（chapter-card�?── */
.chapter-card {
    background: #fdfcf9;
    border: 1px solid #d4c4a8;
    border-left: 3px solid #967c46;
    border-radius: 0 6px 6px 0;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.chapter-card:hover { border-left-color: #c49a47; }

/* ── 张力�?── */
.tension-bar {
    height: 5px;
    border-radius: 3px;
    background: #e8dcc8;
    overflow: hidden;
    margin-top: 6px;
}
.tension-bar-fill {
    height: 100%;
    background: linear-gradient(90deg,#967c46,#c49a47);
    border-radius: 3px;
    transition: width 0.6s cubic-bezier(0.16,1,0.3,1);
}

/* ── 素材标签（material-tag�?── */
.material-tag {
    display: inline-block;
    padding: 0.22em 0.65em;
    background: rgba(150,124,70,0.10);
    color: #745836;
    border: 1px solid rgba(150,124,70,0.25);
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}

/* ── 徽章 ── */
.badge-gold {
    background: rgba(196,154,71,0.15);
    color: #967c46;
    border: 1px solid rgba(196,154,71,0.3);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}
.badge-plum {
    background: rgba(124,92,191,0.08);
    color: #6a4a9a;
    border: 1px solid rgba(124,92,191,0.22);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}
.badge-jade {
    background: rgba(93,138,74,0.08);
    color: #4a7a3a;
    border: 1px solid rgba(93,138,74,0.22);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}

/* ── 加载动画（墨滴·典雅版�?── */
.ink-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 0;
    gap: 18px;
}
.ink-drop-anim {
    position: relative;
    width: 60px; height: 60px;
    display: flex; align-items: center; justify-content: center;
}
.ink-ring {
    position: absolute;
    border-radius: 50%;
    border: 2px solid rgba(150,124,70,0.35);
    animation: ink-expand 2.4s ease-out infinite;
}
.ink-ring-1 { width: 20px; height: 20px; animation-delay: 0s; }
.ink-ring-2 { width: 36px; height: 36px; animation-delay: 0.8s; }
.ink-ring-3 { width: 52px; height: 52px; animation-delay: 1.6s; }
.ink-core {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: radial-gradient(circle,#d4af37 0%,#967c46 60%,#745836 100%);
    box-shadow: 0 0 12px rgba(150,124,70,0.5);
}
@keyframes ink-expand {
    0%   { transform: scale(0.5); opacity: 0.9; border-color: rgba(150,124,70,0.5); }
    80%  { transform: scale(1.25); opacity: 0; }
    100% { transform: scale(1.25); opacity: 0; }
}
.ink-loading-text {
    color: #9a8a78;
    font-size: 12.5px;
    letter-spacing: 0.1em;
    text-align: center;
    font-family: 'Noto Serif SC', serif;
}

/* ── 底部说明 ── */
.hint-box {
    margin-top: 1.8em;
    padding: 14px 18px;
    background: rgba(150,124,70,0.05);
    border: 1px solid rgba(150,124,70,0.18);
    border-radius: 6px;
    font-size: 12.5px;
    color: #8a7a68;
    line-height: 1.8;
}

/* ── Logo 标题�?── */
.ink-logo { text-align: center; padding: 20px 0 6px; }
.ink-logo-main {
    font-family: 'Noto Serif SC', serif !important;
    font-size: 20px;
    font-weight: 700;
    color: #523427;
    letter-spacing: 0.18em;
}
.ink-logo-main::before { content: '�?; color: #967c46; }
.ink-logo-main::after  { content: '�?; color: #967c46; }
.ink-logo-sub {
    font-size: 11.5px;
    color: #9a8a78;
    letter-spacing: 0.22em;
    margin-top: 4px;
}

/* ── 风格样章卡片（style-preview-card�?── */
.style-preview-card {
    background: #fffdf8;
    border: 1.5px solid #d4c4a8;
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 0;
    transition: all 0.2s ease;
    height: 100%;
}
.style-preview-card:hover {
    border-color: #c49a47;
    box-shadow: 0 2px 8px rgba(150,124,70,0.12);
}
.style-preview-card.selected {
    border-color: #967c46;
    border-width: 2px;
    background: #fffbf0;
    box-shadow: 0 3px 12px rgba(150,124,70,0.15);
}

/* ── 创作意图预览卡（intent-summary-card�?── */
.intent-summary-card {
    background: linear-gradient(135deg, #fdfcf9, #f8f4ed);
    border: 1px solid #d4c4a8;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(82,58,39,0.05);
}

/* ── 副标题小�?── */
.caption-text {
    font-size: 12px;
    color: #9a8a78;
    font-style: italic;
    margin-bottom: 8px;
}

/* ── 小节标题（h3 级别�?── */
.section-title {
    font-family: 'Noto Serif SC', serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #523427 !important;
    margin: 20px 0 12px !important;
    padding-bottom: 6px !important;
    border-bottom: 1px solid #d4c4a8 !important;
}

/* ── 高潮章节标记 ── */
.climax-badge {
    background: linear-gradient(135deg, #a34a3a, #c4634a);
    color: #fff;
    border-radius: 20px;
    padding: 1px 8px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.05em;
}

/* ── 选中态遮�?── */
.selected-overlay {
    position: relative;
}
.selected-overlay::before {
    content: '�?已�?;
    position: absolute;
    top: 10px; right: 12px;
    background: linear-gradient(135deg, #967c46, #c49a47);
    color: #fff;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}

/* ── 隐藏 Streamlit 默认 logo / hamburger ── */
[data-testid="stToolbar"] { display: none !important; }
#MainMenu { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f0ebe0; }
::-webkit-scrollbar-thumb { background: #d4c4a8; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #c49a47; }
</style>
"""
st.markdown(_INK_GOLD_CSS, unsafe_allow_html=True)

# ── 日志抑制（减�?Streamlit 控制台噪音）────────────────
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ════════════════════════════════════════════════════════════
# 页面状态管理（session_state�?
# ════════════════════════════════════════════════════════════
def _init_state():
    # ── 只在 key 不存在时初始化；已存在的值（如用户刚提交�?step=1）不覆盖 ──
    defaults = {
        "step": 0,
        "user_input": None,
        "book_design": None,
        "selected_scheme_id": None,
        "style_phase": None,
        "unified": None,
        "chapter_contents": [],
        "selected_style": None,
        "custom_materials": None,
        "suggested_materials": None,
        "mats_confirmed": False,
        "chapter1_approved": False,
        "generation_started": False,
        "error": None,
        "_prev_topic": None,
        "_parsed_intent": None,
        "_next_part_to_generate": 2,
        "_completed_parts": [],
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

_init_state()

# ════════════════════════════════════════════════════════════
# 核心逻辑（延迟导入，避免 Streamlit 重载时重复执行）
# ════════════════════════════════════════════════════════════
@st.cache_resource
def get_llm():
    from shared.tools.llm_clients import get_llm_client
    return get_llm_client()


def run_phase1(llm, user_input: dict):
    """Phase1: 风格尝味"""
    from progressive_guide import UnifiedPreviewComposer
    composer = UnifiedPreviewComposer(llm_client=llm)
    style_phase = composer.build_style_preview(user_input)
    return composer, style_phase


def run_phase2(composer, style_phase, user_input, mock_orchestration, mock_materials):
    """Phase2: 框架预览"""
    unified = composer.build_framework_preview(
        user_input=user_input,
        style_phase=style_phase,
        orchestration_output=mock_orchestration,
        material_scout_output=mock_materials,
    )
    return unified


def generate_material_suggestions(llm, user_input: dict) -> dict:
    """
    Phase 2A: LLM 根据用户创作主题推荐历史事件和关键人物�?
    返回结构（每个素材含推荐理由 + 是否必选）�?
      {
        "events": [{"name": "...", "reason": "...", "mandatory": true/false}, ...],
        "figures": [{"name": "...", "reason": "...", "mandatory": true/false}, ...],
        "topics": [...]
      }

    mandatory=true 表示该素材是叙事核心骨架，通常不可跳过�?
    mandatory=false 表示该素材丰富故事，可根据篇幅决定是否使用�?
    """
    topic = user_input.get("chapter_title", "")
    desc = user_input.get("description", "")
    chars = user_input.get("characters", [])
    themes = user_input.get("themes", [])

    prompt = f"""你是一位历史题材创作顾问。用户准备写一篇关于「{topic}」的历史通俗作品�?

【创作主题】：{topic}
【描述】：{desc}
【主角人物】：{', '.join(chars) if chars else '暂无（请自行推断核心人物�?}
【核心主题】：{', '.join(themes) if themes else '暂无'}

请为这个创作主题推荐创作素材，输�?JSON�?

{{
  "events": [
    {{
      "name": "事件名称",
      "reason": "为什么推荐这个事件（10-20字，说明在故事中的作用）",
      "mandatory": true  // true=叙事骨架必选，false=可选项（丰富故事用�?
    }},
    ...
  ],
  "figures": [
    {{
      "name": "人物名称",
      "reason": "为什么推荐这个人物（10-20字，说明在叙事中的作用）",
      "mandatory": true
    }},
    ...
  ],
  "topics": ["主题�?", "主题�?"]
}}

规则�?
- mandatory=true 的事�?人物是故事的核心骨架，缺少它叙事就不完整
  （如主角的人生转折点、核心冲突事件、贯穿全文的关键人物�?
- mandatory=false 的素材是锦上添花，用于丰富层�?
- 主角本人 mandatory=true；主角参与的重大事件 mandatory=true
- 事件名称要具体有画面感（�?乌台诗案"�?黄州躬�?而非"被贬�?�?
- 人物可以是主角、配角、反派，只要与主题相�?
- 全部用中文；mandatory 用英�?true/false
- 只输�?JSON，不要任何解�?""

    try:
        resp = llm.chat(prompt, temperature=0.3, max_tokens=800)
        raw = resp.content.strip() if hasattr(resp, "content") else ""
        import json as _json
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = _json.loads(raw[start:end])
            # 规范化字段（允许 LLM 用不�?key 名）
            def norm(items, key_name="name"):
                if not items:
                    return []
                if isinstance(items[0], str):
                    return [{"name": i, "reason": "", "mandatory": False} for i in items]
                return [
                    {
                        "name": str(it.get(key_name, it.get("name", it.get("figure", "")))),
                        "reason": str(it.get("reason", "")),
                        "mandatory": bool(it.get("mandatory", False)),
                    }
                    for it in items
                ]

            return {
                "events": norm(data.get("events", [])),
                "figures": norm(data.get("figures", data.get("characters", [])), "name"),
                "topics": data.get("topics", []),
            }
    except Exception as e:
        pass

    # Fallback：把用户输入的人物转成建议（无理由，�?mandatory 区分�?
    result = {"events": [], "figures": [], "topics": list(themes) if themes else []}
    if chars:
        result["figures"] = [
            {"name": c, "reason": "（你输入的主角人物）", "mandatory": True}
            for c in chars
        ]
    return result


# ════════════════════════════════════════════════════════════
# 创作意图模板解析器（支持�?Markdown 文件导入�?
# ════════════════════════════════════════════════════════════

def _parse_intent_template(raw: str) -> dict | None:
    """
    解析创作意图 Markdown 模板，返回符�?page_input() 所需�?dict�?
    支持格式�?
      - YAML frontmatter�?-- ... ---�?
      - Markdown 章节格式�?*标题�?* 内容�?
      - Python code block（```yaml ... ```�?
    字段映射见下�?
    """
    import re

    def _strip(text: str) -> str:
        return text.strip().strip("`\"'").strip()

    def _yaml_val(block: str, key: str) -> str:
        """�?YAML 代码块中查找 key: value"""
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*[:：]\s*(.+)$", re.M)
        m = pattern.search(block)
        return _strip(m.group(1)) if m else ""

    def _md_key_val(text: str, key: str) -> str:
        """�?Markdown 正文中查�?**key** �?## key 后的第一段内�?""
        patterns = [
            rf"\*\*{re.escape(key)}[�?]*\s*\*?\s*(.+?)(?=\n\n|\n[^ \n]|$)",
            rf"##?\s+{re.escape(key)}[�?]*\s*(.+?)(?=\n\n|\n[^ \n]|$)",
            rf"^{re.escape(key)}\s*[:：]\s*(.+)$",
        ]
        for p in patterns:
            m = re.search(p, text, re.M | re.S)
            if m:
                val = m.group(1).strip()
                # 去除 Markdown 粗体/斜体标记
                val = re.sub(r"\*+", "", val)
                val = re.sub(r"^[-�?]\s*", "", val)
                return val.strip()
        return ""

    def _md_code_block(text: str, lang: str = "yaml") -> str:
        """提取 ```lang ... ``` 代码块内�?""
        pattern = re.compile(
            rf"```{lang}[^\n]*\n(.*?)```", re.DOTALL
        )
        m = pattern.search(text)
        return m.group(1).strip() if m else ""

    def _md_code_inline(text: str) -> str:
        """提取 ``` ... ``` 代码块内容（无语言标识�?""
        pattern = re.compile(r"```(?:yaml)?[^\n]*\n?(.*?)```", re.DOTALL)
        blocks = pattern.findall(text)
        return "\n".join(b.strip() for b in blocks if b.strip())

    def _extract_characters(text: str) -> list[str]:
        """从人物节提取 / 分隔的字符串，返回列�?""
        # 先试 YAML
        yaml_block = _md_code_block(text, "yaml")
        chars = _yaml_val(yaml_block, "核心人物")
        if chars:
            return [c.strip() for c in re.split(r"[/�?，]", chars) if c.strip()]
        # 再试代码�?
        block = _md_code_inline(text)
        if "人物" in block or "characters" in block.lower():
            lines = [l for l in block.splitlines() if l.strip() and not l.strip().startswith("#")]
            for line in lines:
                if "/" in line or "�? in line or "," in line:
                    return [c.strip() for c in re.split(r"[/�?，]", line) if c.strip()]
        # �?Markdown 正文匹配
        m = re.search(r"核心人物[^�?]*[�?]\s*\n?((?:.+\n){1,5}?)(?=\n[^ \n]|\n\n|\Z)", text, re.S)
        if m:
            candidates = m.group(1)
            line = [l for l in candidates.splitlines() if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("**")][0:1]
            if line:
                return [c.strip() for c in re.split(r"[/�?，]", line[0]) if c.strip()]
        return []

    def _extract_themes(text: str) -> list[str]:
        """从主题节提取 / 分隔的字符串，返回列�?""
        yaml_block = _md_code_block(text, "yaml")
        themes = _yaml_val(yaml_block, "核心主题")
        if themes:
            return [t.strip() for t in re.split(r"[/�?，]", themes) if t.strip()]
        block = _md_code_inline(text)
        for line in block.splitlines():
            if ("主题" in line or "themes" in line.lower()) and ("/" in line or "�? in line):
                return [t.strip() for t in re.split(r"[/�?，]", line) if t.strip()]
        return []

    def _safe_int(s: str) -> int:
        try:
            return int(re.sub(r"\D", "", s))
        except Exception:
            return 15000  # 默认

    # ── 主逻辑 ─────────────────────────────────────────────
    raw = raw.strip()

    # 1. YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", raw, re.DOTALL)
    fm = fm_match.group(1).strip() if fm_match else ""

    # 2. 作品标题
    title = (
        _yaml_val(fm, "作品标题")
        or _yaml_val(_md_code_block(raw, "yaml"), "作品标题")
        or _md_key_val(raw, "作品标题")
        or (re.search(r"^#\s+(.+)$", raw, re.M).group(1).strip() if re.search(r"^#\s+(.+)$", raw, re.M) else "")
        or ""
    )

    # 3. 副标题（作为描述补充�?
    subtitle = (
        _yaml_val(fm, "副标�?)
        or _yaml_val(_md_code_block(raw, "yaml"), "副标�?)
        or ""
    )

    # 4. 创作描述（一句话简�?+ 创作描述正文�?
    desc = (
        _md_key_val(raw, "一句话简�?)
        or _md_key_val(raw, "一句话简介（100字以内）")
        or _yaml_val(fm, "一句话简�?)
    )
    # 追加正文中的创作描述�?
    desc_body = _md_key_val(raw, "创作描述")
    if desc_body and desc_body not in desc:
        desc = (desc + "\n\n" + desc_body).strip() if desc else desc_body
    if subtitle and subtitle not in (desc or ""):
        desc = (desc + "\n\n" + subtitle).strip() if desc else subtitle

    # 5. 人物
    char_list = _extract_characters(raw)

    # 6. 主题
    theme_list = _extract_themes(raw)

    # 7. 目标字数
    target_raw = _yaml_val(fm, "目标字数") or _md_key_val(raw, "目标字数")
    target_length = _safe_int(target_raw)

    # 8. 创作目的
    purpose_map = {
        "学术": "学术写作（论�?论述�?,
        "通俗": "通俗写作（给普通读者）",
        "备�?: "备考练习（校�?高考）",
        "个人": "个人创作（文学性）",
        "论文": "学术写作（论�?论述�?,
    }
    purpose_raw = _yaml_val(fm, "创作目的") or _md_key_val(raw, "创作目的")
    purpose = purpose_map.get(purpose_raw.strip()[:4], "通俗写作（给普通读者）")
    # 从正文中模糊匹配
    if purpose_raw not in purpose_map and purpose_raw:
        for k, v in purpose_map.items():
            if k in purpose_raw:
                purpose = v
                break

    # 9. 对标作品
    ref_works = (
        _yaml_val(fm, "对标作品")
        or _md_key_val(raw, "对标作品")
        or _md_key_val(raw, "对标作品（选填�?)
        or ""
    )

    # 10. 作品类型
    genre_map = {
        "人物": "历史人物故事",
        "事件": "历史事件演义",
        "文化": "文化史话",
        "社科": "社科随笔",
    }
    genre_raw = _yaml_val(fm, "作品类型") or _md_key_val(raw, "作品类型")
    genre = genre_map.get(genre_raw.strip()[:4], "历史事件演义")
    for k, v in genre_map.items():
        if k in genre_raw:
            genre = v
            break

    # 11. 风格
    style = "narrative_casual"  # 默认

    result = {
        "chapter_title": title,
        "description": desc,
        "characters": char_list,
        "themes": theme_list,
        "target_length": target_length,
        "genre": genre,
        "purpose": purpose,
        "ref_works": ref_works,
        "style": style,
    }

    # 至少需要标�?
    if not result["chapter_title"]:
        return None

    return result


# ════════════════════════════════════════════════════════════
# UI 组件�?
# ════════════════════════════════════════════════════════════

def render_header():
    """页面顶部标题栏（CSS 已整合到 _INK_GOLD_CSS，此函数保留为空兼容�?""
    pass  # CSS 已整合到顶层 _INK_GOLD_CSS，无需重复注入


def step_badge(step: int):
    """
    横向步骤进度条（S6 典雅墨韵版）
    显示 5 个步骤节点：当前=active，已完成=done，待完成=默认�?
    """
    STEP_NAMES = {
        0: "输入创作意图",
        1: "选择全书方案",
        2: "确认风格取材",
        3: "生成�?�?,
        4: "全书生成",
    }

    total_steps = 5
    # 构建 5 个节点的 HTML
    nodes_html = ""
    for i in range(total_steps):
        if i < step:
            state_cls = "done"
            num = "�?
        elif i == step:
            state_cls = "active"
            num = str(i + 1)
        else:
            state_cls = ""
            num = str(i + 1)
        label_text = STEP_NAMES.get(i, f"步骤{i+1}")
        nodes_html += (
            f'<div class="step-node {state_cls}">'
            f'<div class="step-circle">{num}</div>'
            f'<div class="step-label">{label_text}</div>'
            f'</div>'
        )

    html = f'<div class="step-progress-wrap">{nodes_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


def _get_selected_scheme():
    """获取当前选中的方案对�?""
    bd = st.session_state.get("book_design")
    sid = st.session_state.get("selected_scheme_id")
    if bd and sid:
        return next((s for s in bd.schemes if s.scheme_id == sid), None)
    return None


def tension_bar_chart(values: list[float], labels: list[str]):
    """渲染张力曲线 ASCII �?""
    bars = []
    for i, (v, lbl) in enumerate(zip(values, labels)):
        bar_len = int(v * 30)
        bar = "�? * bar_len + "�? * (30 - bar_len)
        pct = f"{v:.0%}"
        bars.append(f"第{i+1}�?[{bar}] {pct}  {lbl}")
    return "\n".join(bars)


# ════════════════════════════════════════════════════════════
# 页面一：意图输入（结构化）
# ════════════════════════════════════════════════════════════
def page_input():
    st.markdown('<div class="main-header">�?PT-047 社科智能体创作平�?/div>', unsafe_allow_html=True)

    # ── �?Markdown 模板导入（折叠区域）────────────────────
    with st.expander("📄 �?Markdown 模板导入创作意图", expanded=False):
        st.caption("使用流程：① 下载模板 �?�?�?AI 对话中讨论完�?�?�?上传/粘贴此文�?�?�?点击「解析并填入表单�?)

        col_imp_file, col_imp_text = st.columns([1, 1])
        uploaded_file = col_imp_file.file_uploader(
            "上传 .md 模板文件", type=["md"], label_visibility="collapsed"
        )

        template_text = col_imp_text.text_area(
            "或粘贴模板内�?,
            value="",
            placeholder="�?Markdown 模板内容粘贴于此�?,
            height=140,
            label_visibility="collapsed",
        )

        # 优先使用上传文件内容
        raw_text = ""
        if uploaded_file is not None:
            try:
                raw_text = uploaded_file.read().decode("utf-8")
            except Exception:
                raw_text = ""
        elif template_text.strip():
            raw_text = template_text

        col_parse, col_tips = st.columns([1, 2])
        parse_clicked = col_parse.button(
            "🔍 解析并填入表�?,
            use_container_width=True,
            type="primary",
            disabled=not raw_text.strip(),
        )
        with col_tips:
            st.caption(
                "💡 **提示**：先�?AI 对话窗口中讨论创作意图，�?AI 帮你完善人物、主题、叙事切入点�?
                "确认后再导出�?.md 文件导入此处。模板位置：`templates/创作意图模板.md`"
            )

        if parse_clicked and raw_text.strip():
            parsed = _parse_intent_template(raw_text)
            if parsed:
                st.session_state["_parsed_intent"] = parsed
                st.success(f"�?解析成功：{parsed['chapter_title']}，字段已填入下方表单")
            else:
                st.error("�?解析失败：未能识别作品标题。请确认模板格式，或手动填写下方表单�?)

    # ── 预填值（优先取解析结果，否则�?session_state）────
    parsed = st.session_state.get("_parsed_intent")
    _ss = st.session_state.get("user_input") or {}

    _default_title = (parsed["chapter_title"] if parsed else _ss.get("chapter_title")) or ""
    _default_desc = (parsed["description"] if parsed else _ss.get("description")) or ""
    _default_chars = (
        " / ".join(parsed["characters"]) if parsed and parsed.get("characters") else _ss.get("characters") or []
    )
    if isinstance(_default_chars, list):
        _default_chars = " / ".join(_default_chars)
    _default_themes = (
        " / ".join(parsed["themes"]) if parsed and parsed.get("themes") else _ss.get("themes") or []
    )
    if isinstance(_default_themes, list):
        _default_themes = " / ".join(_default_themes)
    _default_target = (parsed["target_length"] if parsed else _ss.get("target_length")) or 15000
    _default_purpose = (parsed["purpose"] if parsed else _ss.get("purpose")) or "通俗写作（给普通读者）"
    _default_ref = (parsed["ref_works"] if parsed else _ss.get("ref_works")) or ""
    _default_genre = (parsed["genre"] if parsed else _ss.get("genre")) or "历史事件演义"

    with st.form("intent_form", clear_on_submit=False):
        st.subheader("📝 告诉我你想写什�?)

        col1, col2 = st.columns([2, 1])

        with col1:
            chapter_title = st.text_input(
                "作品标题 / 主题",
                value=_default_title or "李世民玄武门兵变",
                placeholder="例如：玄武门之变的谋略与果断",
                help="这是你的作品标题或核心主�?
            )
            description = st.text_area(
                "创作描述",
                value=_default_desc or (
                    '武德九年六月初四，秦王李世民在长安玄武门设伏，射杀太子李建成、齐王李元吉�?
                    '随后迫使父亲李渊禅位，开创贞观之治。这是一场改变中国历史走向的宫廷政变�?
                    '也是一曲关于野心、决断与团队默契的英雄史诗�?
                ),
                height=140,
                help="描述你想要的故事内容、人物、情感基�?
            )

        with col2:
            characters = st.text_input(
                "主要人物（用 / 分隔�?,
                value=_default_chars or "李世�?/ 李建�?/ 李元�?/ 李渊 / 尉迟敬德 / 房玄�?,
                help="作品中的核心人物"
            )
            themes = st.text_input(
                "核心主题（用 / 分隔�?,
                value=_default_themes or "权力与道�?/ 团队协作 / 历史转折 / 果断决策",
                help="作品要表达的核心主题"
            )
            target_length = st.slider(
                "目标字数",
                min_value=1000, max_value=80000,
                value=int(_default_target) if _default_target else 15000,
                step=1000,
                help="预计全文总字数�?0000字以下推荐直接用提示词，15000字以上建议分段创作�?
            )

        # ── 新增结构化字�?──────────────────────────────
        st.markdown("---")
        col3, col4 = st.columns([1, 1])
        purposes = ["学术写作（论�?论述�?, "通俗写作（给普通读者）", "备考练习（校�?高考）", "个人创作（文学性）"]
        genres = ["历史人物故事", "历史事件演义", "文化史话", "社科随笔", "其他"]
        with col3:
            purpose = st.selectbox(
                "创作目的",
                options=purposes,
                index=purposes.index(_default_purpose) if _default_purpose in purposes else 1,
                help="影响文风建议和取材倾向"
            )
        with col4:
            ref_works = st.text_input(
                "对标作品（选填�?,
                value=_default_ref or "",
                placeholder="例如：《苏东坡传》林语堂，《千年一叹�?,
                help="AI 会参考这些作品的叙事风格"
            )
        genre = st.selectbox(
            "作品类型",
            options=genres,
            index=genres.index(_default_genre) if _default_genre in genres else 0,
        )

        st.markdown("---")

        submitted = st.form_submit_button(
            "🚀 生成全书设计方案 �?,
            use_container_width=True,
            type="primary",
        )

        if submitted:
            if not chapter_title.strip():
                st.error("请输入作品标�?)
                return

            char_list = [c.strip() for c in characters.split("/") if c.strip()]
            theme_list = [t.strip() for t in themes.split("/") if t.strip()]

            st.session_state["user_input"] = {
                "chapter_title": chapter_title.strip(),
                "description": description.strip(),
                "characters": char_list,
                "themes": theme_list,
                "target_length": target_length,
                "genre": genre,
                "purpose": purpose,
                "ref_works": ref_works.strip(),
                "style": "narrative_casual",
            }
            st.session_state["step"] = 1
            st.session_state["error"] = None
            # ── 彻底重置所有下游状态，防止旧数据残�?──
            st.session_state["book_design"] = None
            st.session_state["selected_scheme_id"] = None
            st.session_state["selected_style"] = None
            st.session_state["custom_materials"] = None
            st.session_state["suggested_materials"] = None
            st.session_state["unified"] = None
            st.session_state["chapter_contents"] = []
            st.session_state["chapter1_approved"] = False
            st.session_state["style_phase"] = None    # 新增：清除旧风格样章缓存
            st.session_state["_prev_topic"] = None     # 新增：清除主题变更检测记�?
            st.session_state["_parsed_intent"] = None   # 新增：清除模板解析缓�?
            st.session_state["_next_part_to_generate"] = 2
            st.session_state["_completed_parts"] = []
            st.session_state["mats_confirmed"] = False
            st.session_state["generation_started"] = False
            # 清除 LLM 相关缓存（避�?BookDesignGenerator 等持有旧数据�?
            try:
                st.cache_data.clear()
                st.cache_resource.clear()
            except Exception:
                pass
            st.rerun()

    # 底部说明
    st.markdown("""
    <div style="margin-top:2em; padding:1em; background:#f8f9fa; border-radius:8px; font-size:0.85em; color:#666;">
    💡 <b>工作流程�?/b>填写意图 �?<b>选择全书设计方案</b>（AI生成3-4套方案） �?确认风格与取�?�?生成�?章（确认后再生成全书�?
    &nbsp;|&nbsp; 📄 <a href="#" onclick="return false;"><b>�?Markdown 模板导入</b></a>（上方展开�?
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# 页面二：选择全书设计方案
# ════════════════════════════════════════════════════════════

_SCHEME_COLORS = {
    "A": ("#523427", "#fdfcf9"),  # 墨褐
    "B": ("#5d8a4a", "#f0faf0"),  # 翠玉
    "C": ("#6a4a9a", "#f5f0ff"),  # 绛紫
    "D": ("#967c46", "#fdfcf9"),  # 赭石
}


def _part_label(scheme: "BookScheme") -> str:
    """返回方案�?�?标签（如果有�?""
    if not scheme.chapters:
        return ""
    parts = {ch.part for ch in scheme.chapters if ch.part is not None}
    if parts:
        return f"（{len(parts)} 部）"
    return ""


def _scheme_card_html(scheme: "BookScheme", is_selected: bool) -> str:
    """渲染单套方案卡片 HTML"""
    sid = scheme.scheme_id
    title_color, bg_color = _SCHEME_COLORS.get(sid, ("#2c3e50", "#f8f9fa"))
    border = "2px solid #967c46" if is_selected else "1.5px solid #d4c4a8"
    check = "�?" if is_selected else "&nbsp;&nbsp;"

    # ── 全书梗概与高�?────────────────────────────────
    # 找高潮章节（张力最高的�?
    climax_idx = max(
        range(len(scheme.chapters)),
        key=lambda i: scheme.chapters[i].tension_level
    ) if scheme.chapters else -1

    arc_rows = ""
    for i, ch in enumerate(scheme.chapters):
        is_climax = (i == climax_idx)
        marker = '<span style="background:#b54a4a;color:#fff;padding:1px 7px;border-radius:10px;font-size:10px;font-weight:700;margin-left:4px;">高潮</span>' if is_climax else ""
        # 优先显示 subtitle，其�?chapter_arc，再�?title
        display_text = ch.subtitle if ch.subtitle and ch.subtitle not in ("章节副标�?, "章节副标题（自拟�?) \
            else (ch.chapter_arc if ch.chapter_arc and ch.chapter_arc not in ("本章叙事�?, "本章叙事弧（自拟�?) else ch.title)
        tension_pct = int(ch.tension_level * 100)
        bar_w = max(4, int(ch.tension_level * 60))
        arc_rows += (
            f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:10px;">'
            f'<div style="width:20px;height:20px;border-radius:50%;background:{title_color}40;color:{title_color};'
            f'font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;">'
            f'{ch.chapter}</div>'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">'
            f'<span style="font-weight:600;font-size:13px;color:#523427;">{ch.title}</span>'
            f'{marker}'
            f'</div>'
            f'<div style="font-size:12px;color:#666;line-height:1.5;margin-bottom:4px;">{display_text}</div>'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="flex:1;height:4px;background:#eee;border-radius:2px;overflow:hidden;">'
            f'<div style="width:{bar_w}px;height:100%;background:{"#b54a4a" if is_climax else "#8a7235"};border-radius:2px;"></div>'
            f'</div>'
            f'<span style="font-size:10px;color:{"#b54a4a" if is_climax else "#888"};font-weight:600;">{tension_pct}%</span>'
            f'</div>'
            f'</div></div>'
        )

    # ── 章节简览（带分部结构）─────────────────────
    chapters_list_parts = ""
    if scheme.chapters and scheme.chapters[0].part is not None:
        from itertools import groupby
        by_part = {}
        for ch in scheme.chapters:
            p = ch.part or 0
            if p not in by_part:
                by_part[p] = []
            by_part[p].append(ch)
        for part_num in sorted(by_part.keys()):
            part_chs = by_part[part_num]
            part_title = part_chs[0].part_title if part_chs else f"第{part_num}�?
            chapters_list_parts += (
                f'<div style="margin-bottom:0.3em; padding:0.3em 0.5em; '
                f'background:#fff; border-left:3px solid {title_color}; font-weight:600; font-size:0.9em;">'
                f'{part_title}</div>'
            )
            for ch in part_chs:
                chapters_list_parts += (
                    f'<div style="padding:0.1em 0.5em 0.1em 1em; font-size:0.82em; color:#444;">'
                    f'第{ch.chapter}章「{ch.title}�?/div>'
                )
    else:
        chapters_list = "<br>".join(
            f"第{ch.chapter}章「{ch.title}�? for ch in scheme.chapters
        )
        chapters_list_parts = chapters_list

    return f"""
    <div style="border:{border}; background:{bg_color}; border-radius:10px; padding:1.2em; margin-bottom:0.8em;">
        <div style="display:flex; align-items:center; gap:0.5em; margin-bottom:0.5em;">
            <div style="background:{title_color}; color:white; padding:0.2em 0.7em; border-radius:1em; font-weight:700; font-size:1.1em;">
                方案{sid}
            </div>
            <div style="font-weight:700; font-size:1.05em; color:#523427;">{check}{scheme.scheme_title}</div>
        </div>
        <div style="font-size:0.82em; color:#555; margin-bottom:0.5em;">
            <b>结构�?/b>{scheme.structure_type} &nbsp;|&nbsp; <b>视角�?/b>{scheme.perspective}
        </div>
        <div style="font-size:0.85em; color:#333; margin-bottom:0.5em; line-height:1.5;">
            <b>主线�?/b>{scheme.main_arc}
        </div>
        <div style="font-size:0.82em; color:#666; margin-bottom:0.4em;">
            <b>切入角度�?/b>{scheme.focus_angle}
        </div>
        <div style="background:rgba(150,124,70,0.08); border:1px solid rgba(150,124,70,0.2); border-radius:6px; padding:0.5em 0.7em; margin-bottom:0.5em; font-size:0.82em;">
            �?亮点：{scheme.highlight}
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5em; font-size:0.82em; color:#555; margin-bottom:0.4em;">
            <div>📖 {scheme.chapter_count} �?| ~{scheme.estimated_words} 字{_part_label(scheme)}</div>
            <div>🖌�?{scheme.style_tone}</div>
        </div>
        <details style="font-size:0.8em; color:#666;">
            <summary style="cursor:pointer; font-weight:600;">�?叙事结构</summary>
            <div style="margin-top:0.4em; padding:0.5em 0.7em; background:white; border-radius:6px;">
                <div style="margin-bottom:6px; font-size:12px; color:#555; line-height:1.6;">
                    <b>叙事主线�?/b>{scheme.main_arc}
                </div>
                <div style="font-size:12px; color:#777; line-height:1.6;">
                    <b>切入角度�?/b>{scheme.focus_angle}
                </div>
            </div>
        </details>
        <details open style="font-size:0.8em; color:#666; margin-top:0.3em;">
            <summary style="cursor:pointer; font-weight:600;">�?全书梗概与高�?/summary>
            <div style="margin-top:0.4em; padding:0.6em 0.8em; background:white; border-radius:6px;">
                {arc_rows}
            </div>
        </details>
    </div>
    """


def page_scheme_selection():
    """步骤二：展示 AI 生成�?3-4 套全书设计方案，供用户选择"""
    user_input = st.session_state["user_input"]
    topic = user_input.get("chapter_title", "?")
    llm = get_llm()

    # ── 主题变化检测（step 1 也需要，防止 page_input() 直接跳转时的残留）──
    _check_topic_change(user_input)

    st.markdown(f"""
    <div class="main-header">📋 全书设计方案 · 请选择一�?/div>
    <div style="margin-bottom:1em; padding:0.8em; background:#fef9e7; border-radius:8px; border-left:4px solid #f39c12; font-size:0.9em;">
    📌 作品�?b>{topic}</b>
    &nbsp;|&nbsp; 目标字数：{user_input.get('target_length', 0)}
    &nbsp;|&nbsp; 目的：{user_input.get('purpose', '一般写�?)}
    </div>
    """, unsafe_allow_html=True)

    progress_ph = st.empty()

    # ── 生成或加载设计方�?─────────────────────────────
    if st.session_state.get("book_design") is None:
        with st.spinner("正在根据你的主题生成 3 套全书设计方案（�?15 秒）…�?):
            try:
                from progressive_guide import BookDesignGenerator
                gen = BookDesignGenerator(llm)
                bd = gen.generate(user_input, num_schemes=3)
                st.session_state["book_design"] = bd
                progress_ph.success("�?方案已生成！")
            except Exception as e:
                st.error(f"方案生成失败：{e}")
                return

    bd = st.session_state["book_design"]
    selected_id = st.session_state.get("selected_scheme_id")

    # ── 展示方案卡片 + 选择 ────────────────────────────
    for scheme in bd.schemes:
        is_sel = selected_id == scheme.scheme_id
        html = _scheme_card_html(scheme, is_sel)
        st.markdown(html, unsafe_allow_html=True)

        col_sel, col_detail = st.columns([1, 3])
        with col_sel:
            if st.button(
                f"{'�?已选择' if is_sel else '�?选择此方�?}",
                key=f"select_scheme_{scheme.scheme_id}",
                use_container_width=True,
                type="primary" if not is_sel else "secondary",
            ):
                st.session_state["selected_scheme_id"] = scheme.scheme_id
                st.rerun()
        with col_detail:
            core = scheme.core_materials[:5]
            st.caption(f"核心取材：{' / '.join(core) if core else '�?}")

        st.markdown("---")

    # ── 已选方案详情摘�?───────────────────────────────
    if selected_id:
        chosen = next((s for s in bd.schemes if s.scheme_id == selected_id), None)
        if chosen:
            st.markdown(f"""
            <div style="padding:1em; background:#eafaf1; border-radius:8px; border:2px solid #27ae60; margin:0.8em 0;">
                <div style="font-weight:700; margin-bottom:0.4em; color:#1e8449;">
                    �?已选方�?{chosen.scheme_id}：{chosen.scheme_title}
                </div>
                <div style="font-size:0.88em; color:#555;">
                    <b>主线�?/b>{chosen.main_arc}<br>
                    <b>章节�?/b>{chosen.chapter_count} 章（{' / '.join(ch.title for ch in chosen.chapters)}�?
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_confirm, col_regen, col_back = st.columns([2, 1, 1])
            with col_confirm:
                if st.button("�?确认方案，进入下一�?�?, use_container_width=True, type="primary"):
                    st.session_state["step"] = 2
                    st.session_state["selected_style"] = None  # 重置风格选择
                    st.session_state["custom_materials"] = None
                    st.session_state["suggested_materials"] = None
                    st.session_state["unified"] = None
                    st.rerun()
            with col_regen:
                if st.button("🔄 重新生成", use_container_width=True):
                    st.session_state["book_design"] = None
                    st.session_state["selected_scheme_id"] = None
                    st.rerun()
            with col_back:
                if st.button("�?返回修改", use_container_width=True):
                    st.session_state["step"] = 0
                    st.rerun()
    else:
        st.info("👆 请从上方选择一套方案，确认后进入下一�?)

    # ── 底部说明 ─────────────────────────────────────
    st.markdown("""
    <div style="margin-top:1.5em; padding:0.8em; background:#f8f9fa; border-radius:8px; font-size:0.82em; color:#666;">
    💡 <b>如何选方案：</b>每套方案的结构类型、叙事视角、切入角度均不同。点击「选择此方案」后，底部出现确认按钮�?br>
    选择困难？优先选主线最吸引你的方案，或章节数与你期望最接近的方案�?
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# 页面三：确认风格与取材（基于所选方案）
# ════════════════════════════════════════════════════════════
def page_preview():
    user_input = st.session_state["user_input"]
    bd = st.session_state.get("book_design")
    selected_scheme = None
    if bd:
        selected_scheme = next(
            (s for s in bd.schemes if s.scheme_id == st.session_state.get("selected_scheme_id")),
            None,
        )
    scheme_name = f"方案{selected_scheme.scheme_id}「{selected_scheme.scheme_title}�? if selected_scheme else "�?
    llm = get_llm()

    st.markdown(f"""
    <div class="main-header">👁 确认风格与取�?/div>
    <div style="margin-bottom:1em; padding:0.8em; background:#d4efdf; border-radius:8px; border-left:4px solid #27ae60; font-size:0.9em;">
    📋 已选方案：<b>{scheme_name}</b>
    &nbsp;|&nbsp; 作品�?b>{user_input.get('chapter_title', '')}</b>
    </div>
    """, unsafe_allow_html=True)
    _check_topic_change(user_input)

    st.markdown(f"""
    <div class="main-header">👁 创作预览 · 确认后再生成</div>
    <div style="margin-bottom:1em; padding:0.8em; background:#fef9e7; border-radius:8px; border-left:4px solid #f39c12; font-size:0.9em;">
    📌 作品�?b>{user_input['chapter_title']}</b>
    &nbsp;|&nbsp; 人物：{' / '.join(user_input['characters'][:3])}
    &nbsp;|&nbsp; 目标字数：{user_input['target_length']}
    </div>
    """, unsafe_allow_html=True)

    progress_ph = st.empty()

    # ════════════════════════════════════════════════════════
    # 步骤一：选择风格（不变）
    # ════════════════════════════════════════════════════════
    st.markdown("### �?步骤一：选择你喜欢的风格")
    st.caption("下面是根据你的主题实时生成的 3 种风格样章，点击选择一�?)

    if st.session_state["style_phase"] is None:
        with st.spinner("正在生成 3 种风格样章，请稍候（�?20 秒）…�?):
            progress_ph.progress(10, text="Phase 1: 风格尝味")
            try:
                composer, style_phase = run_phase1(llm, user_input)
                st.session_state["style_phase"] = (composer, style_phase)
                progress_ph.progress(50, text="风格样章已生�?)
            except Exception as e:
                st.error(f"风格样章生成失败：{e}")
                return
    else:
        composer, style_phase = st.session_state["style_phase"]
        progress_ph.progress(20, text="风格样章已就�?)

    sp = style_phase.raw_result
    col1, col2, col3 = st.columns(3)
    selected_style = st.session_state.get("selected_style", None)

    for col, sample in zip([col1, col2, col3], sp.samples):
        is_sel = (selected_style == sample.style)
        border = "3px solid #27ae60" if is_sel else "2px solid #ddd"
        bg = "#f0fff4" if is_sel else "#fff"
        check = "�?" if is_sel else "  "
        with col:
            st.markdown(f"""
            <div style="border:{border}; background:{bg}; border-radius:8px; padding:1em; min-height:260px;">
                <div style="font-weight:700; font-size:1.05em; margin-bottom:0.3em;">{check}{sample.label}</div>
                <div style="font-size:0.8em; color:#888; margin-bottom:0.6em;">{sample.description}</div>
                <div style="font-size:0.85em; color:#555; line-height:1.6; border-top:1px solid #eee; padding-top:0.6em;">
                    {sample.content[:200]}�?
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"选择此风�?, key=f"sel_{sample.style}", use_container_width=True):
                st.session_state["selected_style"] = sample.style
                composer.apply_style_choice(style_phase, sample.style)
                st.session_state["style_phase"] = (composer, style_phase)
                st.session_state["unified"] = None   # 换风�?�?重置框架
                st.rerun()

    if selected_style:
        sel_label = next((s.label for s in sp.samples if s.style == selected_style), selected_style)
        st.success(f"�?风格已锁定：{sel_label}")

    # ════════════════════════════════════════════════════════
    # 步骤二：AI 推荐取材（核心新功能�?
    # ════════════════════════════════════════════════════════
    st.markdown("### �?步骤二：AI 推荐取材（基于你的主题）")
    st.info("""
    **�?核心骨架**：叙事离不开的核心事�?人物�?*不可取消**（缺了故事不完整�? 
    **�?丰富层次**：锦上添花的素材，可根据篇幅自由勾�?
    """)

    # ── 获取或生�?AI 推荐 ─────────────────────────────
    if st.session_state.get("suggested_materials") is None:
        with st.spinner("正在根据「{}」生成取材推荐（�?8 秒）…�?.format(user_input.get("chapter_title", ""))):
            try:
                suggestions = generate_material_suggestions(llm, user_input)
                st.session_state["suggested_materials"] = suggestions
                # 初始�?custom_materials = 所有推荐的名字（字符串，set() 可用�?
                all_evts = suggestions.get("events", [])
                all_figs = suggestions.get("figures", [])
                st.session_state["custom_materials"] = {
                    "events": [it.get("name", "") for it in all_evts if it.get("name")],
                    "figures": [it.get("name", "") for it in all_figs if it.get("name")],
                    "themes": list(suggestions.get("topics", [])),
                }
            except Exception as e:
                st.warning(f"AI推荐生成失败，将使用你输入的人物：{e}")
                fallback_chars = user_input.get("characters", [])
                st.session_state["suggested_materials"] = {
                    "events": [],
                    "figures": [
                        {"name": c, "reason": "（你输入的主角人物）", "mandatory": True}
                        for c in fallback_chars
                    ],
                    "themes": list(user_input.get("themes", [])),
                }
                st.session_state["custom_materials"] = {
                    "events": [],
                    "figures": list(fallback_chars),   # 只存名字字符串，不存 dict
                    "themes": list(user_input.get("themes", [])),
                }
        st.rerun()   # 重新渲染带推荐的界面

    suggestions = st.session_state.get("suggested_materials", {})
    all_events = suggestions.get("events", [])
    all_figures = suggestions.get("figures", [])

    # ── 初始�?custom_materials ────────────────────────
    # custom_materials 只存被选中的名字（字符串），用于框架生�?
    mats = st.session_state.get("custom_materials")
    if mats is None:
        # 首次初始化：从建议中取所有名字（必选的默认选中�?
        mats = {
            "events": [it.get("name", "") for it in all_events if it.get("name")],
            "figures": [it.get("name", "") for it in all_figures if it.get("name")],
            "themes": suggestions.get("topics", []),
        }
        st.session_state["custom_materials"] = mats

    sel_events_set = set(mats.get("events", []))
    sel_figures_set = set(mats.get("figures", []))

    # ── 展示素材推荐（必�?vs 可�?+ 理由）────────────
    # 把建议数据按 mandatory 分组
    def group_by_mandatory(items):
        mandatory = [it for it in items if it.get("mandatory", False)]
        optional = [it for it in items if not it.get("mandatory", False)]
        return mandatory, optional

    mand_evts, opt_evts = group_by_mandatory(all_events)
    mand_figs, opt_figs = group_by_mandatory(all_figures)

    col_evts, col_figs = st.columns(2)

    with col_evts:
        st.markdown("**📌 历史事件**")
        if all_events:
            # ── 必选（核心骨架，不可取消）─────────────────
            if mand_evts:
                st.markdown("""
                <div style="font-size:0.8em; color:#c0392b; font-weight:600; margin-bottom:0.4em;">
                    �?核心骨架（必选，不可取消�?
                </div>
                """, unsafe_allow_html=True)
                for it in mand_evts:
                    name = it.get("name", "")
                    reason = it.get("reason", "")
                    if name and name not in sel_events_set:
                        sel_events_set.add(name)
                    st.markdown(f"""
                    <div style="display:flex; align-items:flex-start; gap:0.4em; margin-bottom:0.5em;">
                        <div style="color:#c0392b; font-size:1em; margin-top:0.1em;">�?/div>
                        <div>
                            <div style="font-weight:600; color:#2c3e50;">{name}</div>
                            <div style="font-size:0.78em; color:#888; margin-top:0.1em;">{reason}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── 可选（丰富故事，可勾选）──────────────────
            if opt_evts:
                st.markdown("""
                <div style="font-size:0.8em; color:#27ae60; font-weight:600; margin:0.6em 0 0.4em;">
                    �?丰富层次（可选，勾选后使用�?
                </div>
                """, unsafe_allow_html=True)
                for idx, it in enumerate(opt_evts):
                    name = it.get("name", "")
                    reason = it.get("reason", "")
                    checked = name in sel_events_set
                    # 理由 �?勾选框 纵向排列，让理由更突�?
                    st.markdown(f"""
                    <div style="display:flex; align-items:flex-start; gap:0.5em; margin-bottom:0.6em; padding:0.5em;
                                background:#f0fff4; border-radius:6px; border:1px solid #a9dfbf;">
                        <div style="color:#27ae60; font-size:1em; margin-top:0.15em;">�?/div>
                        <div style="flex:1;">
                            <div style="font-size:0.82em; color:#555; line-height:1.5; margin-bottom:0.35em;">
                                💡 {reason}
                            </div>
                            <div style="display:flex; align-items:center; gap:0.4em;">
                                <div style="font-weight:600; color:#2c3e50; font-size:0.92em;">{name}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    new_checked = st.checkbox(
                        f"使用「{name}�?,
                        value=checked,
                        key=f"cb_evt_opt_{idx}_{name}",
                    )
                    if new_checked:
                        sel_events_set.add(name)
                    else:
                        sel_events_set.discard(name)
            elif mand_evts:
                # 有必选但无可选时，友好提�?
                st.caption("　💡 该主题暂无额外可选事件，更多素材可手动添�?)
        else:
            st.caption("（暂无推荐事件，可手动添加）")

        # 保存
        mats["events"] = list(sel_events_set)
        st.session_state["custom_materials"] = mats

    with col_figs:
        st.markdown("**👤 关键人物**")
        if all_figures:
            # ── 必选（核心骨架）─────────────────────────
            if mand_figs:
                st.markdown("""
                <div style="font-size:0.8em; color:#c0392b; font-weight:600; margin-bottom:0.4em;">
                    �?核心人物（必选，不可取消�?
                </div>
                """, unsafe_allow_html=True)
                for it in mand_figs:
                    name = it.get("name", "")
                    reason = it.get("reason", "")
                    if name and name not in sel_figures_set:
                        sel_figures_set.add(name)
                    st.markdown(f"""
                    <div style="display:flex; align-items:flex-start; gap:0.4em; margin-bottom:0.5em;">
                        <div style="color:#c0392b; font-size:1em; margin-top:0.1em;">�?/div>
                        <div>
                            <div style="font-weight:600; color:#2c3e50;">{name}</div>
                            <div style="font-size:0.78em; color:#888; margin-top:0.1em;">{reason}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── 可选（丰富故事）──────────────────────────
            if opt_figs:
                st.markdown("""
                <div style="font-size:0.8em; color:#27ae60; font-weight:600; margin:0.6em 0 0.4em;">
                    �?辅助人物（可选，勾选后使用�?
                </div>
                """, unsafe_allow_html=True)
                for idx, it in enumerate(opt_figs):
                    name = it.get("name", "")
                    reason = it.get("reason", "")
                    checked = name in sel_figures_set
                    st.markdown(f"""
                    <div style="display:flex; align-items:flex-start; gap:0.5em; margin-bottom:0.6em; padding:0.5em;
                                background:#f0fff4; border-radius:6px; border:1px solid #a9dfbf;">
                        <div style="color:#27ae60; font-size:1em; margin-top:0.15em;">�?/div>
                        <div style="flex:1;">
                            <div style="font-size:0.82em; color:#555; line-height:1.5; margin-bottom:0.35em;">
                                💡 {reason}
                            </div>
                            <div style="display:flex; align-items:center; gap:0.4em;">
                                <div style="font-weight:600; color:#2c3e50; font-size:0.92em;">{name}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    new_checked = st.checkbox(
                        f"使用「{name}�?,
                        value=checked,
                        key=f"cb_fig_opt_{idx}_{name}",
                    )
                    if new_checked:
                        sel_figures_set.add(name)
                    else:
                        sel_figures_set.discard(name)
            elif mand_figs:
                # 有必选但无可选时，友好提�?
                st.caption("　💡 该主题暂无额外可选人物，更多素材可手动添�?)
        else:
            st.caption("（暂无推荐人物，可手动添加）")

        mats["figures"] = list(sel_figures_set)
        st.session_state["custom_materials"] = mats

    # ── 手动补充 ────────────────────────────────────────
    st.markdown("**✏️ 补充添加素材**")
    col_add_e, col_add_f = st.columns(2)

    with col_add_e:
        new_evt = st.text_input(
            "补充事件（如：乌台诗案）", placeholder="输入后点添加",
            key="input_add_event", label_visibility="collapsed"
        )
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("�?添加事件", key="btn_add_evt"):
                if new_evt.strip() and new_evt.strip() not in mats["events"]:
                    mats["events"].append(new_evt.strip())
                    sel_events_set.add(new_evt.strip())
                    st.session_state["custom_materials"] = mats
                    st.rerun()
        with c2:
            st.caption(f"当前 {len(mats.get('events', []))} �?)

    with col_add_f:
        new_fig = st.text_input(
            "补充人物（如：苏辙）", placeholder="输入后点添加",
            key="input_add_fig", label_visibility="collapsed"
        )
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("�?添加人物", key="btn_add_fig"):
                if new_fig.strip() and new_fig.strip() not in mats["figures"]:
                    mats["figures"].append(new_fig.strip())
                    sel_figures_set.add(new_fig.strip())
                    st.session_state["custom_materials"] = mats
                    st.rerun()
        with c2:
            st.caption(f"当前 {len(mats.get('figures', []))} 个人�?)

    # ── 取材确认汇�?────────────────────────────────────
    mats_summary = st.session_state.get("custom_materials", {})
    evts_final = mats_summary.get("events", [])
    figs_final = mats_summary.get("figures", [])

    st.markdown(f"""
    <div style="padding:0.8em; background:#eafaf1; border-radius:8px;
                border:1px solid #a9dfbf; margin:0.8em 0; font-size:0.9em;">
        📋 <b>取材已就绪：</b>
        事件 <b>{len(evts_final)}</b> �?
        {', '.join(evts_final[:5]) if evts_final else '（无�?}
        &nbsp;|&nbsp;
        人物 <b>{len(figs_final)}</b> �?
        {', '.join(figs_final[:5]) if figs_final else '（无�?}
    </div>
    """, unsafe_allow_html=True)

    # ── 生成章节框架按钮 ────────────────────────────────
    has_style = st.session_state.get("selected_style") is not None
    has_mats = len(evts_final) > 0 or len(figs_final) > 0

    col_gen, col_regen = st.columns([2, 1])
    with col_gen:
        if st.button(
            "🔄 用这些素材生成章节框�?,
            use_container_width=True, type="primary",
            disabled=not has_style,
        ):
            if not has_style:
                st.warning("请先选择风格（步骤一�?)
            else:
                _build_and_show_framework(
                    composer, style_phase, user_input,
                    mats_summary, progress_ph,
                )

    with col_regen:
        if st.button("🔄 重新生成 AI 推荐", use_container_width=True):
            # 重置取材，重新调�?LLM
            st.session_state["suggested_materials"] = None
            st.session_state["custom_materials"] = None
            st.session_state["unified"] = None
            st.rerun()

    # ════════════════════════════════════════════════════════
    # 步骤三：章节框架预览（已生成时显示）
    # ════════════════════════════════════════════════════════
    if st.session_state.get("unified") is not None:
        unified = st.session_state["unified"]
        fr = unified.framework_result
        chapters = fr.chapters

        st.markdown("### �?步骤三：预览章节框架")
        st.caption("以下是基于你的取材生成的章节结构，确认后开始生成正�?)

        tension_values = [ch.tension_level for ch in chapters]
        emoji_map = {"开篇引�?: "🌒", "矛盾积累": "🌓", "高潮时刻": "🌕",
                     "回落收束": "🌗", "结局": "🌑", "发展展开": "🌔",
                     "高潮与衰�?: "�?, "上升至高�?: "🔥", "高峰与衰�?: "�?,
                     "冲突展开": "🌔"}

        for ch in chapters:
            emoji = emoji_map.get(ch.tension_label, "📖")
            pct = f"{ch.tension_level:.0%}"
            with st.container():
                st.markdown(f"""
                <div class="chapter-card">
                    <div style="display:flex; align-items:center; gap:0.5em; margin-bottom:0.4em;">
                        <span style="font-size:1.2em;">{emoji}</span>
                        <span style="font-weight:700; font-size:1.05em;">第{ch.chapter}章「{ch.title}�?/span>
                        <span style="background:#ebf5fb; color:#2980b9; padding:0.15em 0.6em;
                                    border-radius:1em; font-size:0.8em; margin-left:auto;">{pct} {ch.tension_label}</span>
                    </div>
                    <div style="color:#555; font-size:0.9em; margin-bottom:0.3em;">{ch.subtitle}</div>
                    <div style="font-size:0.8em; color:#888;">事件：{' / '.join(ch.key_events[:2]) if ch.key_events else '�?}&nbsp;&nbsp;人物：{' / '.join(ch.key_figures[:2]) if ch.key_figures else '�?}</div>
                    <div style="margin-top:0.3em;">
                        <div class="tension-bar" style="width:{int(ch.tension_level*100)}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown("**全书梗概**")
            for i, ch in enumerate(chapters):
                pct = int(ch.tension_level * 100)
                is_climax = ch.tension_level == max(c.tension_level for c in chapters)
                badge = "🔴 高潮" if is_climax else f"张力 {pct}%"
                st.markdown(
                    f"**第{ch.chapter}�?{ch.title}** &nbsp;"
                    f"<span style='color:{'#b54a4a' if is_climax else '#888'}; font-size:0.85em;'>{badge}</span>"
                    f"\n\n{ch.subtitle}\n",
                    unsafe_allow_html=True,
                )
        with col_right:
            st.markdown("**本次取材清单**")
            st.markdown(f"事件 **{len(evts_final)}** 个：" + " / ".join(evts_final[:6] if evts_final else ["（无�?]))
            st.markdown(f"人物 **{len(figs_final)}** 个：" + " / ".join(figs_final[:6] if figs_final else ["（无�?]))

        st.markdown("---")
        st.markdown("### �?确认后生成第1�?)
        style_label = next(
            (s.label for s in (style_phase.raw_result.samples if style_phase else [])
             if s.style == st.session_state.get("selected_style")),
            "通俗故事�?,
        )
        col_confirm, col_reset = st.columns([2, 1])
        with col_confirm:
            if st.button("�?全部确认，生成第1�?�?, use_container_width=True, type="primary"):
                # 直接从所选方案构�?unified（无需再次 LLM 调用�?
                if selected_scheme:
                    unified = _finalize_scheme_to_unified(
                        selected_scheme, style_label, mats_summary, llm
                    )
                else:
                    unified = composer.apply_unified_feedback(unified, {"action": "full_approve"})
                st.session_state["unified"] = unified
                st.session_state["step"] = 3
                st.session_state["generation_started"] = True
                progress_ph.empty()
                st.rerun()
        with col_reset:
            if st.button("�?重新开�?, use_container_width=True):
                _reset_all_state()
                st.rerun()


def _check_topic_change(user_input):
    """
    检测用户是否在 step 1/2 期间更换了主题，如果是则彻底清除所有缓存状态�?

    触发条件：prev_topic != curr_topic（真实的主题变化�?
    不触发的情况�?
      - prev_topic is None（刚进入/刚提交表单，page_input() 已直接清除状态）
      - prev_topic == curr_topic（主题未变，正常渲染�?
    """
    prev_topic = st.session_state.get("_prev_topic", None)
    curr_topic = user_input.get("chapter_title", "")

    # 真实主题变化 �?清除所有旧缓存
    if prev_topic is not None and prev_topic != curr_topic:
        logger = logging.getLogger("gui")
        logger.warning(f"[Topic Change] '{prev_topic}' �?'{curr_topic}' �?clearing ALL cached state")
        st.session_state["style_phase"] = None
        st.session_state["suggested_materials"] = None
        st.session_state["custom_materials"] = None
        st.session_state["unified"] = None
        st.session_state["book_design"] = None
        st.session_state["selected_scheme_id"] = None
        st.session_state["selected_style"] = None
        st.session_state["step"] = 1
        st.rerun()

    # 更新主题记录（无论是否变化都更新，保证下次比较准确）
    st.session_state["_prev_topic"] = curr_topic



def _finalize_scheme_to_unified(selected_scheme, style_label, mats_summary, llm) -> "UnifiedPreviewResult":
    """
    将用户选中的方�?+ 风格 + 取材直接转为 UnifiedPreviewResult�?
    无需再次调用 LLM 生成章节框架（章节已由方案提供）�?
    """
    from progressive_guide import UnifiedPreviewResult

    # 从方案构建章节大纲（来自 BookScheme.chapters�?
    chapter_outline = []
    for ch in selected_scheme.chapters:
        chapter_outline.append({
            "chapter": ch.chapter,
            "title": ch.title,
            "subtitle": ch.subtitle,
            "tension": ch.tension_level,
            "tension_label": ch.tension_label,
            "estimated_chars": ch.word_target,
        })

    enhanced = {
        "theme": selected_scheme.main_arc,
        "style_label": style_label,
        "overall_theme": selected_scheme.focus_angle,
        "tension_arc": selected_scheme.tension_arc,
        "chapter_outline": chapter_outline,
        "materials": {
            "events": mats_summary.get("events", []),
            "figures": mats_summary.get("figures", []),
        },
        "scheme_id": selected_scheme.scheme_id,
        "scheme_title": selected_scheme.scheme_title,
    }

    # 构建 mock UnifiedPreviewResult（只�?enhanced_context�?
    class _SimpleResult:
        def __init__(self, ec):
            self.enhanced_context = ec

    return _SimpleResult(enhanced)


def _build_and_show_framework(composer, style_phase, user_input, mats_summary, progress_ph):
    """构建 mock_materials 并调用框架生成�?""
    evts = mats_summary.get("events", [])
    figs = mats_summary.get("figures", [])
    all_items = [{"name": str(e), "type": "event"} for e in evts] + \
                [{"name": str(f), "type": "figure"} for f in figs]
    mock_mats = {"candidate_materials": all_items}
    mock_orch = {
        "cog": {
            "name": "user_custom_cog",
            "nodes": ["custom_input"],
            "edges": [],
            "intent": "epic",
            "tension_arc": "rising_climax",
        }
    }
    with st.spinner("正在生成章节框架（约 10 秒）…�?):
        try:
            progress_ph.progress(70, text="生成章节框架�?)
            unified = run_phase2(
                composer, style_phase,
                user_input,
                mock_orchestration=mock_orch,
                mock_materials=mock_mats,
            )
            st.session_state["unified"] = unified
            progress_ph.progress(100, text="章节框架已生�?�?)
            st.rerun()
        except Exception as e:
            st.error(f"框架生成失败：{e}")


def _reset_all_state():
    """重置所有会话状态，回到起点�?""
    for key in ["step", "user_input", "book_design", "selected_scheme_id",
                 "style_phase", "unified", "selected_style",
                 "chapter_contents", "generation_started",
                 "custom_materials", "suggested_materials",
                 "chapter1_approved", "_prev_topic",
                 "_next_part_to_generate", "_completed_parts"]:
        st.session_state[key] = None
    st.session_state["step"] = 0
    st.session_state["_next_part_to_generate"] = 2
    st.session_state["_completed_parts"] = []



# ════════════════════════════════════════════════════════════
# 页面四：生成�?�?+ 确认�?
# ════════════════════════════════════════════════════════════

def _build_chapter_prompt(
    user_input: dict,
    ch_outline: dict,
    ctx: dict,
    mats_src: dict,
    prev_text: str = "",
) -> str:
    """构建单章生成 prompt（统一模板�?""
    events_str = "�?.join(mats_src.get("events", ctx.get("materials", {}).get("events", []))[:8])
    figures_str = "�?.join(mats_src.get("figures", ctx.get("materials", {}).get("figures", []))[:8])
    style_label = ctx.get("style_label", "通俗故事�?)
    ch_num = ch_outline["chapter"]

    tension_map = {
        1: "本章为开篇，节奏宜缓，通过日常场景建立时代氛围和人物形象，末尾引入核心冲突或悬念�?,
        2: "本章为冲突升级章。正面描写核心事件和人物的抉择，要有具体场景和人物对话，情节逐步升温�?,
    }
    tension_directive = tension_map.get(ch_num) or (
        "本章为高潮与收束章。情感要有爆发力，结尾要有余韵，让读者回味主题�?
    )

    prev_section = (f"\n【前情提要】\n{prev_text}\n") if prev_text else ""

    return f"""你是一位历史通俗作品作家。请根据以下创作规范，写�?*第{ch_num}�?*的完整正文�?

【书名】《{ctx.get('theme', user_input['chapter_title'])}�?
【风格】{style_label}
{prev_section}【章节】第{ch_num}章「{ch_outline['title']}」—�?{ch_outline['subtitle']}
【张力目标】{ch_outline['tension']:.0%}（{ch_outline.get('tension_label', '发展�?)}�?
【预估字数】约 {ch_outline.get('estimated_chars', 800)} �?
【素材】事件：{events_str} | 人物：{figures_str}
【章节指引】{tension_directive}
【要求】约 {ch_outline.get('estimated_chars', 800)} 字，人物对话符合时代身份，有具体场景，直接输出正文，不要加标题前缀�?""


def page_chapter1():
    """步骤四：生成�?章，展示并等待用户确认，确认后进入步骤五"""
    user_input = st.session_state["user_input"]
    unified = st.session_state.get("unified")
    ctx = unified.enhanced_context if unified else {}
    chapters_outline = ctx.get("chapter_outline", [])

    if not chapters_outline:
        st.error("章节大纲为空，请返回步骤三重新确认框�?)
        if st.button("�?返回步骤�?):
            st.session_state["step"] = 2
            st.rerun()
        return

    ch1_outline = chapters_outline[0]
    results = st.session_state.get("chapter_contents", [])
    ch1_existing = next((r for r in results if r["chapter"] == 1), None)

    # 方案信息
    selected_scheme = _get_selected_scheme()

    st.markdown(f"""
    <div class="main-header">📖 生成�?�?· 请确认后再生成全�?/div>
    <div style="margin-bottom:1em; padding:0.8em; background:#fef9e7; border-radius:8px;
                border-left:4px solid #f39c12; font-size:0.9em;">
    📖 <b>{user_input['chapter_title']}</b>
    &nbsp;|&nbsp; 方案�?b>{selected_scheme.scheme_title if selected_scheme else '�?}</b>
    &nbsp;|&nbsp; 风格�?b>{ctx.get('style_label', '�?)}</b>
    &nbsp;|&nbsp; �?<b>{len(chapters_outline)}</b> �?
    </div>
    """, unsafe_allow_html=True)

    llm = get_llm()

    # ── 生成�?章（如尚未生成）────────────────────────
    if ch1_existing is None:
        progress_bar = st.progress(0, text="准备生成�?章�?)
        mats_src = st.session_state.get("custom_materials", {})

        progress_bar.progress(30, text=f"正在生成�?章「{ch1_outline['title']}」�?)
        prompt = _build_chapter_prompt(user_input, ch1_outline, ctx, mats_src)
        try:
            resp = llm.chat(prompt, temperature=0.75, max_tokens=2048)
            content = resp.content.strip() if hasattr(resp, "content") else str(resp)
        except Exception as e:
            content = f"[生成失败：{e}]"

        ch1_result = {
            "chapter": 1,
            "title": ch1_outline["title"],
            "subtitle": ch1_outline["subtitle"],
            "tension": ch1_outline["tension"],
            "tension_label": ch1_outline.get("tension_label", ""),
            "content": content,
            "char_count": len(content),
        }
        results = [ch1_result]
        st.session_state["chapter_contents"] = results
        progress_bar.progress(100, text="�?章生成完�?�?)
        progress_bar.empty()
        st.rerun()  # 重新渲染显示结果
    else:
        ch1_result = ch1_existing

    # ── 展示�?章内�?───────────────────────────────
    emoji_map = {"开篇引�?: "🌒", "矛盾积累": "🌓", "高潮时刻": "🌕",
                 "回落收束": "🌗", "结局": "🌑", "发展展开": "🌔",
                 "高峰与衰�?: "�?, "上升至高�?: "🔥"}
    emoji = emoji_map.get(ch1_result["tension_label"], "📖")

    st.markdown(f"""
    <div class="chapter-card" style="border-left:4px solid #f39c12; background:#fffbef;">
        <div style="display:flex; align-items:center; gap:0.5em; margin-bottom:0.4em;">
            <span style="font-size:1.2em;">{emoji}</span>
            <span style="font-weight:700; font-size:1.1em;">�?章「{ch1_result['title']}�?/span>
            <span style="background:#ebf5fb; color:#2980b9; padding:0.15em 0.6em;
                        border-radius:1em; font-size:0.8em; margin-left:auto;">
                {ch1_result['tension']:.0%} {ch1_result['tension_label']}
            </span>
        </div>
        <div style="color:#555; font-size:0.9em; margin-bottom:0.5em;">{ch1_result['subtitle']}</div>
        <div style="color:#888; font-size:0.82em;">�?{ch1_result['char_count']} �?/div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(ch1_result["content"])
    st.caption(f"字数：约 {ch1_result['char_count']} �?| 张力：{ch1_result['tension']:.0%}（{ch1_result['tension_label']}�?)

    # ── 确认�?──────────────────────────────────────
    st.markdown("---")

    # 判断是否有分部结�?
    all_chapters = chapters_outline  # list of dict from unified
    parts_in_schemes = set()
    if selected_scheme and selected_scheme.chapters:
        parts_in_schemes = {ch.part for ch in selected_scheme.chapters if ch.part is not None}
    has_parts = len(parts_in_schemes) > 1

    if has_parts:
        total_parts = len(parts_in_schemes)
        part1_chapters = [c for c in all_chapters
                          if (next((sc for sc in selected_scheme.chapters
                                    if sc.chapter == c["chapter"]), None) or type('S', (), {'part': None})()).part == 1]
        part1_count = len(part1_chapters)
        st.info(
            f"📖 本作品共 **{total_parts} �?*，第1部包含第1章�?
            f"确认后将先生成第2部（�?{len([c for c in all_chapters if (next((sc for sc in selected_scheme.chapters if sc.chapter == c['chapter']), type('S',(),{'part':None})()).part or 0) == 2])} 章）�?
            f"完成后需再次确认，后面的部数以此类推�?
        )
    else:
        st.info("👆 请阅读上方第1章，确认文风、节奏、人物塑造是否符合你的预期。确认后系统将生成全书（�?-N章）�?)

    col_confirm, col_regen, col_back = st.columns([3, 2, 1])
    with col_confirm:
        btn_label = "�?�?章OK，生成第2-N�?�? if not has_parts else "�?�?章OK，开始生成下一�?�?
        if st.button(btn_label, use_container_width=True, type="primary"):
            st.session_state["chapter1_approved"] = True
            # 初始化分部追�?
            st.session_state["_completed_parts"] = []
            st.session_state["_next_part_to_generate"] = 2
            st.session_state["step"] = 4
            st.rerun()
    with col_regen:
        if st.button("🔄 重新生成�?�?, use_container_width=True):
            results = [r for r in results if r["chapter"] != 1]
            st.session_state["chapter_contents"] = results
            st.rerun()
    with col_back:
        if st.button("�?修改框架"):
            st.session_state["step"] = 2
            st.rerun()


# ════════════════════════════════════════════════════════════
# 页面五：生成全书（第2-N章）并展示（支持分部确认�?
# ════════════════════════════════════════════════════════════

def _chapter_part_map(selected_scheme, chapters_outline):
    """返回 {chapter_num: part_num} 的映�?""
    part_map = {}
    if selected_scheme and selected_scheme.chapters:
        for ch in chapters_outline:
            sch_ch = next(
                (sc for sc in selected_scheme.chapters if sc.chapter == ch["chapter"]),
                None,
            )
            part_map[ch["chapter"]] = sch_ch.part if sch_ch else None
    return part_map


def _render_all_chapters(results, ctx, selected_scheme, user_input):
    """渲染所有已生成的章节（含分部标题）"""
    results_sorted = sorted(results, key=lambda x: x["chapter"])
    if not results_sorted:
        return 0

    # 渲染分部标题
    if selected_scheme and selected_scheme.chapters:
        part_map = {}
        for ch_num in [r["chapter"] for r in results_sorted]:
            sc = next((s for s in selected_scheme.chapters if s.chapter == ch_num), None)
            part_map[ch_num] = sc.part if sc else None

        # 检测分部切�?
        prev_part = None
        for r in results_sorted:
            p = part_map.get(r["chapter"])
            if p != prev_part and p is not None:
                pt = next((s.part_title for s in selected_scheme.chapters
                           if s.part == p and s.part_title), f"第{p}�?)
                st.markdown(f"### 📂 {pt}")
            prev_part = p
    else:
        st.markdown("## 📖 完整书稿")

    total_chars = sum(r["char_count"] for r in results_sorted)
    emoji_map = {"开篇引�?: "🌒", "矛盾积累": "🌓", "高潮时刻": "🌕",
                 "回落收束": "🌗", "结局": "🌑", "发展展开": "🌔",
                 "高峰与衰�?: "�?, "上升至高�?: "🔥"}

    for r in results_sorted:
        emoji = emoji_map.get(r["tension_label"], "📖")
        with st.expander(
            f"📖 第{r['chapter']}章「{r['title']}�?{emoji} {r['tension']:.0%} | �?{r['char_count']} �?,
            expanded=(r["chapter"] == 1),
        ):
            st.markdown(f"*{r['subtitle']}*")
            st.markdown("---")
            st.markdown(r["content"])
            st.caption(f"字数：约 {r['char_count']} �?| 张力：{r['tension']:.0%}（{r['tension_label']}�?)

    return total_chars


def _download_book(results, ctx, selected_scheme, user_input):
    """生成并提供书稿下�?""
    if not results:
        return
    results_sorted = sorted(results, key=lambda x: x["chapter"])
    total_chars = sum(r["char_count"] for r in results_sorted)

    book_md = f"# {ctx.get('theme', user_input['chapter_title'])}\n\n"
    book_md += f"**方案**：{selected_scheme.scheme_title if selected_scheme else ''}\n"
    book_md += f"**风格**：{ctx.get('style_label', '')} | **章节�?*：{len(results_sorted)}\n\n---\n\n"

    if selected_scheme and selected_scheme.chapters:
        part_map = {}
        for ch_num in [r["chapter"] for r in results_sorted]:
            sc = next((s for s in selected_scheme.chapters if s.chapter == ch_num), None)
            part_map[ch_num] = sc.part if sc else None
        prev_part = None
        for r in results_sorted:
            p = part_map.get(r["chapter"])
            if p != prev_part and p is not None:
                pt = next((s.part_title for s in selected_scheme.chapters
                           if s.part == p and s.part_title), f"第{p}�?)
                book_md += f"\n## 📂 {pt}\n\n"
            prev_part = p
            book_md += f"## 第{r['chapter']}章「{r['title']}」\n\n*{r['subtitle']}*\n\n{r['content']}\n\n---\n\n"
    else:
        for r in results_sorted:
            book_md += f"## 第{r['chapter']}章「{r['title']}」\n\n*{r['subtitle']}*\n\n{r['content']}\n\n---\n\n"

    book_md += f"\n*全稿�?{total_chars} �?| �?PT-047 社科智能体创作平台生�?\n"
    st.download_button(
        label="📥 下载完整书稿（Markdown�?,
        data=book_md,
        file_name=f"{user_input['chapter_title']}.md",
        mime="text/markdown",
        use_container_width=True,
    )


def page_full_book():
    """步骤五：分部确认式全书生�?""
    user_input = st.session_state["user_input"]
    unified = st.session_state.get("unified")
    ctx = unified.enhanced_context if unified else {}
    chapters_outline = ctx.get("chapter_outline", [])
    results = st.session_state.get("chapter_contents", [])
    llm = get_llm()
    mats_src = st.session_state.get("custom_materials", {})
    selected_scheme = _get_selected_scheme()

    # ── 分部结构分析 ────────────────────────────────
    part_map = _chapter_part_map(selected_scheme, chapters_outline)
    all_parts = sorted({p for p in part_map.values() if p is not None})
    has_parts = len(all_parts) > 1
    total_parts = len(all_parts) or 1
    next_part = st.session_state.get("_next_part_to_generate", 2)
    completed_parts = st.session_state.get("_completed_parts", [])
    current_part = all_parts[next_part - 1] if has_parts and next_part - 1 < len(all_parts) else None

    # ── 头部状�?────────────────────────────────────
    completed_ch_count = len(results)
    total_ch_count = len(chapters_outline)

    if has_parts:
        header_color = "#27ae60"
        header_bg = "#eafaf1"
        part_label = f"（{len(completed_parts)}/{total_parts} 部完成）"
        header_sub = (
            f"📖 <b>{user_input['chapter_title']}</b>"
            f"&nbsp;|&nbsp; 方案�?b>{selected_scheme.scheme_title if selected_scheme else '�?}</b>"
            f"&nbsp;|&nbsp; {len(completed_parts)}/{total_parts} 部完成{part_label}"
        )
    else:
        header_color = "#27ae60"
        header_bg = "#eafaf1"
        header_sub = (
            f"📖 <b>{user_input['chapter_title']}</b>"
            f"&nbsp;|&nbsp; 方案�?b>{selected_scheme.scheme_title if selected_scheme else '�?}</b>"
            f"&nbsp;|&nbsp; �?<b>{total_ch_count}</b> �?
        )

    st.markdown(f"""
    <div class="main-header">📚 全书生成中{part_label if has_parts else '�?}</div>
    <div style="margin-bottom:1em; padding:0.8em; background:{header_bg}; border-radius:8px;
                border-left:4px solid {header_color}; font-size:0.9em;">
    {header_sub}
    </div>
    """, unsafe_allow_html=True)

    # ── 分部确认门（如果当前需要等待确认）───────────
    if has_parts and next_part == "__waiting__":
        # 显示已完成部分，等待用户确认
        _render_all_chapters(results, ctx, selected_scheme, user_input)
        st.markdown("---")
        current_completed = completed_parts[-1] if completed_parts else 1
        st.warning(
            f"📖 第{current_completed}部已完成（{len(results)}/{total_ch_count} 章）"
            "——请确认以上内容是否符合预期，再继续生成下一部�?
        )
        col_conf, col_regen = st.columns([3, 1])
        with col_conf:
            next_p = (completed_parts[-1] + 1) if completed_parts else 2
            if st.button(
                f"�?第{current_completed}部OK，生成下一部（第{next_p}部）�?,
                use_container_width=True, type="primary",
            ):
                st.session_state["_next_part_to_generate"] = next_p
                st.rerun()
        with col_regen:
            # 重生成当前部的最后一�?
            if st.button("🔄 重新生成最后章"):
                if results:
                    last_ch = sorted(results, key=lambda x: x["chapter"])[-1]
                    results_clean = [r for r in results if r["chapter"] != last_ch["chapter"]]
                    st.session_state["chapter_contents"] = results_clean
                    st.session_state["_next_part_to_generate"] = "__waiting__"
                    st.rerun()
        return

    # ── 生成逻辑 ──────────────────────────────────
    def get_prev_text(results_so_far):
        if not results_so_far:
            return ""
        return "\n\n".join(r["content"][:400] + "…�? for r in sorted(results_so_far, key=lambda x: x["chapter"]))

    # 确定需要生成的章节
    if has_parts:
        # 生成分部：current_part
        chapters_to_generate = [
            c for c in chapters_outline[1:]
            if part_map.get(c["chapter"]) == current_part
        ]
        # 如果当前部的章节都已生成，弹出确认门
        already_done = all(
            any(r["chapter"] == c["chapter"] for r in results)
            for c in chapters_to_generate
        )
        total_in_this_part = len(chapters_to_generate)
        if already_done and current_part is not None:
            # 本部完成，弹出确认门
            _render_all_chapters(results, ctx, selected_scheme, user_input)
            st.markdown("---")
            st.warning(
                f"📖 **第{current_part}部已完成**（{total_in_this_part} 章）"
                f"——请确认后继续生成�?
            )
            # 记录完成
            if current_part not in completed_parts:
                completed_parts.append(current_part)
                st.session_state["_completed_parts"] = completed_parts

            is_last_part = current_part == all_parts[-1]
            col_conf, col_regen = st.columns([3, 1])
            with col_conf:
                if is_last_part:
                    # 全书完成
                    st.success("🎉 全书生成完毕�?)
                    total_chars = sum(r["char_count"] for r in results)
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    col_s1.metric("总章�?, f"{len(results)} �?)
                    col_s2.metric("总字�?, f"�?{total_chars} �?)
                    col_s3.metric("风格", ctx.get("style_label", "�?))
                    col_s4.metric("状�?, f"�?全书完成")
                    st.markdown("---")
                    _download_book(results, ctx, selected_scheme, user_input)
                    st.markdown("---")
                    if st.button("🔄 重新开始创�?, use_container_width=True):
                        _reset_all_state()
                        st.rerun()
                else:
                    next_p = current_part + 1
                    if st.button(
                        f"�?第{current_part}部OK，生成第{next_p}�?�?,
                        use_container_width=True, type="primary",
                    ):
                        st.session_state["_next_part_to_generate"] = next_p
                        st.rerun()
            with col_regen:
                if st.button("🔄 重写最后章"):
                    last_ch_num = chapters_to_generate[-1]["chapter"] if chapters_to_generate else None
                    if last_ch_num:
                        results_clean = [r for r in results if r["chapter"] != last_ch_num]
                        st.session_state["chapter_contents"] = results_clean
                        st.rerun()
            return
    else:
        # 无分部：生成�?章起所有章�?
        chapters_to_generate = chapters_outline[1:]

    # ── 生成进度�?────────────────────────────────
    progress_bar = st.progress(0, text="准备生成�?)

    for i, ch_outline in enumerate(chapters_to_generate):
        ch_num = ch_outline["chapter"]
        already = next((r for r in results if r["chapter"] == ch_num), None)
        if already:
            progress_bar.progress((i + 1) / len(chapters_to_generate),
                                  text=f"第{ch_num}章已完成 �?)
            continue

        emoji_map = {"开篇引�?: "🌒", "矛盾积累": "🌓", "高潮时刻": "🌕",
                     "回落收束": "🌗", "结局": "🌑", "发展展开": "🌔",
                     "高峰与衰�?: "�?, "上升至高�?: "🔥"}
        emoji = emoji_map.get(ch_outline.get("tension_label", ""), "📖")

        if has_parts:
            label = f"正在生成第{current_part}部第{ch_num}章「{ch_outline['title']}」{emoji}�?
        else:
            label = f"正在生成第{ch_num}章「{ch_outline['title']}」{emoji}�?

        progress_bar.progress((i + 0.5) / len(chapters_to_generate), text=label + "（约 15�?5 秒）")

        prev_text = get_prev_text(results)
        prompt = _build_chapter_prompt(user_input, ch_outline, ctx, mats_src, prev_text)

        try:
            resp = llm.chat(prompt, temperature=0.75, max_tokens=2048)
            content = resp.content.strip() if hasattr(resp, "content") else str(resp)
        except Exception as e:
            content = f"[生成失败：{e}]"

        result_entry = {
            "chapter": ch_num,
            "title": ch_outline["title"],
            "subtitle": ch_outline["subtitle"],
            "tension": ch_outline["tension"],
            "tension_label": ch_outline.get("tension_label", ""),
            "content": content,
            "char_count": len(content),
        }
        results.append(result_entry)
        st.session_state["chapter_contents"] = results
        progress_bar.progress((i + 1) / len(chapters_to_generate),
                              text=f"第{ch_num}章生成完�?�?)

    progress_bar.empty()

    # ── 生成完毕 ──────────────────────────────────
    # 有分部：本部完成后弹出确认门；无分部：全书完�?
    if has_parts:
        # 触发确认门（设置标记�?
        st.session_state["_next_part_to_generate"] = "__waiting__"
        st.rerun()
    else:
        total_chars = sum(r["char_count"] for r in results)
        _render_all_chapters(results, ctx, selected_scheme, user_input)
        st.markdown("---")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("总章�?, f"{len(results)} �?)
        col_s2.metric("总字�?, f"�?{total_chars} �?)
        col_s3.metric("风格", ctx.get("style_label", "�?))
        col_s4.metric("状�?, "�?全书生成完毕")
        st.markdown("---")
        _download_book(results, ctx, selected_scheme, user_input)
        st.markdown("---")
        if st.button("🔄 重新开始创�?, use_container_width=True):
            _reset_all_state()
            st.rerun()



# ════════════════════════════════════════════════════════════
# 主路�?
# ════════════════════════════════════════════════════════════
def main():
    step = st.session_state.get("step", 0)
    step_badge(step)

    if step == 0:
        page_input()
    elif step == 1:
        page_scheme_selection()
    elif step == 2:
        page_preview()
    elif step == 3:
        page_chapter1()
    elif step == 4:
        page_full_book()


if __name__ == "__main__":
    main()
