# 通俗历史长文本作品 · 全自动生产体系 SOP 完整版

> 版本：V3.0（交响乐版）
> 日期：2026-07-10
> 来源：基于"全自动内容生产体系"V2.0 方法论 + 19 轮深度讨论 + 设计需求文档 + 平台构建素材全集

---

## 一、总纲：核心理念

**将专家经验规则化、内容结构模板化、表现力参数化，把大模型从"创作者"降级为"受控执行器"。模型只做选择题（选模板、填槽位），不做作文题（自由创作）。**

### 与教材的本质区别

| 维度 | 教材 | 历史通俗作品 |
|---|---|---|
| 驱动方式 | 大纲驱动（知识点全集固定） | **目标驱动**（选材有自由度，需主动"挑戏"） |
| 立场 | 追求共识性正确 | **有立场的共鸣**（史观参数化） |
| 读者 | 按年级预设前置知识 | **动态寻找读者连接点**（认知桥+情感桥） |
| 叙事 | 逻辑清晰即可 | **必须全程无尿点**（心理动力学编排） |
| 品牌 | 教材品牌靠出版社背书 | **风格即品牌**（系列 Profile 驱动） |

---

## 二、业务流总览图（一页全景）

```
┌─① 冷启动 ────────────────────────────────────┐
│  Series Profile | 史观包 | 读者画像           │
│  标签体系 | 10 模板库 | 文风包 | 张力模板     │
│  ← 一次性重投入，定义"审美标准"              │
└─────────────────────┬────────────────────────┘
                      ↓
┌─② 选材引擎 ──────────────────────────────────┐
│  Narrative Intent → 加权评分 → 约束过滤      │
│  → 编辑干预(pin/boost/exclude)               │
│  ← 目标驱动，决定"讲什么"                   │
└─────────────────────┬────────────────────────┘
                      ↓
┌─③ 编排（COG + PDL）─────────────────────────┐
│  模板选择器三层漏斗 → 角色指派              │
│  悬念/张力阶梯/高潮/呼吸/冲击力/主旋律     │
│  钩子系统(章首/章尾/中间钩)                 │
│  ← 决定"怎么讲"                            │
└─────────────────────┬────────────────────────┘
                      ↓
┌─④ 对抗评审 ──────────────────────────────────┐
│  史观审计员 | 读者代言人 | 叙事评论家       │
│  真实性守护者 | 视角挑战者                  │
│  （三级强度：轻/中/重）                     │
│  ← 质量关卡，倒逼内容韧性                  │
└─────────────────────┬────────────────────────┘
                      ↓ （不通过→返回③修改）
┌─⑤ 受控生成 ──────────────────────────────────┐
│  LLM 填槽（选择题/填空题，非自由创作）       │
│  四层注入：史观→读者连接→文风→冲击力/主旋律 │
│  输出后校验（禁用词/张力/风格JS散度）        │
└─────────────────────┬────────────────────────┘
                      ↓
┌─⑥ 多模态输出 ────────────────────────────────┐
│  结构化文本 | SSML音频脚本                   │
│  动画分镜标签 | 交互知识卡片                 │
└──────────────────────────────────────────────┘
```

---

## 阶段一：冷启动——定义"审美标准"（一次性重投入）

这一阶段是整个体系投入最大的部分——把"什么是好的历史作品"这一隐性标准，变成显式、可参数化、可审计的配置资产。

### 1.1 定义 Series Profile（系列品牌 DNA）

```yaml
series_profile:
  series_id: "the_structure_of_china"
  brand_name: "结构中国：大历史的解剖"
  version: "1.0"

  # ① 共享史观（可被子书局部 override）
  historiography_profile_ref: "structural_materialist_v1"
  core_values:
    - "尊重史实：一切结论基于可核查史料"
    - "追问结构：优先追问制度、技术、财政等结构性成因"
    - "关怀个体：在宏大结构中看见人的挣扎与尊严"
    - "当代回响：坚持'一切历史都是当代史'，引导读者反观当下"

  # ② 共享主旋律（Motif）——品牌记忆锚点
  core_motif:
    statement: "宏大叙事的崩塌，始于技术治理的缺位。"
    contemporary_echo: true
    recurrence: "per_chapter"                # 每章出现
    variation_policy: "progressive_deepening" # 每本递进（点出→展开→当代方案暗示）

  # ③ 共享文风包（系列"嗓音"）
  style_pack_ref: "cp_history_huang_renyu_v1"
  style_lock:
    forbidden_deviations:
      - "colloquial_slang_heavy"    # 禁止过于口语化
      - "heroic_epic_tone"          # 禁止英雄史诗语调
      - "shock_clickbait"           # 禁止震惊体

  # ④ 共享模板偏好（系列"叙事性格"）
  template_role_preference:
    primary: [TPL_01, TPL_09]       # 微观撬动 + 长时段（主力）
    secondary: [TPL_03, TPL_08]     # 制度悲剧 + 历史反转（辅助）
    discourage: [TPL_02]            # 少用人格英雄叙事

  # ⑤ 共享冲击力 & 节奏签名
  impact_policy:
    require_counter_intuitive: true
    max_sensationalism: "low"
  pacing_signature:
    breathe_ratio: "one_low_density_per_two_high"
    climax_always_in: "structure_unit"

  # ⑥ 共享读者基调（可被子书细化）
  base_reader_persona: "educated_general_with_curiosity"

  # ⑦ 品牌标识（跨模态扩展）
  brand_signature:
    cover_motif: "fractured_continuum"            # 封面色调意象
    audio_intro_ssml: "<break time='800ms'/>本系列，看历史的结构。"
```

### 1.2 建设五大生产资料库

#### 1.2.1 统一标签体系

**叙事类型标签**（10个）：

| 标签ID | 含义 | 典型模板关联 |
|--------|------|-------------|
| `#scene_setting` | 场景铺垫 | TPL-01/09情境单元 |
| `#event_trigger` | 事件触发 | TPL-01/04事件单元 |
| `#decision_point` | 决策点 | TPL-02事件单元 |
| `#consequence` | 后果展现 | TPL-02/03后果单元 |
| `#turning_point` | 转折点 | TPL-04分析单元 |
| `#micro_event` | 微观事件 | TPL-01必选 |
| `#climax_decision` | 高潮决策 | TPL-02高潮单元 |
| `#counterfactual` | 假设分析 | TPL-02反思单元 |
| `#dramatic_irony` | 戏剧性反讽 | TPL-01/03核心张力 |
| `#moral_dilemma` | 道德困境 | TPL-02/03人物单元 |

**分析类型标签**（7个）：

| 标签ID | 含义 | 典型模板 |
|--------|------|----------|
| `#institutional_analysis` | 制度分析 | TPL-01, TPL-03 |
| `#long_term_causality` | 长周期因果 | TPL-09 |
| `#comparative_history` | 比较史学 | TPL-04 |
| `#structural_explanation` | 结构解释 | TPL-01, TPL-03 |
| `#technological_breakthrough` | 技术突破 | TPL-05 |
| `#intellectual_crisis` | 思想危机 | TPL-06 |
| `#social_restructuring` | 社会重组 | TPL-05 |

**人物维度标签**（7个）：

| 标签ID | 含义 |
|--------|------|
| `#character_trait` | 性格特质刻画 |
| `#motivation` | 动机分析 |
| `#contradiction` | 内在矛盾/两难 |
| `#individual_agency` | 个人能动性 |
| `#idealistic_actor` | 理想主义者 |
| `#ordinary_people` | 普通人/底层 |
| `#great_man_focus` | 英雄史观视角 |

**史学立场标签**（5个）：`#materialist` / `#cultural` / `#great_man` / `#structural` / `#revisionist_evidence`

**知识类型标签**（9个）：`#concept_intro` / `#analogy` / `#formal_def` / `#derivation` / `#experiment` / `#boundary_misconception` / `#historical_note` / `#philosophical_implication`

**难度/深度标签**（3个）：`#layman` / `#enthusiast` / `#technical_appendix`

**呈现约束标签**（9个）：

| 标签ID | 渲染行为 |
|--------|----------|
| `#boxed_analogy` | 灰底类比框，可折叠 |
| `#boxed_context` | 可折叠背景知识框 |
| `#timeline_bar` | 横向或纵向时间轴 |
| `#character_card` | 人物小传卡片 |
| `#what_if_sidebar` | "假如……"假设分析侧栏 |
| `#primary_source` | 原始史料引用块 |
| `#sidebar_bio` | 侧边栏人物简介 |
| `#math_block` | 独立公式块 |
| `#comparison_table` | 双栏对比布局 |

#### 1.2.2 10 种叙事模板库（完整规格）

**设计原则**：模板 = 单元编排规则 + 约束条件 + 表现力锚点。模板不是写作套路（那是Prompt），而是可被规则引擎执行的单元组装指令。

---

**TPL-01｜小事撬动大局（黄仁宇式）**

| 属性 | 内容 |
|------|------|
| 适用 | 制度史、政治史、长周期因果分析 |
| 核心逻辑 | 微观事件 → 宏观结构跃升 |
| 结构序列 | 情境单元 → 事件单元 → 人物单元 → 结构单元 → 反思单元 |
| required_tags | `#micro_event`, `#institutional_constraint` |
| forbidden_tags | `#heroic_triumph` |
| 过渡规则 | event_unit → structure_unit（强制） |
| PDL 特殊槽位 | `dramatic_irony_marker`（认知落差）、`iceberg_marker`（冰山隐喻）、`ticking_clock`（时间压力） |
| 张力弧线 | narrative_hook → slow_buildup → dramatic_irony → structural_reveal |
| 角色亲和度 | anchor_event=**3**, deep_dive=2, counterpoint=1, macro_frame=2, synthesis=0, bridge=2 |
| 示例 | 万历十五年，一封关于官员考核的普通奏折，暴露出整个文官集团与皇权的结构性死结 |

---

**TPL-02｜命运抉择时刻（通俗传记式）**

| 属性 | 内容 |
|------|------|
| 适用 | 人物中心叙事、关键历史转折点 |
| 核心逻辑 | 压力 → 抉择 → 不可逆后果 |
| 结构序列 | 情境单元 → 人物单元 → 事件单元(抉择) → 后果单元 → 反思单元(含反事实) |
| required_tags | `#decision_point`, `#character_trait` |
| PDL 特殊槽位 | `stakes_clarity`（抉择代价）、`path_not_taken`（未被选择的道路） |
| 允许 | psychological_portrayal=deep, allow_counterfactual=true |
| 张力弧线 | narrative_hook → rising_tension → climax_decision → reflective_close |
| 角色亲和度 | anchor_event=**3**, deep_dive=2, counterpoint=0, macro_frame=0, synthesis=1, bridge=1 |
| 示例 | 鸿门宴上，项羽放走刘邦——那一刻，不是仁慈，而是政治直觉的缺席 |

---

**TPL-03｜制度杀人（悲剧宿命式）**

| 属性 | 内容 |
|------|------|
| 适用 | 政治清洗、变法失败、忠臣悲剧 |
| 核心逻辑 | 好人 + 好意 → 坏制度 → 必然毁灭 |
| 结构序列 | 人物单元 → 情境单元 → 事件单元 → 结构单元 → 后果单元 → 反思单元 |
| required_tags | `#idealistic_actor`, `#rigid_institution` |
| 约束 | dramatic_irony=high, moral_judgment=discouraged |
| 张力弧线 | character_intro → hope_buildup → dramatic_irony → tragic_climax |
| 注意 | 情绪压抑，不宜连续使用，需搭配 lighter 模板 |
| 角色亲和度 | anchor_event=2, deep_dive=**3**, counterpoint=1, macro_frame=1, synthesis=0, bridge=1 |
| 示例 | 张居正死后被清算，不是因为贪腐，而是因为他触碰了明代财政制度的隐形红线 |

---

**TPL-04｜文明碰撞（全球史/比较史）**

| 属性 | 内容 |
|------|------|
| 适用 | 中西对比、殖民史、技术传播 |
| 核心逻辑 | 两种逻辑体系的不对称相遇 |
| 结构序列 | 情境单元A → 情境单元B → 事件单元 → 分析单元 → 后果单元 → 反思单元 |
| required_tags | `#civilization_A`, `#civilization_B`, `#asymmetric_encounter` |
| 约束 | avoid_value_judgment=true |
| 张力弧线 | curiosity_hook → cultural_shock → analytical_expansion → reflective_close |
| 角色亲和度 | anchor_event=2, deep_dive=2, counterpoint=2, macro_frame=**3**, synthesis=1, bridge=1 |

---

**TPL-05｜技术改变社会（科技史/经济史）**

| 属性 | 内容 |
|------|------|
| 适用 | 农业革命、工业革命、信息革命 |
| 核心逻辑 | 技术突破 → 社会结构重组 |
| 结构序列 | 情境单元 → 事件单元 → 分析单元 → 结构单元 → 反思单元 |
| required_tags | `#technological_breakthrough`, `#social_restructuring` |
| 优点 | 唯一一个在 deep_dive 和 macro_frame 上都得 3 分的模板 |
| 张力弧线 | status_quo → disruptive_event → structural_shift → philosophical_reflection |
| 角色亲和度 | anchor_event=1, deep_dive=**3**, counterpoint=1, macro_frame=**3**, synthesis=2, bridge=1 |

---

**TPL-06｜观念诞生记（思想史/文化史）**

| 属性 | 内容 |
|------|------|
| 适用 | 启蒙运动、文艺复兴、新文化运动 |
| 核心逻辑 | 旧观念危机 → 新思想孕育 → 社会接受/排斥 |
| 结构序列 | 情境单元 → 人物单元 → 事件单元 → 分析单元 → 后果单元 → 反思单元 |
| required_tags | `#intellectual_crisis`, `#new_paradigm` |
| 张力弧线 | intellectual_discomfort → breakthrough_moment → social_resistance → long_term_impact |
| 角色亲和度 | anchor_event=1, deep_dive=**3**, counterpoint=2, macro_frame=2, synthesis=**3**, bridge=1 |

---

**TPL-07｜被遗忘的多数（社会史/微观史）**

| 属性 | 内容 |
|------|------|
| 适用 | 平民生活、女性史、底层视角 |
| 核心逻辑 | 宏大叙事之外普通人的真实生存逻辑 |
| 结构序列 | 情境单元 → 事件单元 → 人物单元 → 分析单元 → 反思单元 |
| required_tags | `#ordinary_people`, `#daily_life` |
| 约束 | avoid_great_man_theory=true |
| 编排价值 | 防止章节过于精英化，在密集分析后提供人文温度 |
| 张力弧线 | quiet_daily_life → disruption → resilience → historiographical_reflection |
| 角色亲和度 | anchor_event=2, deep_dive=2, counterpoint=**3**, macro_frame=1, synthesis=1, bridge=**3** |

---

**TPL-08｜历史反转（侦探式/修正史）**

| 属性 | 内容 |
|------|------|
| 适用 | 翻案文章、重新评价历史人物/事件 |
| 核心逻辑 | 常识认知 → 新证据 → 认知反转 |
| 结构序列 | 情境单元(常识) → 事件单元(新史料) → 分析单元 → 结构单元 → 反思单元 |
| required_tags | `#popular_myth`, `#revisionist_evidence` |
| PDL 特殊槽位 | `common_belief`（复述常识）、`subversion_trigger`（引爆反转的细节）、`cognitive_dissonance`（常识崩塌后的空白） |
| 张力弧线 | familiar_narrative → cognitive_conflict → paradigm_shift → nuanced_conclusion |
| 角色亲和度 | anchor_event=1, deep_dive=2, counterpoint=**3**, macro_frame=1, synthesis=2, bridge=2 |

---

**TPL-09｜长时段缓慢变化（布罗代尔式）**

| 属性 | 内容 |
|------|------|
| 适用 | 气候史、地理史、长周期社会变迁 |
| 核心逻辑 | 几乎不变 → 缓慢积累 → 突然显现 |
| 结构序列 | 情境单元(稳态) → 分析单元(缓慢指标) → 事件单元(临界点) → 结构单元 → 反思单元 |
| required_tags | `#longue_duree`, `#gradual_accumulation` |
| 约束 | event_unit=de_emphasized, tempo=slow/panoramic/detached |
| 编排建议 | 常作为章节或全书的结尾，提供宿命感和哲学反思 |
| 张力弧线 | stasis → slow_acceleration → sudden_emergence → macro_reflection |
| 角色亲和度 | anchor_event=0, deep_dive=2, counterpoint=0, macro_frame=**3**, synthesis=2, bridge=1 |

---

**TPL-10｜复调历史（多视角并置）**

| 属性 | 内容 |
|------|------|
| 适用 | 复杂冲突、民族矛盾、战争史 |
| 核心逻辑 | 同一事件，不同立场，各自合理 |
| 结构序列 | 情境单元 → 人物单元A(视角A) → 人物单元B(视角B) → 分析单元 → 反思单元 |
| required_tags | `#multiple_perspectives`, `#structural_conflict` |
| 约束 | balance_perspectives=true, equal_empathy |
| 张力弧线 | neutral_setup → divergent_views → structural_inevitability → tragic_ambiguity |
| 角色亲和度 | anchor_event=1, deep_dive=1, counterpoint=**3**, macro_frame=2, synthesis=2, bridge=2 |

---

#### 1.2.3 模板 × 角色亲和度矩阵（10×6 完整表）

| 模板ID | anchor_event | deep_dive | counterpoint | macro_frame | synthesis | bridge |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| TPL-01 | **3** | 2 | 1 | 2 | 0 | 2 |
| TPL-02 | **3** | 2 | 0 | 0 | 1 | 1 |
| TPL-03 | 2 | **3** | 1 | 1 | 0 | 1 |
| TPL-04 | 2 | 2 | 2 | **3** | 1 | 1 |
| TPL-05 | 1 | **3** | 1 | **3** | 2 | 1 |
| TPL-06 | 1 | **3** | 2 | 2 | **3** | 1 |
| TPL-07 | 2 | 2 | **3** | 1 | 1 | **3** |
| TPL-08 | 1 | 2 | **3** | 1 | 2 | 2 |
| TPL-09 | 0 | 2 | 0 | **3** | 2 | 1 |
| TPL-10 | 1 | 1 | **3** | 2 | 2 | 2 |

**3**=天生契合首选，**2**=可用次选，1=勉强可用需人工微调，0=违和禁止自动选用。加粗为主角色。

---

### 1.3 史观参数包（Historiography Profile）

管"说什么、站在哪边、褒谁贬谁"，与文风包（管"怎么说"）解耦。

```yaml
historiography_profile:
  profile_id: "structural_materialist_v1"
  display_name: "结构唯物主义史观"
  version: "1.0"

  # ① 核心立场向量（-1.0至+1.0，可量化可审计）
  stance_vector:
    individual_agency: -0.3          # 个人作用权重（负=结构为主）
    structural_determinism: 0.8      # 结构决定论强度
    moral_judgment: -0.7             # 道德评判倾向（负=少道德化）
    great_man_theory: -0.8           # 英雄史观（负=反对）
    popular_agency: 0.6              # 群众能动性
    cultural_relativism: 0.0

  # ② 情绪基调（全局情绪底色）
  emotional_tone:
    default: "sober_detached"                    # 冷静、略带悲观
    toward_power: "skeptical"                    # 对权力方怀疑
    toward_vulnerable: "empathetic_but_not_sentimental"  # 对弱势方共情但不煽情

  # ③ 价值观关键词
  value_keywords:
    approved:
      - "制度困境"
      - "结构性矛盾"
      - "技术治理"
      - "路径依赖"
      - "资源约束"
    discouraged:
      - "昏庸"
      - "奸佞"
      - "圣明"
      - "天意"
      - "天命所归"
    forbidden:
      - "种族优劣"
      - "历史宿命论（非结构性）"

  # ④ 模板偏好（影响模板选择器评分）
  template_bias:
    TPL_01: 0.2      # 偏好小事撬动大局
    TPL_03: 0.2      # 偏好制度杀人
    TPL_02: -0.3     # 降低命运抉择（个人英雄）
    TPL_09: 0.1      # 偏好长时段
    TPL_05: 0.1

  # ⑤ 情绪注入规则
  emotion_injection:
    toward_systemic_tragedy: "quiet_sorrow"                    # 制度悲剧：安静悲伤
    toward_individual_struggle: "restrained_respect"           # 个人挣扎：克制敬意
    toward_irony_of_history: "subtle_irony_no_laughter"       # 历史反讽：不强笑

  # ⑥ 主旋律定义
  core_motif:
    statement: "缺乏技术治理支撑的道德教化，终将沦为系统性谎言。"
    contemporary_echo: "现代组织的KPI崇拜，若缺乏底层数据支撑，亦是另一种道德教化。"
    emotional_color: "sober_warning"
    recurrence_frequency: "per_chapter"
```

### 1.4 读者画像（Reader Persona）

```yaml
reader_persona:
  persona_id: "burned_out_professional_v1"
  display_name: "职业倦怠白领"

  # ① 认知基线（三级标注）
  knowledge_assumptions:
    history:
      solid: ["鸦片战争", "辛亥革命", "改革开放"]
      fuzzy: ["王安石变法", "一条鞭法", "军机处"]
      unknown: ["明代财政技术细节", "漕运具体流程"]
    general:
      solid: ["职场晋升逻辑", "KPI压力", "部门内斗", "流程审批"]

  # ② 认知桥梁域（类比来源）
  cognitive_style:
    prefers_analogy_from:
      - "corporate_structure"       # 公司组织架构
      - "project_management"        # 项目管理
      - "office_politics"           # 办公室政治
    dislikes:
      - "excessive_dates"           # 嫌日期太多
      - "pure_military_details"     # 嫌纯军事细节

  # ③ 情感原型
  emotional_archetype:
    primary: "ambitious_but_trapped_professional"  # 有抱负但被困住
    resonates_with:
      - "systemic_frustration"       # 对系统的挫败感
      - "career_ceiling"             # 职业天花板
      - "process_over_personal"      # 流程压死人
      - "overworked_leader"          # 超负荷的管理者
    repelled_by:
      - "peasant_uprising_glorification"  # 美化农民起义
      - "pure_battle_heroism"             # 纯战斗英雄主义

  # ④ 阻抗地图
  resistance_map:
    triggers: ["道德说教", "宏大空话", "纯军事细节"]
    avoidance_strategy: "用管理类比替代道德评价，用数据替代空话"

  # ⑤ 深层需求
  deep_needs:
    - "验证自己的职场挫折具有普遍性"
    - "获得超越日常琐事的宏大视角"
    - "为自己的无力感找到结构性解释"

  # ⑥ 语言亲和度
  language_affinity:
    preferred_register: "semi_formal_with_colloquial_touch"
    taboo_expressions: ["你应该", "这就是命"]
    preferred_sentence_len: "medium"
```

### 1.5 文风包——五层形式化维度

```yaml
style_pack:
  id: cp_history_huang_renyu_v1
  meta:
    genre: new_socio_history
    audience: educated_general

  # Layer 1 · Persona（叙述者角色）
  persona:
    narrator: "detached_observer_with_structural_vision"
    tone: "calm_analytical_with_subtle_irony"
    persona_desc: "冷静的制度观察者，用结构解释代替道德评判"
    intimacy: 2
    authority: 4
    drama: 3

  # Layer 2 · Lexical Pool（词汇池）
  lexical_pool:
    openers:
      - "从表面上看，"
      - "若从制度层面审视，"
      - "这并非偶然——"
    connectors:
      - "换言之"
      - "由此观之"
      - "其背后隐含着"
    historical_markers:
      - "当日"
      - "彼时"
      - "终明一代"
    transition_to_macro:
      - "然而，将xx归咎于yy，是一种危险的简化。"
      - "若将镜头拉远至整个世纪……"
    forbidden:
      - "令人震惊"
      - "不可思议"
      - "昏庸"
      - "奸佞"
      - "圣明"
      - "天意"

  # Layer 3 · Syntactic Bias（句式偏好）
  syntax_bias:
    sentence_len: "medium_long"        # 偏好中长句
    clause_density: "high"             # 从句密度高
    passive_voice: "allowed"           # 允许被动语态
    dash_usage: "moderate"             # 破折号适量
    paragraph_break_freq: "moderate"   # 段落适中

  # Layer 4 · Rhetorical Ops（修辞开关）
  rhetoric:
    irony_subtle: true                 # 微妙反讽
    macro_micro_link: always           # 必做微观→宏观跳跃
    primary_source_quotes: "sparse_but_precise"  # 史料引用少而精
    moral_judgment: discouraged        # 避免道德评价

  # Layer 5 · Layout/Pacing（布局与节奏）
  narrative_pacing:
    event_description: "concise"        # 事件描述简洁
    structural_analysis: "expansive"    # 结构分析展开
  tension_map:
    dramatic_irony:
      narrator_distance: high
      hint_without_spelling_out: true
    structural_reveal:
      slow_unfold: true
      link_to_theme: "magnitude_of_institutions"
```

---

## 阶段二：选材——决定"讲什么"

### 2.1 叙事意图（Narrative Intent）——选材的一级驱动

| 意图 | 选材偏好 | 示例 |
|------|----------|------|
| `INTENT_EPIC` | 标志性转折事件、制度突变点、跨文明对比 | 《人类简史》式 |
| `INTENT_MICRO` | 普通人日记、器物、地方档案、日常琐事 | 《奶酪与蛆虫》式 |
| `INTENT_TRAGEDY` | 改革者困境、制度反弹、理想↔现实落差 | 王安石、张居正 |
| `INTENT_REVISION` | 被误读人物/事件、冷门一手史料 | 李鸿章翻案 |
| `INTENT_PERSONAL` | 关键抉择点、书信、内心冲突 | 人物传记式 |
| `INTENT_IDEATIONAL` | 关键文本、论战、概念演变节点 | 启蒙观念传播 |

### 2.2 知识节点数据结构（选材加权字段）

```yaml
knowledge_node:
  node_id: "event_wanli_15_zhangju_zheng"
  node_type: event
  date: "1587"
  summary: "万历十五年，张居正死后五年，改革成果逐步被清算，文官集团与皇权陷入结构性僵局。"

  labels:
    content: ["#micro_event", "#administrative_dispute", "#personnel_issue"]
    actor: ["#scholar_official", "#emperor", "#bureaucracy"]
    structure: ["#institutional_constraint", "#fiscal_system"]
    scale: ["#single_incident", "#long_term_consequence"]
    narrative_potential: ["#dramatic_irony", "#systemic_trap"]

  actors:
    - name: "万历皇帝"
      traits: ["passive_resentful", "trapped_by_ritual"]
    - name: "申时行"
      role: "首辅"
      dilemma: "调和君臣 vs 维持制度"

  context:
    institutional: "文官集团制衡皇权"
    long_term_causality: "财政僵化 → 改革受阻"

  narrative_hooks:
    - "一封被搁置的奏折"
  structural_insights:
    - "道德治国与技术治理的张力"

  # ---- 选材加权字段（核心） ----
  significance:
    political: 0.6
    economic: 0.2
    cultural: 0.8
    personal_agency: 0.5
    symbolic_power: 0.9

  dramatic_potential:
    has_dramatic_irony: true
    has_moral_dilemma: true
    has_visible_consequence: false
    score: 0.85

  source_quality:
    primary_sources: 3
    reliability: "high"
    contemporary: true

  narrative_fit_tags:
    - "INTENT_TRAGEDY"
    - "INTENT_MICRO"
    - "INTENT_REVISION"

  typical_reader_resonance:
    burned_out_professional: 0.7
    student_lay: 0.4

  # ---- 冲击力字段 ----
  impact_potential:
    counter_intuitive_score: 0.7
    precision_data:
      value: "国库仅余白银2300两"
      context: "尚不足皇室一日脂膏"
      source: "《明实录·崇祯朝》"
    emotional_valence: "quiet_despair"
    memorable_phrase_seed: "道德无法填补制度的真空"

  # ---- 依赖关系 ----
  relations:
    precedes: ["salhu_defeat_1619"]
    part_of: ["wanli_reign_crisis"]
    contradicts: ["heroic_narrative_zhang_juzheng"]
    depends_on: ["ming_cabinet_system_definition"]

  default_style_pack: "cp_history_huang_renyu_v1"
  default_tension_arc: ["narrative_hook", "slow_buildup", "dramatic_irony", "structural_reveal"]
```

### 2.3 选材评分公式

```
SelectionScore = α·IntentFit + β·DramaticPotential + γ·SourceQuality + δ·ReaderResonance + ε·HistoriographyBias
```

各项含义与默认权重：

| 项 | 含义 | 计算方式 | 默认权重 | 通俗版 | 学术版 |
|----|------|----------|---------|--------|--------|
| IntentFit | 叙事意图匹配度 | narrative_fit_tags 含当前 INTENT → 1，否则降权 | α=0.35 | 0.30 | 0.35 |
| DramaticPotential | 戏剧性潜质 | 直接读取 score 字段 | β=0.25 | 0.30 | 0.15 |
| SourceQuality | 史料可靠性 | (primary_sources × reliability_factor) 归一化 | γ=0.15 | 0.10 | 0.20 |
| ReaderResonance | 读者共鸣度 | typical_reader_resonance[persona_id] | δ=0.15 | 0.20 | 0.10 |
| HistoriographyBias | 史观亲和度 | HP.stance_vector 与 significance 向量点积 | ε=0.10 | 0.10 | 0.20 |

### 2.4 选材约束（五项硬约束）

```yaml
selection_constraints:
  - name: "coverage_balance"
    desc: "同一章至少包含一个 #micro_event 和一个 #structural_explanation"
  - name: "time_order_respected"
    desc: "除非 flashback 明确标记，否则节点按时间升序"
  - name: "no_single_perspective"
    desc: "TRAGEDY/REVISION 章节须包含 ≥1 对立视角节点"
  - name: "drama_density_cap"
    desc: "连续 >2 个 dramatic_potential>0.8 的节点需插入 ≤0.4 的缓和节点"
  - name: "source_minimum"
    desc: "每个选定事件须有 ≥1 primary_source 或 high reliability 的二手史料"
```

### 2.5 编辑干预接口

```yaml
editor_override:
  - action: "boost +0.3"
    bind: "node_id"
    reason: "作者认为此事件是全书结构困境的最佳象征"
  - action: "pinned: true"
    bind: "node_id"
    reason: "必选事件，构成全书叙事主线"
  - action: "excluded: true"
    bind: "node_id"
    reason: "史料争议过大，不适合这本书的基调"
  - action: "weight_adjustment"
    bind: "selection_weights"
    params:
      beta_drama: 0.30     # 作者偏重戏剧性
      gamma_source: 0.10   # 不那么看重考据
    reason: "本系列面向大众读者，戏剧性优先"
```

所有干预操作记录原因，形成可复用的「选材品味档案」。

---

## 阶段三：编排（COG + PDL）——决定"怎么讲"

### 3.1 模板选择器——三层漏斗模型

```
Layer 1：硬性过滤（Hard Filter）
  每个模板声明 precondition（required_labels / forbidden_labels / min_scale / preferred_node_type），不满足直接淘汰
  输出：候选模板列表（通常 2-3 个）

Layer 2：加权评分（Scoring Model）
  TemplateScore = 0.4×LabelOverlap + 0.25×StructuralFit + 0.2×NarrativePotential + 0.1×SourceRichness + 0.05×HistoriographyMatch
  标签重合度用 Jaccard 相似系数计算
  结构契合度考察节点在知识图谱中的位置（如 TPL-01 偏好 part_of 节点 +0.3）
  叙事潜力考察 dramatic_irony/moral_dilemma 标签

Layer 3：语境修正（Contextual Adjustment）
  章节位置修正：开篇偏好 TPL-01/TPL-04 +0.1，转折偏好 TPL-02/TPL-08 +0.1，结尾偏好 TPL-09/TPL-10 +0.1
  前后文去重：连续两节相同模板 -0.15
  史观参数修正：HP.template_bias 直接加减
```

### 3.2 选择器决策记录输出格式

```json
{
  "selection_result": {
    "selected_template": "TPL_01",
    "confidence": 0.87,
    "runner_up": {"template": "TPL_03", "score": 0.72},
    "decision_trace": {
      "hard_filter": {
        "passed": true,
        "eliminated": ["TPL_09 (scale mismatch)", "TPL_02 (missing #decision_point)"]
      },
      "scoring": {
        "label_overlap": 0.92,
        "structural_fit": 0.80,
        "narrative_potential": 0.70,
        "source_richness": 0.90,
        "historiography_match": 1.00
      },
      "contextual_adjustment": {
        "chapter_position_bonus": "+0.05 (opening chapter)",
        "repetition_penalty": "none"
      }
    }
  }
}
```

### 3.3 章节编排语法（COG）——六种角色与四种编排模式

**六种章节角色**：

| 角色 | 定义 | 常配模板 | 作用 |
|------|------|----------|------|
| anchor_event | 锚定事件，章节起点 | TPL-01(3), TPL-02(3) | 吸引读者入场 |
| deep_dive | 深入制度/心理内部 | TPL-03(3), TPL-05(3), TPL-06(3) | 核心论证 |
| counterpoint | 提供对立/修正视角 | TPL-08(3), TPL-10(3), TPL-07(3) | 打破单一叙事 |
| macro_frame | 提供长时段/结构框架 | TPL-04(3), TPL-09(3), TPL-05(3) | 拉升认知维度 |
| synthesis | 综合前文，升华主题 | TPL-06(3), TPL-07(1) | 收束全章 |
| bridge | 承上启下 | TPL-01(2), TPL-07(3) | 章节间过渡 |

**四种经典编排模式**：

```yaml
chapter_archetypes:
  archetype_a_micro_macro:
    description: "微观→修正→宏观"
    sequence: [anchor_event, counterpoint, macro_frame]
    recommended_ids: [TPL-01, TPL-08, TPL-09]

  archetype_b_tragedy:
    description: "抉择→毁灭→反思"
    sequence: [anchor_event, deep_dive, synthesis]
    recommended_ids: [TPL-02, TPL-03, TPL-06]

  archetype_c_clash:
    description: "碰撞→变革→复调"
    sequence: [macro_frame, deep_dive, counterpoint]
    recommended_ids: [TPL-04, TPL-05, TPL-10]

  archetype_d_page_turner:
    description: "高悬念、强节奏、情绪过山车（追更型）"
    sequence: [anchor_event, deep_dive, counterpoint, macro_frame]
    psychological_dynamics:
      opening_hook: "dramatic_irony"
      tension_curve: "sharp_rise_then_slow_burn"
      breathing:
        after_high_density: "insert_TPL_07_for_human_touch"
      climax:
        unit: "structure_unit_of_TPL_01_or_TPL_09"
        pacing: "slow_and_heavy"
      ending_hook:
        type: "foreshadowing"
        emotional_tone: "foreboding"
```

### 3.4 过渡规则（Transition Rules）

模板之间通过过渡单元衔接，不允许直接拼接：

```yaml
transition_types:
  cognitive_contrast:
    marker_pool: ["然而新证据表明——", "但事实远比常识复杂。", "若深入审视，却会发现另一番图景。"]
    tension_shift: increase
    required_tags: ["#revisionist_evidence"]

  temporal_expansion:
    marker_pool: ["若将镜头拉远至整个世纪……", "把时间轴向前推两百年……", "这一困境的种子，早在更早的时代便已埋下。"]
    tension_shift: scale_up
    time_jump: true

  psychological_deepening:
    marker_pool: ["在做出这一决定时，他内心并非毫无波澜。", "深夜的烛火下，他独自面对着一个无解的选择。"]
    tension_shift: intensify

  structural_leap:
    marker_pool: ["这并非孤例，而是整个系统的缩影。", "从个体的困境，我们看到的是制度的困境。"]
    tension_shift: abstract_up

# 过渡校验规则
transition_validation:
  - rule: "temporal_expansion 要求 to_tpl.scale > from_tpl.scale"
  - rule: "cognitive_contrast 要求前后标签存在冲突"
  - rule: "structural_leap 要求 to_tpl.has_tag('#macro_causality')"
  - rule: "心理深化后必须跟随 tension_shift 向上的单元"
```

### 3.5 心理动力学编排层（PDL）

PDL 将剧本/剧作手法翻译为模板系统的可执行约束，实现"全程无尿点"的工程化。

#### 3.5.1 认知落差槽（Dramatic Irony Slot）

每个 anchor_event 模板实例必须包含，在情境单元末尾插入：

> 示例："此时，申时行并不知道，这一封奏折将在十七年后，成为萨尔浒之战溃败的注脚。"

#### 3.5.2 张力阶梯规则

```yaml
tension_ladder:
  rules:
    - "每个 Section 标注 tension_level (0-1) 和 pressure_source"
    - "pressure_source 必须与前一节构成递进或转化关系"
    - "禁止 tension_level 连续下降（除非刻意制造'虚假安全感'）"
    - "张力不能在同一维度上累加超过3次（必须质变）"
  
  example:
    sec_01: { tension: 0.3, pressure_source: "routine_administrative_issue" }
    sec_02: { tension: 0.6, pressure_source: "institutional_backlash" }
    sec_03: { tension: 0.9, pressure_source: "systemic_collapse" }
```

#### 3.5.3 高潮设计

```yaml
climax_rules:
  - "每个 Chapter 有且仅有一个 is_chapter_climax: true 的单元"
  - "高潮单元必须是结构分析单元（TPL-01/03/09 的 structure_unit）"
  - "高潮节奏：慢、沉、重（不是快，是停顿和加重）"
  - "高潮前必须有明显的节奏变化（前紧后松或前快后慢）"
  - "高潮中必须注入 motif_variation(type: thesis)"
```

#### 3.5.4 节奏呼吸规则

```yaml
breathing_rules:
  density_classification:
    high: [TPL-03, TPL-06, TPL-09]    # 深度分析
    medium: [TPL-01, TPL-04, TPL-05]  # 叙事+分析
    low: [TPL-07, TPL-10]             # 感性/多视角

  constraints:
    - "高密度单元后必须跟中或低密度单元"
    - "连续三个中密度后必须插入低密度"
    - "结尾必须是中低密度（留给读者思考空间）"
```

#### 3.5.5 六大钩子槽位

| 钩子类型 | 位置 | 规则 |
|----------|------|------|
| 开篇悬念钩 | 章首 | 必须在 chapter 前 5% 篇幅内 |
| 认知落差钩 | 情境单元末 | 利用读者后见之明 |
| 矛盾钩 | 矛盾升级点 | 卡在 tension_level 从 low→mid 的拐点上 |
| 信息差钩 | 分析单元中 | 制造"后文会揭示"的期待 |
| 高潮钩 | 结构跃升前 | 在高潮单元的前一节末尾 |
| 结尾钩 | 章末 | 除最后一章外必须包含 foreshadowing |

**每章标配**：开篇悬念钩 + 结尾钩 + 中间至少一个（信息差钩或矛盾钩）

#### 3.5.6 冲击力注入规则

```yaml
impact_injection:
  positions:
    - name: "opening_hook"
      condition: "counter_intuitive_score > 0.7"
      format: "raw_data + contrast_context"
      example: "当李自成军队攻入北京时，他们发现国库里只剩2300两白银"
    
    - name: "conflict_escalation"
      condition: "tension_level 0.4→0.7 上升阶段"
      format: "precision_data（数字+来源）"
      source_annotation: required
    
    - name: "pre_climax_silence"
      condition: "在 climax_unit 之前一个单元末尾"
      format: "极简数据，单句成段，前后空行"
      example: "崇祯在谕旨中写下的最后一个数字是：2300。"
    
    - name: "ending_hook"
      condition: "结尾钩类型为 contemporary_echo"
      format: "precision_data 指向当下的映射"

  hard_constraints:
    - "require_primary_source: true"
    - "forbid_superlative_distortion: true"
    - "forbid_emotional_amplifier: true"
    - "source_context_required: true"
```

#### 3.5.7 主旋律记忆层（Motif Layer）

借鉴瓦格纳歌剧的 Leitmotif 手法，每章 4 节点变奏：

| 变奏位置 | 变奏类型 | 示例 |
|----------|----------|------|
| 开篇陈述 | statement | "这又是一个试图用道德填补技术真空的故事。" |
| 矛盾激化 | rhetorical_question | "当流程只剩道德口号，谁来填补那2300两白银的亏空？" |
| 高潮论断 | thesis | "道德是锦上添花，技术是雪中送炭。" |
| 结尾警句 | epigram | "历史从不重复，但缺乏技术底座的宏大叙事，总会以相似的方式塌方。" |

每章三节点强制（开篇/高潮/结尾）+ 当代映射强制。

**防空洞检测**：主旋律复现必须落到一个具体的知识节点（有史料/数据支撑），或落到读者画像中标注的当下具体问题（有 relatable 场景），否则标记为"空洞"。

---

## 阶段四：对抗评审——质量关卡

### 4.1 五个对抗 Agent

发生在编排后、渲染前。每个 Agent 的 Prompt/规则必须注入史观包、读者画像和审美标准——"不是自由的批评家，而是戴着镣铐的考官"。

```yaml
adversarial_agents:
  - id: "historiography_auditor"
    role: "史观一致性审查员"
    attack_angles:
      - "检测 forbidden_keywords 使用"
      - "检测立场漂移（individual_agency 权重超标、情绪基调不一致）"
      - "检测价值关键词误用"
    severity: error

  - id: "reader_advocate"
    role: "目标读者代言人"
    attack_angles:
      - "检测知识门槛过高（超出 reader_persona.unknown）"
      - "检测类比失效（来源域不属于 prefers_analogy_from）"
      - "检测情感错位（不匹配 resonates_with）"
      - "检测抵触触发（触及 resistance_map.triggers）"
    severity: error/warning

  - id: "narrative_critic"
    role: "叙事结构审稿人"
    attack_angles:
      - "检测张力曲线不合理（连续下降无标记）"
      - "检测高潮不唯一或多高潮冲突"
      - "检测高潮疲软（不够慢/不够重/不是结构跃升）"
      - "检测悬念造假（使用人工制造的假悬念）"
      - "检测呼吸段缺失"
    severity: warning

  - id: "integrity_guardian"
    role: "历史真实性与冲击力质量审查员"
    attack_angles:
      - "检测 precision_data 缺少 source 标注"
      - "检测 superlative 滥用（'史上最'等）"
      - "检测主旋律空洞（不落在具体知识点或读者问题）"
      - "检测争议史实未标注条件限定"
    severity: error/warning

  - id: "perspective_challenger"
    role: "叙事视角/选材偏见审查员"
    attack_angles:
      - "检测视角单一（全章只有皇帝大臣，无底层）"
      - "检测翻案过度（完全忽视反方史料）"
      - "检测史观包框架下仍属过度的表述"
    severity: warning
```

### 4.2 评审输出格式

```json
{
  "review_result": {
    "passed": false,
    "reviewer": "ReaderAdvocate_v1",
    "issues": [
      {
        "dimension": "emotional_resonance",
        "severity": "medium",
        "location": "sec_02.deep_dive.actor_unit",
        "issue": "将崇祯焦虑类比为'CEO的KPI压力'，但目标读者更可能对'无权无钱的中层管理者'产生共鸣",
        "suggestion": "将类比对象从CEO调整为'部门总监'，增加对执行层无力感的描写",
        "auto_fixable": true
      }
    ],
    "overall_comment": "结构完整，但情感连接点偏高，未击中核心读者群的真实痛点"
  }
}
```

### 4.3 对抗强度等级

| 等级 | 说明 | 参与 Agent | 通过规则 |
|------|------|-----------|----------|
| 轻度 | 草稿自检，仅规则对抗 | 规则引擎（关键词/张力曲线等） | 标记警告允许继续 |
| 中度 | 内部打磨 | 规则 + 史观审计员 + 读者代言人（LLM对抗） | 返回修改建议需人工确认 |
| 重度 | 出版前终审 | 全部5个Agent | 不通过阻断渲染 |

---

## 阶段五：受控生成——LLM 填槽

### 5.1 填槽哲学

LLM 不是在创作，而是在填槽。每个模板单元被拆解为明确的 fill_slots JSON Schema，LLM 只能在指定槽位内输出受约束文本。

**关键禁止**：
- 不能修改模板结构
- 不能增删单元
- 不能跨过模板的角色和标签约束
- 不能使用 forbidden 词表中的词汇

### 5.2 四层注入引擎

```
Layer 1 史观注入 → system_prompt
  ├─ 注入 HP.stance_vector 描述
  ├─ 注入 HP.forbidden 到 negative_constraints
  ├─ 注入 HP.emotional_tone 到 tone_guidance
  └─ 注入 HP.emotion_injection 规则

Layer 2 读者连接点注入 → cognitive_bridge_slot + emotional_bridge_slot
  ├─ 认知桥：在 analogy_pool 中搜索 source_domain 匹配的类比
  └─ 情感桥：匹配节点 emotional_tone 与 reader_persona.resonates_with

Layer 3 文风包注入 → fill_instruction + post_generation_filter
  ├─ Layer 0 Meta → system_prompt
  ├─ Layer 1 Persona → 角色设定
  ├─ Layer 2 Lexical Pool → 随机选连接词 + 输出后禁词硬过滤
  ├─ Layer 3 Syntactic Bias → 输出后统计校验
  ├─ Layer 4 Rhetorical Ops → Prompt 约束
  └─ Layer 5 Layout/Pacing → 模板默认值

Layer 4 冲击力与主旋律注入 → specific_slots
  ├─ impact_strike 槽位：从 impact_potential 读取 + 按 position 格式化
  └─ motif_variation 槽位：按 variation_type 生成不同变奏
```

### 5.3 输出后校验

```yaml
post_generation_checks:
  - check: "forbidden_keywords_hit"
    action: "自动替换 → 重新校验 → 如果仍命中则阻断"
  - check: "style_deviation (JS散度 < 0.15)"
    action: "偏离 > 0.15 则降低文风包自由度（从随机选改为强制 Top-1）"
  - check: "slot_length_compliance"
    action: "截断至 max_chars（保留完整句子边界）"
  - check: "tension_consistency"
    action: "标记不匹配的单元供对抗评审关注"
```

### 5.4 LLM 标准化调用接口

```yaml
llm_call:
  endpoint: "/generate/fill_slot"
  request: {
    unit_template: object,        # 当前模板单元的 JSON Schema
    slot_content: object,         # 已填充的槽位
    knowledge_context: {
      node: knowledge_node,
      adjacent_nodes: [node],
      series_profile: object
    },
    style_pack: object,           # 完整文风包
    constraints: {
      forbidden_keywords: [string],
      tone: string,
      max_chars_per_slot: object
    },
    tension_context: {
      current_tension: float,
      hook_requirements: [string]
    }
  }
  response: {
    filled_units: [unit_id → filled_text],
    confidence_scores: [unit_id → float],
    warnings: [string]
  }
```

模型切换后需执行回归测试（句长分布/JS散度/forbidden 命中数/情绪词比例），偏离阈值则微调 Prompt 模板。

---

## 阶段六：多模态输出

### 6.1 SSML 音频脚本生成规则

```yaml
ssml_generation:
  narrative_hook: "<prosody rate='fast'>hook_text</prosody>"
  dramatic_irony: "<prosody rate='slow' volume='soft'>text</prosody>"
  structural_reveal: "<break time='800ms'/><prosody rate='x-slow' pitch='low'><emphasis level='strong'>text</emphasis></prosody><break time='600ms'/>"
  reflective_close: "<prosody rate='medium'>text</prosody><break time='1000ms'/>"
  impact_strike: "<break time='500ms'/><prosody rate='x-slow'>data_text</prosody><break time='800ms'/>"
  motif_epigram: "<break time='600ms'/><prosody rate='slow' volume='loud'><emphasis level='moderate'>epigram_text</emphasis></prosody><break time='1200ms'/>"
```

### 6.2 动画分镜标签生成规则

```yaml
template_to_animation:
  TPL_01:
    - "context_unit → static_scene（历史背景图）"
    - "event_unit → timeline_zoom_in（聚焦具体文档/事件）"
    - "structure_unit → institutional_structure_diagram（制度结构分层展开）"
    - "impact_strike → data_pulse（数字突然显现放大，配震撼音效标记）"
  TPL_09:
    - "context_unit → slow_pan_across_map（地图缓慢平移）"
    - "analysis_unit → timeline_with_data_curve（时间轴+数据曲线缓慢爬升）"
    - "event_unit → crisis_icon_flash（临界点图标快速闪烁）"
    - "structure_unit → full_system_collapse_visual（全景崩塌可视化）"
```

---

## 阶段七：系列品牌管理

### 7.1 多系列 IP 隔离与复用

```yaml
multi_series_rules:
  isolation:
    - "每个 Series 拥有独立的配置数据库"
    - "Series Profile 之间全部字段互不继承"
    - "一个系列的模板偏好/禁用项不影响另一个"
  
  sharing:
    - "通用知识节点可跨系列共享"
    - "文风包可跨系列引用（但每个系列可锁定 custom forbidden 项）"
    - "读者画像可跨系列复用"
  
  conflict_detection:
    - "同一个机构运营的多个系列需在同一年发布时，自动检查风格相似度"
    - "相似度度量：JS 散度计算 Lexical Pool 分布差异"
    - "JS 散度 < 0.2 触发品牌稀释警告"
    - "JS 散度 < 0.1 阻断生成（除非人工确认差异化路径）"
  
  mitigation_suggestions:
    - "为系列 B 更换 primary motif"
    - "为系列 B 调整模板角色偏好"
    - "为系列 B 设置不同的冲击力政策"
```

### 7.2 系列一致性校验

```yaml
series_consistency_check:
  - check: "motif_present_and_varied_in_chapter"
    desc: "主旋律在本章出现并完成至少3次变奏"
  - check: "style_pack_deviation_within_limit"
    desc: "文风包偏离度在 ±0.05 内（JS散度）"
  - check: "forbidden_template_not_used"
    desc: "未使用系列禁用模板"
  - check: "contemporary_echo_in_reflection"
    desc: "章末反思单元包含当代映射"
  - check: "impact_policy_compliant"
    desc: "冲击力遵守系列政策（max_sensationalism 等）"
```

---

## 附录

### A. 质量度量体系

| 指标 | 目标值 | 检测阶段 |
|------|--------|----------|
| 模板合规率 | ≥98% | 生成后校验 |
| 张力曲线通过率 | ≥95% | 编排后对抗 |
| 史观一致性通过率 | 0 error + ≤3 warning/章 | 对抗评审 |
| 读者连接点覆盖率 | 100% | 生成后校验 |
| 冲击力合规率 | 100% | 对抗评审 |
| 主旋律复现完成度 | ≥3次/章 + 当代映射 | 编排后校验 |
| 钩子系统覆盖率 | 100%（每章≥2钩子+中间≥1） | 编排后校验 |
| 人为干预占比 | 稳态≤15% | 月度统计 |

### B. 实施路线图

| Phase | 周期 | 核心任务 | 交付物 |
|-------|------|----------|--------|
| 1 MVP | 3-4个月 | 模板Schema/COG引擎/单文风包/最小知识库/模板选择器三层漏斗/LLM填槽接口 | 2-3个完整章节 |
| 2 叙事工程 | 3-4个月 | 史观包/读者画像/选材引擎/PDL/冲击力注入/主旋律记忆 | 完整作品草稿(8-12万字) |
| 3 质量品牌 | 2-3个月 | 5对抗Agent/Series Profile/系列一致性校验/多模态输出/文风包逆向工具 | 终稿+音频+动画+交付包 |
| 4 平台化 | 持续 | 多系列IP管理/SDK/跨领域扩展/协作工作流 | SaaS平台 |

### C. 关键异常处理

| 异常 | 处理方式 |
|------|----------|
| 选材候选为空 | 逐层放宽约束 → 通知编辑手动选择 |
| 模板候选为空 | 移除 forbidden_tags → 放宽 min_scale → 回退 default 模板 |
| 依赖冲突 | 自动插入 bridge section 或被依赖节点前置 |
| LLM 填槽格式错误 | 重试2次 → 使用模板 fallback 文本 |
| 对抗评审3+ error | 阻断生成，汇总报告发送编辑 |

---

*文档版本：V3.0 | 最后更新：2026-07-10 | 源文档：基于19轮深度对话 + 设计需求文档 + 平台构建素材全集*
