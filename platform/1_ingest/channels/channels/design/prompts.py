"""
SR-CH-004: AI 设计前线周报 — Prompt 配置
C 创意赛道 + D 技术文档赛道 + E 科普赛道
"""

# ─── C 赛道：创意（设计趋势文案）──────────────────

C_CREATIVE_SYSTEM = """你是 AI 产品设计评论员，专精于从产品迭代中识别设计趋势并用富有感染力的文案表达。
写作风格：有观点、有审美判断、避免空洞形容词、每个趋势用具体产品作为案例。"""

# 本周设计趋势
PROMPT_DESIGN_TRENDS = """【C 创意赛道】本周设计趋势

输入：{design_signals_json} + {app_scan_data_json}

识别本周 AI 产品设计的前沿趋势：
1. 用具体产品案例说明趋势（不要只说"极简"——说"Cursor 的暗色编码面板将注意力完全聚焦在代码上"）
2. 指出这些趋势背后的驱动力（技术进步？用户习惯变化？）
3. 给出审美判断——哪些趋势是短命的，哪些可能成为新常态

格式：
### {序号}. {趋势名称}
**案例：** {产品名} — {具体设计决策描述}
**判断：** {审美/趋势判断}
"""

# 鸿蒙启示（融合到趋势分析中）
PROMPT_HARMONY_INSIGHT = """【C 创意赛道】跨平台灵感 → 鸿蒙启示

输入：{android_top3_json} + {ios_top3_json}

从 Android/iOS AI 应用的设计亮点中提炼可迁移至鸿蒙的设计灵感：
1. 不做简单罗列——做「跨平台抽象」
2. 每个启示含：竞品案例 → 设计模式提取 → 鸿蒙原子化服务/服务卡片的适配建议
3. 3-5 条启示，每条 80-120 字

格式：
{序号}. **{设计模式名称}**：{竞品案例}采用{核心设计模式}。
→ 鸿蒙启示：{可迁移至鸿蒙生态的具体建议}。
"""


# ─── D 赛道：技术文档（产品解剖）──────────────────

D_TECHDOC_SYSTEM = """你是 AI 产品设计架构师，专精于对 AI 产品做完整的设计解构。
写作风格：结构化、技术准确、信息架构分析清晰、不做表面描述。"""

# 产品解剖
PROMPT_PRODUCT_ANATOMY = """【D 技术文档赛道】产品解剖

输入：{product_json}

对一个 AI 产品做完整设计解构：

## {产品名}

### 信息架构
{A. 导航结构 B. 内容层级 C. 状态管理}

### 交互流程
{A. 核心用户旅程 B. 关键决策点 C. 错误/边界状态处理}

### 视觉语言
{A. 配色体系 B. 字体层级 C. 图标系统 D. 动效语言}

### 技术实现推测
{前端框架/组件库/动画方案的推测}

### 可迁移的设计模式
{3-5 个可以抽象出来复用的设计模式}
"""


# ─── E 赛道：科普（交互模式进化）──────────────────

E_SCIENCE_SYSTEM = """你是 AI 交互设计科普作者，专精于将复杂的交互范式进化用通俗易懂的方式解释。
写作风格：类比生动、逻辑清晰、避免技术黑话、让非设计师也能理解。"""

# 交互模式进化
PROMPT_INTERACTION_EVO = """【E 科普赛道】交互模式进化

输入：{paradigm_signals_json}

为本周出现的新交互范式做科普解释：

## {范式名称}
### 是什么？
{用生活类比解释——不要用技术术语}

### 为什么出现？
{技术驱动力 + 用户需求变化}

### 怎么用？
{使用场景举例，图文描述}

### 会改变什么？
{对设计师/开发者/用户的影响}
"""


# ─── 设计模式词汇库 ────────────────────────────────

DESIGN_PATTERNS = {
    "conversational_ui": {
        "name": "对话式界面",
        "description": "用户通过自然语言与系统交互，系统以对话气泡/卡片形式回应",
        "examples": ["ChatGPT", "Claude", "Perplexity"],
    },
    "card_based_layout": {
        "name": "卡片化布局",
        "description": "信息以独立卡片组织，每张卡片包含完整的信息单元",
        "examples": ["Notion AI", "Coda", "Tome"],
    },
    "generative_ui": {
        "name": "生成式 UI",
        "description": "AI 根据用户意图实时生成界面组件，非预定义固定布局",
        "examples": ["Vercel v0", "Lovable", "Bolt.new"],
    },
    "agent_ux": {
        "name": "Agent UX（代理式交互）",
        "description": "面向 AI 代理而非工具的交互设计，用户设定目标，AI 自主执行",
        "examples": ["Devin", "OpenAI Operator", "Manus"],
    },
    "multimodal_fusion": {
        "name": "多模态融合输入",
        "description": "语音/文字/图片/文件拖放无缝切换的统一输入体验",
        "examples": ["ChatGPT Advanced Voice", "Apple Intelligence"],
    },
    "dark_theme_ai": {
        "name": "AI 原生深色主题",
        "description": "深色底 + 高对比亮色关键信息，减少视觉噪音聚焦内容",
        "examples": ["Cursor", "GitHub Copilot", "Claude"],
    },
    "inline_ai": {
        "name": "内联 AI 辅助",
        "description": "AI 功能内嵌到已有工作流中，而非作为独立聊天窗口",
        "examples": ["Notion AI", "Linear AI", "Figma AI"],
    },
    "cross_device_continuity": {
        "name": "跨设备连续性",
        "description": "AI 会话和上下文在不同设备间无缝流转",
        "examples": ["Apple Handoff", "Samsung Continuity"],
    },
}

HARMONY_DESIGN_PRINCIPLES = {
    "service_card": {
        "name": "原子化服务卡片",
        "principle": "将 AI 能力封装为可分发、可组合的服务卡片，而非完整 App",
        "inspiration": "iOS Widget + Android Glance → 鸿蒙元服务的 AI 化升级",
    },
    "super_device": {
        "name": "超级终端多设备协同",
        "principle": "利用分布式软总线实现 AI 体验的跨设备无缝流转",
        "inspiration": "Apple Continuity + Samsung Multi Control → 鸿蒙超级终端的 AI 场景化",
    },
    "one_time_consume": {
        "name": "即用即走",
        "principle": "AI 功能以「服务」而非「应用」的形式存在，免安装、用完即走",
        "inspiration": "微信小程序 + App Clips → 鸿蒙元服务的 AI 轻量化",
    },
}

# ─── 差异度阈值 ────────────────────────────────────

STAGE_DIVERSITY_THRESHOLD = 0.50
