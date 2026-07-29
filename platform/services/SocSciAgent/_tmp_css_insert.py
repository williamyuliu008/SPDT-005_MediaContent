# This file contains the new CSS — used as a reference for the edit
# The actual edit will replace the _INK_GOLD_CSS block in gui_app.py

NEW_CSS = r"""
# ── 墨韵典雅主题注入（S6 复古典雅风 · Streamlit DOM）────────
# 设计参考：D:/9_infra/UIUX_design/reference/UIUX_Design_package_202604/
#   - S6_classic_elegant.js  复古典雅风色彩系统
#   - L1_immersive_reading.jsx  沉浸阅读布局
#
# 配色方案：墨韵典雅
#   主色：墨褐 #523427 / 赭石 #967c46 / 烫金 #c49a47
#   背景：羊皮纸 #f8f4eb / 宣纸 #faf8f5
#   辅色：青墨 #5a7a8a / 翠玉 #5d8a4a / 绛紫 #6a4a9a

_INK_GOLD_CSS = r"""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;600&display=swap');

/* ── 全局背景 & 字体 ── */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: #f8f4eb !important;
    font-family: 'Noto Sans SC', 'PingFang SC', sans-serif !important;
}

/* Streamlit 主容器 */
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

/* ── 主标题区（page_input 顶部） ── */
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

/* ── 步骤进度条（横向） ── */
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

/* ── 表单字段区（两列布局） ── */
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

/* ── 输入框 / textarea ── */
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

/* ── 信息框（Alert） ── */
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

/* ── 方案卡片（scheme-card-box） ── */
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

/* ── 章节卡片（chapter-card） ── */
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

/* ── 张力条 ── */
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

/* ── 素材标签（material-tag） ── */
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

/* ── 加载动画（墨滴·典雅版） ── */
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

/* ── Logo 标题区 ── */
.ink-logo { text-align: center; padding: 20px 0 6px; }
.ink-logo-main {
    font-family: 'Noto Serif SC', serif !important;
    font-size: 20px;
    font-weight: 700;
    color: #523427;
    letter-spacing: 0.18em;
}
.ink-logo-main::before { content: '【'; color: #967c46; }
.ink-logo-main::after  { content: '】'; color: #967c46; }
.ink-logo-sub {
    font-size: 11.5px;
    color: #9a8a78;
    letter-spacing: 0.22em;
    margin-top: 4px;
}

/* ── 风格样章卡片（style-preview-card） ── */
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

/* ── 创作意图预览卡（intent-summary-card） ── */
.intent-summary-card {
    background: linear-gradient(135deg, #fdfcf9, #f8f4ed);
    border: 1px solid #d4c4a8;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(82,58,39,0.05);
}

/* ── 副标题小字 ── */
.caption-text {
    font-size: 12px;
    color: #9a8a78;
    font-style: italic;
    margin-bottom: 8px;
}

/* ── 小节标题（h3 级别） ── */
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

/* ── 选中态遮罩 ── */
.selected-overlay {
    position: relative;
}
.selected-overlay::before {
    content: '✓ 已选';
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
