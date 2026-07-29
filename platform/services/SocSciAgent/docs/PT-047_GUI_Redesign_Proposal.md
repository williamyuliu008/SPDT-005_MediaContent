# PT-047 社科智能体创作平台 · GUI 重构设计规划书

> 基于 UIUX SOP v2.0 DAGO 方法论  
> 版本：v1.0 | 日期：2026-07-15  
> 风格：S6 古典高端风（深色金韵）| 技术栈：Gradio | 范围：全量重构

---

## 一、DAGO 六维决策分析

### 1.1 PT-047 六维 dims 推导

| 维度 | 值 | 推导依据 |
|------|-----|---------|
| **D1 功能语义** | `creative-workspace` | 内容创作工具，非管理/数据类，属于创作类工具 |
| **D2 用户角色** | `creative-student` | 备考学生/创作者，专业度中等，需要引导而非纯效率 |
| **D3 信息密度** | `medium` | 5步向导流程，但每步含大量 LLM 生成内容，属于中高密度 |
| **D4 风险等级** | `low` | 内容生成类应用，无高风险操作，容错空间大 |
| **D5 异常路径** | `generation-failure` / `empty-content` / `api-timeout` / `chapter-loss` | LLM 生成特有的异常（空内容/API超时/章节丢失） |
| **D6 使用场景** | `immersive_reading` / `creative_flow` | 创作场景需要沉浸感，长时间注视屏幕 |
| **D7 UX 模式** | `wizard-stepped` | 5步向导流程，线性有序 |
| **D8 视图模式** | `single-page-wizard` | 单页内切换内容区（向导模式） |

### 1.2 DAGO → A层推导链

```
D1 (creative-workspace) → L1（沉浸式阅读布局）
D5 (空内容/API超时) → warning/info 提示态
D6 (immersive_reading) → S6 深色主题（降低长时间注视疲劳）
D2 (creative-student) → 引导性装饰，S6 风格（典雅不刺眼）
D3 (medium) → 间距 16px 网格，信息不过于紧凑
```

### 1.3 最终 DAGO 输出

| 推导项 | 值 | 说明 |
|-------|-----|------|
| **布局模板** | L1（沉浸式阅读） | 大留白，居中内容区，适合创作阅读 |
| **风格模板** | S6 古典高端（Luxury） | 深色背景 + 金韵点缀 + 衬线字体 |
| **组件集合** | card / step_wizard / markdown_rich / spinner_elegant / accordion | 创作工具组件族 |
| **异常态** | generation-failure / empty-content / api-timeout | 优雅降级提示，非阻断式 |
| **视图模式** | single-page-wizard | 向导步骤切换，内容区替换 |

---

## 二、S6 古典高端风 · PT-047 定制调色板

### 2.1 视觉调性

**定位**：精品内容平台风格，如"得到App"、"微信读书"Pro 版
**关键词**：墨韵金声、文人书卷、沉稳典雅
**不适合**：纯深黑（过于技术感）→ 用深墨色代替

### 2.2 完整色彩系统

```css
:root {
  /* ── 背景层 ── */
  --bg-primary:      #0f0f14;   /* 墨黑：页面背景 */
  --bg-secondary:    #16161f;   /* 墨灰：卡片/面板背景 */
  --bg-elevated:     #1e1e2a;   /* 浮层：hover/选中态 */
  --bg-overlay:      #252535;   /* 蒙版层：模态框背景 */

  /* ── 文字层 ── */
  --text-primary:    #e8e4dc;   /* 象牙白：主文字 */
  --text-secondary:  #9e9a94;   /* 灰褐：次要文字 */
  --text-muted:      #5a5850;   /* 暗灰：辅助/占位文字 */
  --text-inverse:    #0f0f14;   /* 反色：深色文字（浅色背景上）*/

  /* ── 金韵主色系 ── */
  --gold-bright:     #f0d060;   /* 明金：高亮/徽章/强调 */
  --gold-primary:    #c9a84c;   /* 主金：品牌色/标题下划线 */
  --gold-muted:      #8a7235;   /* 暗金：次要金色/图标 */
  --gold-glow:       rgba(201, 168, 76, 0.15);  /* 金光晕：焦点态 */

  /* ── 辅色 ── */
  --plum:            #7c5cbf;   /* 墨紫：AI 介入/生成态 */
  --plum-muted:      #4a3875;   /* 暗紫：次要紫色 */
  --jade:            #3a9a7a;   /* 翠玉：成功态/确认 */
  --amber:           #c4833a;   /* 琥珀：警告态 */
  --ruby:            #b54a4a;   /* 朱红：错误态 */

  /* ── 边框/分割 ── */
  --border-subtle:   rgba(201, 168, 76, 0.12);  /* 微金线：分割线 */
  --border-default:  rgba(201, 168, 76, 0.25);   /* 默认边框 */
  --border-strong:   rgba(201, 168, 76, 0.5);    /* 强边框：聚焦态 */

  /* ── 字体 ── */
  --font-display:    'Noto Serif SC', 'Songti SC', 'SimSun', serif;  /* 标题/品牌 */
  --font-body:       'Noto Sans SC', 'PingFang SC', sans-serif;       /* 正文 */
  --font-mono:       'JetBrains Mono', 'Fira Code', monospace;        /* 代码/数字 */

  /* ── 间距 ── */
  --space-xs:  4px;
  --space-sm:  8px;
  --space-md:  16px;
  --space-lg:  24px;
  --space-xl:  40px;
  --space-2xl: 64px;

  /* ── 圆角 ── */
  --radius-sm:  4px;   /* 输入框/小按钮 */
  --radius-md:  8px;   /* 卡片/面板 */
  --radius-lg:  12px;  /* 大容器/模态 */
  --radius-xl:  20px;  /* 特殊强调块 */

  /* ── 阴影 ── */
  --shadow-gold: 0 0 20px rgba(201, 168, 76, 0.12);   /* 金晕阴影 */
  --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.4);       /* 卡片阴影 */
  --shadow-elevated: 0 8px 40px rgba(0, 0, 0, 0.6);   /* 浮层阴影 */

  /* ── 动画 ── */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);           /* 标准缓出 */
  --ease-gold: cubic-bezier(0.34, 1.56, 0.64, 1);      /* 金色弹性 */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 600ms;
}
```

### 2.3 字体系统

```
标题（H1-H3）：Noto Serif SC 700，墨韵衬线体
正文：Noto Sans SC 400，阅读舒适
辅助/标签：Noto Sans SC 300，轻盈
代码/数字：JetBrains Mono 400
```

---

## 三、5步向导页面布局设计

### 3.1 整体框架（L1 沉浸式）

```
┌─────────────────────────────────────────────────────┐
│  [墨韵Logo]  PT-047 社科智能体创作平台     [步骤指示] │  ← 固定顶栏
├───────────┬─────────────────────────────────────────┤
│           │                                         │
│  步骤导航  │           主内容区（内容随步骤切换）     │  ← 居中，最大宽度 860px
│  (左侧)   │                                         │
│           │  · 步骤1：创作意图输入                  │
│  ● 意图   │  · 步骤2：方案选择卡片                  │
│  ● 方案   │  · 步骤3：取材确认                      │
│  ● 取材   │  · 步骤4：第1章生成                    │
│  ● 首章   │  · 步骤5：全书生成                      │
│  ● 全书   │                                         │
│           │                                         │
├───────────┴─────────────────────────────────────────┤
│  [底部版权/帮助链接]                               │
└─────────────────────────────────────────────────────┘
```

### 3.2 各步骤详细设计

#### 步骤1：创作意图输入
```
┌──────────────────────────────────────┐
│  书卷标题区（居中，金色下划线装饰）     │
│  ════════════════════════════════    │
│                                      │
│  📖 作品主题                         │
│  ┌────────────────────────────────┐  │
│  │  苏东坡创作《黄州寒食帖》的故事   │  │  ← 大输入框，衬线字体
│  └────────────────────────────────┘  │
│                                      │
│  📝 创作描述                         │
│  ┌────────────────────────────────┐  │
│  │  苏轼被贬黄州第三年的寒食节...    │  │  ← 多行文本，金色聚焦边框
│  └────────────────────────────────┘  │
│                                      │
│  👤 核心人物（斜杠分隔）             │
│  ┌────────────────────────────────┐  │
│  │  苏轼 / 王巩 / 朝云              │  │
│  └────────────────────────────────┘  │
│                                      │
│  📏 目标字数：[━━━━━━━●━━━] 15000  │  ← 滑块，金色轨道
│                                      │
│        [ 🚀 开启创作旅程 → ]         │  ← 主按钮，金色渐变
└──────────────────────────────────────┘
```

#### 步骤2：方案选择（卡片画廊）
```
┌──────────────────────────────────────┐
│  三套方案 · 请选择其一                  │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ 方案A  【线性叙事】            │ ← 墨紫边框，金角标
│  │ ════════════════════════════│   │
│  │ 主线：苏轼如何在绝境中完成精神  │   │
│  │ 涅槃……                      │   │
│  │ 张力曲线：▁▃▅▇▅▃▁           │   │
│  │ 结构：线性时间流 | 视角：内心   │   │
│  │ 章节：7章                     │   │
│  │  [▶ 选择此方案]               │ ← 金色描边按钮
│  └──────────────────────────────┘   │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ 方案B  【双线并行】   ←未选中   │   │
│  │ ……                            │   │
│  └──────────────────────────────┘   │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ 方案C  【主题式递进】 ←未选中  │   │
│  │ ……                            │   │
│  └──────────────────────────────┘   │
└──────────────────────────────────────┘
```

#### 步骤3：取材确认
```
┌──────────────────────────────────────┐
│  AI 推荐取材 · 请确认使用             │
│  ════════════════════════════════    │
│                                      │
│  ⭐ 核心骨架（不可取消）              │
│  ┌────────────────────────────────┐  │
│  │ ★ 乌台诗案                     │  │  ← 金色星标，必选
│  │   苏轼因诗被陷，仕途断绝的转折点 │
│  │ ★ 黄州垦荒                     │  │
│  │   从庙堂到东坡，精神转折的起点   │
│  └────────────────────────────────┘  │
│                                      │
│  ○ 丰富层次（可取消）                │
│  ┌────────────────────────────────┐  │
│  │ ○ 王巩的乌台诗案平反             │  │  ← 复选框
│  │   苏轼友人，陪伴黄州岁月         │
│  │ ○ 苏辙的手足之情               │  │
│  └────────────────────────────────┘  │
│                                      │
│  ✏️ 手动补充                         │
│  [  事件名称...  ] [+添加]          │
│  [  人物名称...  ] [+添加]          │
│                                      │
│  [ ✨ 生成章节框架预览 → ]           │  ← 紫色渐变（AI 动作）
└──────────────────────────────────────┘
```

#### 步骤4：第1章预览
```
┌──────────────────────────────────────┐
│  第1章「夜雨惊魂」预览               │
│  ════════════════════════════════    │
│                                      │
│  📊 章节信息                         │
│  张力目标：10% 开篇引入               │
│  预估字数：~2142 字                 │
│  核心素材：乌台诗案、苏轼             │
│                                      │
│  ┌────────────────────────────────┐  │
│  │  正文内容渲染区……               │  │  ← Markdown 渲染，金色引用线
│  │  > "自笑平生为口忙，老来事业    │  │
│  │    转荒唐……"                   │  │
│  │                                │  │
│  │  [金色分隔线]                   │  │
│  └────────────────────────────────┘  │
│                                      │
│  [ 🔄 重新生成 ]  [ ✅ 确认并继续 ] │  ← 重新生成（金边框）/ 确认（渐变）
└──────────────────────────────────────┘
```

#### 步骤5：全书生成（分部确认）
```
┌──────────────────────────────────────┐
│  📚 全书生成中（1/2 部完成）          │
│  ════════════════════════════════    │
│                                      │
│  第1部 · 落魄时期（已完成 ✅）        │
│  ├── 第1章：夜雨惊魂      2150字 ✅  │
│  ├── 第2章：荒城孤影      2010字 ✅  │
│  └── 第3章：雨中耕读      1980字 ✅  │
│                                      │
│  第2部 · 寒食帖诞生（生成中 🔄）     │
│  ├── 第4章：寒食将至      2200字 🔄  │  ← 进度指示
│  └── 第5章：...              ⏳      │
│                                      │
│  ┌────────────────────────────────┐  │
│  │  生成中…… 请稍候               │  │  ← 优雅加载动画（墨滴扩散）
│  └────────────────────────────────┘  │
│                                      │
│  [ ⏸ 暂停生成 ]  [ 📥 下载已完成部分 ]│
└──────────────────────────────────────┘
```

---

## 四、Gradio 实现方案

### 4.1 技术选型理由

| 特性 | Streamlit（当前） | Gradio（目标） |
|------|------------------|----------------|
| 主题定制能力 | 有限（st.markdown CSS 注入） | **原生 dark 主题 + CSS 变量** |
| 步骤流程控制 | session_state if/elif | **gr.State() + 自定义 wizard 组件** |
| 组件美观度 | 默认样式较朴素 | **更好看的卡片、按钮、加载动画** |
| Markdown 渲染 | st.markdown | **gr.Markdown（更好看的标题层级）** |
| 部署 | `--server.port` | **--share 或 HuggingFace Spaces** |
| LLM 集成 | 直接调用 | **gr.ChatInterface / gr.Avatar** |

### 4.2 Gradio 核心实现策略

```python
import gradio as gr
from gradio.themes.base import Base

# ── 1. 自定义 S6 墨韵主题 ──────────────────────────
class InkGoldTheme(Base):
    def __init__(self):
        super().__init__(
            primary_hue=gr.themes.colors.Color(
                name="ink_gold",
                c50="#1a1a28",
                c100="#252538",
                c200="#303048",
                c300="#c9a84c",   # 金主色
                c400="#f0d060",   # 明金
                c500="#e8c44a",
                c600="#c9a84c",
                c700="#8a7235",
                c800="#4a3d20",
                c900="#2a2418",
                c950="#161420",
            ),
            secondary_hue=...,
            neutral_hue=gr.themes.colors.Color(...),  # 墨灰色系
            font=("Noto Serif SC", "Noto Sans SC", "system-ui"),
        )

# ── 2. Wizard 状态管理 ──────────────────────────────
wizard_state = gr.State({
    "step": 0,
    "user_input": None,
    "book_design": None,
    "selected_scheme_id": None,
    "custom_materials": None,
    "unified": None,
    "chapter_contents": [],
    "chapter1_approved": False,
})

# ── 3. 步骤切换逻辑 ─────────────────────────────────
def on_step_complete(next_step, state):
    state["step"] = next_step
    return gr.update(visible=True), state

# ── 4. 各步骤生成函数 ──────────────────────────────
def step1_render(state):
    """步骤1：创作意图输入"""
    with gr.Group():
        topic = gr.Textbox(label="📖 作品主题", lines=1, ...)
        desc = gr.Textbox(label="📝 创作描述", lines=4, ...)
        chars = gr.Textbox(label="👤 核心人物（斜杠分隔）", ...)
        words = gr.Slider(minimum=1000, maximum=80000, value=15000, step=500, ...)
        submit = gr.Button("🚀 开启创作旅程", variant="primary")

    submit.click(
        fn=lambda topic, desc, chars, words: {"step": 1, "user_input": {...}},
        inputs=[topic, desc, chars, words],
        outputs=[wizard_state, step_container],
    )

def step2_render(state):
    """步骤2：方案选择"""
    ...

def step3_render(state):
    """步骤3：取材确认 + 框架预览"""
    ...

def step4_render(state):
    """步骤4：第1章预览"""
    ...

def step5_render(state):
    """步骤5：全书生成"""
    ...

# ── 5. 主应用 ─────────────────────────────────────
with gr.Blocks(theme=InkGoldTheme(), title="PT-047 社科智能体创作平台") as demo:
    gr.Markdown("# ✍️ PT-047 社科智能体创作平台")
    gr.Markdown("*水墨金韵 · 文人书卷 · 智能创作*")

    with gr.Tabs():
        with gr.Tab("📖 创作向导"):
            with gr.Column(scale=1):
                step_indicator()    # 步骤指示器
            with gr.Column(scale=3):
                step_container()   # 动态切换步骤内容

        with gr.Tab("📚 书稿库"):
            # 历史书稿管理（未来扩展）
            pass

    demo.launch(server_port=7860, share=True)
```

### 4.3 自定义 CSS（墨韵金韵）

```css
/* PT-047 墨韵金韵 · Gradio 覆盖样式 */

/* 全局背景 */
body, .gradio-container {
    background: #0f0f14 !important;
    font-family: 'Noto Sans SC', sans-serif;
}

/* 标题字体 */
h1, h2, h3, .display-title {
    font-family: 'Noto Serif SC', serif !important;
    color: #e8e4dc;
    letter-spacing: 0.05em;
}

/* 金色下划线标题 */
.title-gold {
    position: relative;
    display: inline-block;
    padding-bottom: 8px;
}
.title-gold::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 80px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #c9a84c, transparent);
}

/* 卡片 */
.gr-card, .output-card, .scheme-card {
    background: #16161f !important;
    border: 1px solid rgba(201, 168, 76, 0.2) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4), 0 0 20px rgba(201, 168, 76, 0.06) !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.gr-card:hover, .scheme-card:hover {
    border-color: rgba(201, 168, 76, 0.4) !important;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(201, 168, 76, 0.12) !important;
    transform: translateY(-2px);
}

/* 选中卡片 */
.scheme-card.selected {
    border-color: #c9a84c !important;
    background: linear-gradient(135deg, #1e1e2a, #1a1a24) !important;
}

/* 主按钮（渐变金） */
.primary-btn, .gr-button.primary {
    background: linear-gradient(135deg, #c9a84c 0%, #f0d060 50%, #c9a84c 100%) !important;
    color: #0f0f14 !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 16px rgba(201, 168, 76, 0.3) !important;
    transition: all 0.3s var(--ease-gold) !important;
}
.primary-btn:hover {
    box-shadow: 0 6px 24px rgba(201, 168, 76, 0.5) !important;
    transform: translateY(-1px);
}

/* 次要按钮（金边框） */
.secondary-btn, .gr-button.secondary {
    background: transparent !important;
    color: #c9a84c !important;
    border: 1px solid #c9a84c !important;
    border-radius: 8px !important;
}

/* AI 动作按钮（墨紫渐变） */
.ai-btn, .gr-button.ai-action {
    background: linear-gradient(135deg, #4a3875 0%, #7c5cbf 50%, #4a3875 100%) !important;
    color: #e8e4dc !important;
    border: none !important;
    border-radius: 8px !important;
}

/* 输入框 */
.gr-textbox, .gr-textarea, input, textarea {
    background: #1a1a24 !important;
    border: 1px solid rgba(201, 168, 76, 0.2) !important;
    border-radius: 6px !important;
    color: #e8e4dc !important;
    font-family: 'Noto Sans SC', sans-serif !important;
    transition: border-color 0.2s ease !important;
}
.gr-textbox:focus, input:focus, textarea:focus {
    border-color: #c9a84c !important;
    box-shadow: 0 0 0 3px rgba(201, 168, 76, 0.1) !important;
    outline: none !important;
}

/* 滑块 */
input[type="range"] {
    accent-color: #c9a84c !important;
}

/* 分割线 */
hr, .divider {
    border: none;
    border-top: 1px solid rgba(201, 168, 76, 0.12);
}

/* Markdown 渲染区 */
.prose, .gr-markdown {
    color: #e8e4dc !important;
    line-height: 1.8 !important;
}
.prose h1, .prose h2, .prose h3 {
    font-family: 'Noto Serif SC', serif !important;
    color: #e8e4dc;
    border-bottom: 1px solid rgba(201, 168, 76, 0.2);
    padding-bottom: 4px;
}
.prose blockquote {
    border-left: 3px solid #c9a84c;
    background: rgba(201, 168, 76, 0.05);
    padding: 8px 16px;
    border-radius: 0 4px 4px 0;
    color: #9e9a94;
}

/* 加载动画（墨滴扩散） */
.loading-ink {
    position: relative;
    width: 60px;
    height: 60px;
    margin: 40px auto;
}
.loading-ink::before,
.loading-ink::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: #c9a84c;
    animation: ink-expand 1.5s ease-out infinite;
}
.loading-ink::after {
    animation-delay: 0.75s;
}
@keyframes ink-expand {
    0% { width: 10px; height: 10px; opacity: 0.8; }
    100% { width: 60px; height: 60px; opacity: 0; }
}

/* 步骤指示器 */
.step-indicator {
    display: flex;
    justify-content: center;
    gap: 24px;
    padding: 16px 0;
}
.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    opacity: 0.4;
    transition: all 0.3s ease;
}
.step-item.active {
    opacity: 1;
}
.step-item.completed {
    opacity: 0.7;
}
.step-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #3a3a48;
    border: 2px solid #3a3a48;
    transition: all 0.3s ease;
}
.step-item.active .step-dot {
    background: #c9a84c;
    border-color: #c9a84c;
    box-shadow: 0 0 10px rgba(201, 168, 76, 0.5);
}
.step-item.completed .step-dot {
    background: #3a9a7a;
    border-color: #3a9a7a;
}

/* 章节卡片 */
.chapter-card {
    background: #16161f;
    border: 1px solid rgba(201, 168, 76, 0.15);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
}
.chapter-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(to bottom, #c9a84c, #8a7235);
}

/* 张力曲线条 */
.tension-bar {
    height: 4px;
    background: linear-gradient(90deg, #c9a84c, #f0d060);
    border-radius: 2px;
    margin: 8px 0;
    transition: width 0.5s var(--ease-out);
}

/* 标签徽章 */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}
.badge-gold {
    background: rgba(201, 168, 76, 0.15);
    color: #c9a84c;
    border: 1px solid rgba(201, 168, 76, 0.3);
}
.badge-plum {
    background: rgba(124, 92, 191, 0.15);
    color: #7c5cbf;
    border: 1px solid rgba(124, 92, 191, 0.3);
}
.badge-jade {
    background: rgba(58, 154, 122, 0.15);
    color: #3a9a7a;
    border: 1px solid rgba(58, 154, 122, 0.3);
}
```

---

## 五、实施计划

### 5.1 文件结构

```
PT-047_SocSciAgent/
├── gui_app.py              # Streamlit 原版（保留）
├── gui_gradio.py           # Gradio 新版（新建）
├── theme_ink_gold.py       # 墨韵金韵主题定义
├── styles/
│   └── ink_gold.css       # 自定义 CSS（墨韵风格）
└── docs/
    └── PT-047_GUI_Redesign_Proposal.md   # 本文档
```

### 5.2 实施阶段

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| **Phase A** | dims.json 构建 + 墨韵主题定义 | 高 |
| **Phase B** | Gradio 基础框架 + 5步向导 + 墨韵CSS | 高 |
| **Phase C** | 与现有 LLM 生成逻辑对接（复用 shared/tools/） | 高 |
| **Phase D** | LLM 生成结果渲染（Markdown美化 + 章节卡片） | 中 |
| **Phase E** | 加载动画 + 优雅降级态 + 响应式优化 | 中 |

### 5.3 Gradio vs Streamlit 功能映射

| Streamlit 原功能 | Gradio 等价实现 |
|-----------------|----------------|
| `st.session_state` | `gr.State()` |
| `st.form` + `st.form_submit_button` | `gr.Button().click()` |
| `st.spinner` | 自定义 `loading-ink` HTML + JS 动画 |
| `st.markdown(..., unsafe_allow_html=True)` | `gr.HTML()` |
| `st.download_button` | `gr.DownloadButton` |
| `st.progress` | `gr.Progress()` 或自定义进度条 |
| `st.rerun()` | `gr.update()` 触发输出刷新 |
| `st.empty()` 动态替换 | 多 `with gr.Group():` + `gr.update(visible=...)` |
| `st.columns([2,1])` | `gr.Row()` + `gr.Column()` |
| `st.tabs` | `gr.Tabs()` + `gr.Tab()` |
| CSS 自定义字体 | Gradio `theme` 参数 + `extra_css` |
| `st.text_input` / `st.text_area` | `gr.Textbox()` |

---

## 六、与 SOP v2.0 的完整对齐

### 6.1 DAGO 推导验证

| 检查项 | 期望 | PT-047 实际 |
|--------|------|------------|
| D1 → Layout | L1 | creative-workspace → L1 ✅ |
| D2 → Style | S6 | creative-student → S6 ✅ |
| D6 → Style | S6 | immersive_reading → S6 ✅ |
| D5 → Error | generation-failure 等 | 4种 LLM 异常 ✅ |
| G层组件 | card/wizard/markdown | 3种组件 ✅ |
| A层推导链 | D1→L, D2→S, D5→E | 3条推导链 ✅ |

### 6.2 与 SOP 经典项目的差异化

| 项目 | D1 | D2 | 风格 | 布局 |
|------|----|----|------|------|
| kaodian | 知识库管理 | admin | S1 企业蓝 | L3 数据看板 |
| patent | 专利检索 | professional | S1 企业蓝 | L2 高效分屏 |
| samrt_edu | 学习系统 | student | S2 温暖橙 | L1 沉浸阅读 |
| **PT-047** | **创意写作** | **creative-student** | **S6 墨韵金** | **L1 沉浸向导** |

PT-047 是 SOP 案例库中**第一个「创意写作工具」场景**，具有独特性：
- D1=creative-workspace（新类型，非 CRUD 非管理非学习）
- S6 墨韵风格（在 SOP 案例库中首次使用）
- wizard-stepped UX 模式（在 SOP 中以 tab 模式覆盖）

---

## 七、预期效果

### 视觉层面
- 墨黑背景 + 金色点缀，完全区别于默认 Streamlit 灰白风格
- 衬线标题字体，呈现文人书卷气质
- 金色加载动画、卡片悬停光效，提升沉浸感

### UX 层面
- 5步向导更清晰，每步聚焦单一任务
- 步骤指示器让用户始终知道进度
- AI 动作（生成/推荐）用墨紫色区分操作类型

### 技术层面
- Gradio 启动更快，主题定制更灵活
- 可发布到 HuggingFace Spaces 分享
- 代码量减少（去掉 st.markdown HTML 注入的复杂度）

---

*本文档基于 UIUX SOP v2.0 DAGO 四层推导方法论生成*
*设计工具：AI编译 | 验证状态：理论推导完成，待实现验证*
