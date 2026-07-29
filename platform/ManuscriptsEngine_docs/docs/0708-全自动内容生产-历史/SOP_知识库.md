好，我已经通读了整个目录中所有文档——从最初的 V2.0 方法论，到历史通俗作品专项设计，再到 19 轮逐步深化的全部讨论。现在我来做完整的提炼。

---

# 通俗历史长文本作品 · 业务流 SOP 与知识库设计

---

## 一、总纲：核心理念

> **将专家经验规则化、内容结构模板化、表现力参数化，把大模型从"创作者"降级为"受控执行器"。模型只做选择题（选模板、填槽位），不做作文题（自由创作）。**

这与教材撰写的本质区别在于：

| | 教材 | 历史通俗作品 |
|---|---|---|
| 驱动方式 | 大纲驱动（知识点全集固定） | **目标驱动**（选材有自由度，需主动"挑戏"） |
| 立场 | 追求共识性正确 | **有立场的共鸣**（史观参数化） |
| 读者 | 按年级预设前置知识 | **动态寻找读者连接点**（认知桥+情感桥） |
| 叙事 | 逻辑清晰即可 | **必须全程无尿点**（心理动力学编排） |
| 品牌 | 教材品牌靠出版社背书 | **风格即品牌**（系列 Profile 驱动） |

---

## 二、业务流 SOP（完整生产流水线）

### 阶段零：冷启动 · 定义"审美标准"（一次性重投入）

**这一阶段是最核心的投资——把"好作品"的隐性标准变成显式配置。**

#### 0.1 定义 Series Profile（系列品牌 DNA）

```
系列品牌圣经（Brand Bible）包含：
├─ 共享史观包（立场、情绪基调、价值关键词）
├─ 共享主旋律（Motif）——如"一切宏大叙事的崩塌，始于技术治理的缺位"
├─ 共享文风包（锁定用词、句式、修辞，禁止煽情/英雄叙事）
├─ 模板角色偏好（主力模板/辅助模板/禁用模板）
├─ 冲击力政策（反常识数据要求、最大耸动度、事实完整性硬约束）
├─ 读者基调
└─ 品牌标识（跨模态签名：封面意象、音频固定开场白）
```

#### 0.2 建设五大生产资料库

| 资料库 | 历史版内容 |
|---|---|
| **统一标签体系** | 叙事类型标签（`#micro_event` `#decision_point` `#turning_point`）、分析类型（`#institutional_analysis` `#structural_explanation`）、人物维度（`#idealistic_actor` `#ordinary_people`）、史学立场（`#materialist` `#structural`）、知识类型（`#concept_intro` `#analogy`）、冲击力标签（`#counter_intuitive` `#precision_data`） |
| **叙事模板库** | TPL-01～TPL-10（小事撬动大局/命运抉择时刻/制度杀人/文明碰撞/技术改变社会/观念诞生记/被遗忘的多数/历史反转/长时段缓慢变化/复调历史） |
| **领域知识库** | 事件+人物+制度+观念四元组知识节点，含选材加权字段（significance/dramatic_potential/source_quality/narrative_fit_tags/impact_potential）和依赖关系（时间线/因果/前置知识） |
| **文风包库** | 黄仁宇式（冷静制度分析+微妙反讽）、通俗演义式（口语化+戏剧化）、费曼式（亲和+设问）——五层形式化（Meta/Persona/Lexical Pool/Syntactic Bias/Rhetorical Ops/Layout-Pacing） |
| **张力/情绪模板库** | `narrative_hook` `dramatic_irony` `structural_reveal` `reflective_close` 及与文风包/Layout 的联动映射 |

#### 0.3 定义史观参数包（Historiography Profile）

| 维度 | 示例（结构唯物主义） |
|---|---|
| **立场向量** | individual_agency=-0.3, structural_determinism=0.8, moral_judgment=-0.7, great_man_theory=-0.8 |
| **情绪基调** | default: sober_detached, toward_power: skeptical, toward_vulnerable: empathetic_but_not_sentimental |
| **价值关键词** | approved: [制度困境, 结构性矛盾, 技术治理], forbidden: [昏庸, 奸佞, 圣明, 天意] |
| **模板偏好** | TPL-01 +0.2, TPL-03 +0.2, TPL-02 -0.3 |
| **主旋律（Motif）** | "缺乏技术治理的道德教化，终将沦为系统性谎言" |

#### 0.4 定义读者画像（Reader Persona）

| 维度 | 示例（职业倦怠白领） |
|---|---|
| **认知基线** | solid=[鸦片战争, 辛亥革命], fuzzy=[一条鞭法, 军机处], unknown=[明代财政技术细节] |
| **认知桥梁域** | prefers_analogy_from=[corporate_structure, office_politics, project_management] |
| **情感原型** | primary=ambitious_but_trapped_professional, resonates_with=[systemic_frustration, career_ceiling] |
| **阻抗地图** | triggers=[道德说教, 宏大空话, 纯军事细节] |
| **语言亲和度** | preferred_register=semi_formal_with_colloquial_touch |

---

### 阶段一：选材 · 决定"讲什么"

#### 1.1 确定叙事意图（Narrative Intent）

六种意图供选择：`INTENT_EPIC`（宏大叙事） / `INTENT_MICRO`（微观史） / `INTENT_TRAGEDY`（制度悲剧） / `INTENT_REVISION`（翻案修正） / `INTENT_PERSONAL`（人物传记） / `INTENT_IDEATIONAL`（观念史）

#### 1.2 选材引擎评分

```
SelectionScore = α·IntentFit + β·DramaticPotential + γ·SourceQuality + δ·ReaderResonance + ε·HistoriographyBias
```

#### 1.3 选材约束

- 覆盖均衡：至少一个微事件 + 一个结构解释
- 时间顺序：除非 flashback 标记，节点按时间升序
- 戏剧密度上限：连续>2个高戏剧性节点需插入缓和节点
- 来源最低要求：每个选定事件须有≥1一手史料

#### 1.4 编辑干预接口

手工调权（boost）、锁定必选（pinned）、排除节点（excluded）、微调五项权重系数——把"选材品味"参数化。

---

### 阶段二：编排 · 决定"怎么讲"

#### 2.1 模板选择器（3层漏斗）

```
Layer 1 硬性过滤：required_labels / forbidden_labels / min_scale 淘汰不匹配模板
Layer 2 加权评分：TemplateScore = 0.4·LabelOverlap + 0.25·StructuralFit + 0.2·NarrativePotential + 0.1·SourceRichness + 0.05·HistoriographyMatch
Layer 3 语境修正：章节位置（开篇/中间/转折/结尾）、前后文去重（连续两节相同模板-0.15）、史观参数修正
```

#### 2.2 章节编排语法（COG）

**6种章节角色** + **10×6角色亲和度矩阵**（每个模板在各角色上的 0-3分）：

| 角色 | 说明 | 常配模板（3分首选） |
|---|---|---|
| anchor_event | 锚定事件，章节叙事起点 | TPL-01, TPL-02 |
| deep_dive | 深入制度/心理内部 | TPL-03, TPL-05, TPL-06 |
| counterpoint | 提供对立/修正视角 | TPL-08, TPL-10, TPL-07 |
| macro_frame | 提供长时段/结构框架 | TPL-04, TPL-09, TPL-05 |
| synthesis | 综合前文，升华主题 | TPL-06 |
| bridge | 承上启下 | TPL-07, TPL-01 |

**4种经典编排模式**：
- Pattern A（微观→修正→宏观）：anchor_event → counterpoint → macro_frame
- Pattern B（抉择→毁灭→反思）：anchor_event → deep_dive → synthesis
- Pattern C（碰撞→变革→复调）：macro_frame → deep_dive → counterpoint
- Pattern D（追更型）：anchor_event → deep_dive → counterpoint → macro_frame

#### 2.3 心理动力学编排（PDL）

**6大要素注入**：

| 要素 | 设计 | 示例 |
|---|---|---|
| **悬念（认知落差）** | 读者知结局，人物不知 | "此时的申时行并不知道，这封奏折将在十七年后成为萨尔浒之战的注脚" |
| **张力阶梯** | tension_level 0.3→0.6→0.9，逐级加码 | 从行政问题→制度反弹→系统性崩溃 |
| **高潮设计** | 唯一高潮、结构跃升单元、慢速沉重 | "这薄薄一页纸，是整个大明财政技术破产的清算单" |
| **节奏呼吸** | 高密度分析后必须插入低密度人文段落 | TPL-03（高）后 → TPL-07（低） |
| **冲击力注入** | 反常识精确数据在穴位释放 | "国库仅剩白银2300两——尚不足皇室一日脂膏" |
| **主旋律复现** | 每章开篇/高潮/结尾变奏出现核心命题 | "历史从不重复，但缺乏技术底座的宏大叙事，总会以相似的方式塌方" |

**6大钩子槽位**：开篇悬念钩 / 认知落差钩 / 矛盾钩 / 信息差钩 / 高潮钩 / 结尾钩（每章标配首+尾钩，除末章外结尾钩必含foreshadowing）

---

### 阶段三：质检 · 对抗评审

#### 3.1 五维对抗 Agent

发生在编排后、渲染前。每个 Agent 也受审美约束（注入史观包+读者画像+审美标准）。

| Agent | 攻击目标 | 典型攻击角度 |
|---|---|---|
| **Historiography Auditor** | 史观一致性 | 检测 forbidden_keywords、立场漂移、情绪基调不一致 |
| **Reader Advocate** | 读者共鸣 | 类比失效、情感错位、知识门槛过高 |
| **Narrative Critic** | 叙事质量 | 悬念造假、张力虚假、高潮疲软 |
| **Integrity Guardian** | 真实性与冲击力 | 数据失真、标题党化、主旋律空洞 |
| **Perspective Challenger** | 选材偏见 | 视角单一、翻案过度忽视对立史料 |

#### 3.2 对抗评审输出

结构化评审报告：passed 状态、issues 数组（dimension/severity/location/issue/suggestion/auto_fixable）

#### 3.3 对抗强度等级

轻度（规则对抗，标记警告） → 中度（LLM 对抗，返回修改建议） → 重度（全部五 Agent，不通过阻断渲染）

---

### 阶段四：受控生成 · LLM 填槽

#### 4.1 填槽模式

每个模板单元被拆解为明确的 fill_slots JSON Schema，LLM 只能在指定槽位内输出受约束文本，不能修改模板结构、增删单元。

#### 4.2 四层注入顺序

```
史观包（立场约束 + 禁用词 + 情绪基调）
  → 读者连接点（认知桥 + 情感桥自动挖掘）
    → 文风包（连接词随机选 + 句式约束 + 禁词硬过滤）
      → 冲击力数据 + 主旋律变奏填入
```

#### 4.3 多模态派生

- 结构化 Markdown 书稿（含知识卡片/类比框/时间轴/史料引用块）
- 一键文风包切换 → 大众版 / 学术版 / 公众号版
- SSML 音频脚本（基于情绪弧线标签自动生成语音标记）
- 动画分镜标签（基于模板自动标注需求 + 时间戳 + 图形元素 + 情绪同步标记）

---

## 三、知识库设计（结构化完整规格）

### 3.1 知识节点数据结构

四种节点类型：`event`（事件） / `actor`（人物） / `institution`（制度） / `concept`（观念）

**核心字段**：

```
knowledge_node:
  node_id, node_type, date/time_range, summary
  labels: content / actor / structure / scale / narrative_potential / historiography
  actors: [name, traits, dilemma]
  context: institutional / long_term_causality / related_events / related_concepts
  relations: precedes / part_of / contradicts / compares_with / depends_on
  narrative_hooks: [string]
  structural_insights: [string]
  common_misconceptions: [string]
  analogy_pool: [{id, suitable_for}]
  default_style_pack, default_tension_arc

  # ---- 选材加权字段 ----
  significance: {political, economic, cultural, personal_agency, symbolic_power}  各0-1
  dramatic_potential: {has_dramatic_irony, has_moral_dilemma, score}
  source_quality: {primary_sources, reliability, contemporary}
  narrative_fit_tags: [INTENT_TRAGEDY, INTENT_MICRO, ...]
  typical_reader_resonance: {persona_id → 0-1}

  # ---- 冲击力字段 ----
  impact_potential: {
    counter_intuitive_score,       # 0-1
    precision_data: {value, context, source},
    emotional_valence,             # shock/despair/awe/irony
    memorable_phrase_seed
  }
```

### 3.2 三种依赖关系

| 依赖类型 | 检查规则 |
|---|---|
| **时间线依赖** | 事件按时间升序，除非 flashback 标记 |
| **因果关系依赖** | 事件 A 是事件 B 的前提，自动校验 |
| **前置知识依赖** | 概念 A 必须在概念 B 之前介绍（如先讲明代内阁制度，再讲票拟/批红流程）|

### 3.3 冲击力数据资产

由领域专家在入库时标注：反常识评分（0-1） + 精确数据（数字+对比语境+史料出处） + 情绪效价（枚举值） + 可记忆短语种子

---

## 四、SOP 总览图（一页）

```
┌─ 冷启动 ───────────────────────────────────┐
│ Series Profile | 史观包 | 读者画像 │
│ 标签体系 | 10 模板 | 文风包 | 张力模板 │
│ ← 一次投入，定义"审美标准" │
└─────────────────┬──────────────────────────┘
                  ↓
┌─ 选材引擎 ──────────────────────────────────┐
│ INTENT → 评分 → 约束过滤 → 编辑干预 │
│ ← 目标驱动，决定"讲什么" │
└─────────────────┬──────────────────────────┘
                  ↓
┌─ 编排（COG + PDL）─────────────────────────┐
│ 模板选择器 → 角色指派 → 悬念/张力/高潮 │
│ 冲击力注入 → 主旋律复现 → 钩子系统 │
│ ← 决定"怎么讲" │
└─────────────────┬──────────────────────────┘
                  ↓
┌─ 对抗评审 ──────────────────────────────────┐
│ 史观审计员 | 读者代言人 | 叙事评论家 │
│ 真实性守护者 | 视角挑战者 │
│ ← 质量关卡，倒逼内容韧性 │
└─────────────────┬──────────────────────────┘
                  ↓
...(truncated)...

好的，之前的总结侧重于**整体框架**，现在来补全SOP中尚未展开的**可执行细节层**——包括每个模板的填槽Schema、对抗Agent的Prompt模板、校验规则的具体实现、多模态输出生成规则，以及人工干预工作流。

---

# 通俗历史长文本 · 业务流 SOP（完整体）

## 接续：阶段二 · 编排（续）

### 2.4 过渡规则（Transition Rules）——模板间衔接规范

模板之间不能直接拼接，必须有**过渡单元**。每种过渡类型有其 marker 文本模板和张力变化方向。

```yaml
# 四种过渡类型完整定义
transition_types:
  cognitive_contrast:
    marker_pool: ["然而新证据表明——", "但事实远比常识复杂。", "若深入审视，却会发现另一番图景。"]
    tension_shift: increase        # 张力上升
    required_tags: ["#revisionist_evidence"]
    example: "然而，将帝国停滞归咎于皇帝怠政，是一种危险的简化。"

  temporal_expansion:
    marker_pool: ["若将镜头拉远至整个世纪……", "把时间轴向前推两百年……", "这一困境的种子，早在更早的时代便已埋下。"]
    tension_shift: scale_up        # 尺度放大
    time_jump: true
    example: "若将镜头拉回两个世纪，我们会发现这一困境的种子早已埋下。"

  psychological_deepening:
    marker_pool: ["在做出这一决定时，他内心并非毫无波澜。", "只有走进他的书房，才能理解那份焦灼。", "深夜的烛火下，他独自面对着一个无解的选择。"]
    tension_shift: intensify
    example: "在写下这道谕旨时，崇祯的笔尖在'朕'字上停顿了三次。"

  structural_leap:
    marker_pool: ["这并非孤例，而是整个系统的缩影。", "这一事件，暴露的是一个时代的结构性盲区。", "从个体的困境，我们看到的是制度的困境。"]
    tension_shift: abstract_up     # 抽象层次上升
    example: "这并非一个人的失败，而是一个系统的宿命。"

# 过渡校验规则
transition_validation:
  - rule: "temporal_expansion 要求 to_tpl.scale > from_tpl.scale"
  - rule: "cognitive_contrast 要求前后标签存在冲突"
  - rule: "structural_leap 要求 to_tpl.has_tag('#macro_causality')"
  - rule: "心理深化后必须跟随 tension_shift 向上的单元（不能深化后立即降低）"
```

### 2.5 PDL 标记全表（每个模板的钩子/张力/高潮点位）

| 模板 | 钩子类型 | 张力节点 | 高潮单元 | 冲击力投放点 | 主旋律变奏位 |
|---|---|---|---|---|---|
| TPL-01 | 开篇悬念钩 + 认知落差钩 + 结尾钩 | 情境→事件 | structure_unit（慢速沉重） | 结构单元反常识数据 | context_unit（陈述）、structure（论断）、reflection（警句） |
| TPL-02 | 矛盾钩 + 高潮钩 | 人物→事件（压力递增） | event_unit（决策瞬间慢镜头） | 决策代价数据（如"这一决定牺牲了X万兵力"） | actor（内心冲突）、reflection（教训） |
| TPL-03 | 认知落差钩 + 悲剧钩 | 人物→事件→结构（层层压迫） | consequence_unit（毁灭时刻，简短克制） | 后果数据（如"清洗涉及X官员"） | context（制度介绍）、reflection（永恒张力） |
| TPL-04 | 开篇悬念钩 + 信息差钩 | 情境A→情境B（差异扩大） | analysis_unit（差异的核心机制揭示） | 对比数据（如"一方生铁产量是另一方的X倍"） | analysis（对比框架）、reflection（进步定义） |
| TPL-05 | 矛盾钩 + 反思钩 | 情境→事件（技术冲击） | structure_unit（社会重组必然后果） | 技术改变生活的具体数据 | analysis（技术中性反思）、reflection（当代映射） |
| TPL-06 | 信息差钩 + 认知落差钩 | 情境→人物（旧观念危机） | analysis_unit（新观念核心逻辑揭示） | 关键文本/论战引文数据 | idea_unit（核心逻辑）、reflection（滞后效应） |
| TPL-07 | 安静钩（低姿态） + 反思钩 | 情境→事件（常态被打断） | analysis_unit（结构对个体的塑造） | 日常生活的量化数据（如"年收入仅X两"） | reflection（历史书写盲区） |
| TPL-08 | 认知落差钩 + 反转钩 | 情境→事件（常识→新证据） | analysis_unit→structure_unit（认知翻转） | 新数据引爆反转 | event（新证据）、reflection（书写主观性） |
| TPL-09 | 宏大钩 + 宿命钩 | 情境→分析（缓慢积累） | structure_unit（临界点揭示，最沉重） | 长周期数据（如"两百年间土地兼并率从X%到Y%"） | analysis（积累指标）、reflection（深海暗流） |
| TPL-10 | 平衡钩 + 开放钩 | 人物A↔人物B（视角切换） | analysis_unit（结构性矛盾超越个人意志） | 冲突双方伤亡/成本对比数据 | actor_A（立场）、actor_B（立场）、reflection（无单一真相） |

---

## 阶段二补充：钩子系统完整规则

### 钩子投放引擎规则

```yaml
hook_engine:
  # 每章标配
  minimum_hooks:
    - type: "opening"        # 开篇钩（必选）
    - type: "ending"         # 结尾钩（必选，除最后一章外必须包含foreshadowing）
  
  # 中间可选钩（至少选1个）
  optional_hooks:
    - type: "dramatic_irony"   # 认知落差钩（读者知结局，人物不知）
    - type: "conflict"         # 矛盾钩（矛盾升级点）
    - type: "info_gap"         # 信息差钩（制造"后文会揭示"的期待）
    - type: "climax"           # 高潮钩（结构跃升前的屏息时刻）
  
  # 钩子位置规则
  placement_rules:
    - "开篇钩必须在 chapter 的前 5% 篇幅内"
    - "认知落差钩必须紧跟在 context_unit 或情境描述后"
    - "矛盾钩必须卡在 tension_level 从 low→mid 的拐点上"
    - "高潮钩必须在 structure_unit 或 climax_unit 的前一节末尾"
    - "结尾钩必须在最后一段，且不与章节末端超过 3 句"
  
  # 结尾钩的特殊规则
  ending_hook_rules:
    - "除最后一章外，所有章节必须有结尾钩"
    - "结尾钩类型必须为 foreshadowing（指向下一章）或 contemporary_echo（指向当下）"
    - "结尾钩的情绪基调必须与史观包 emotional_tone 一致"
    - "结尾钩禁止使用 trivial 悬念（如'预知后事如何，请听下回分解'）"
  
  # 钩子质量校验
  quality_checks:
    - "开篇钩能否在3秒内引发好奇心？如果不，标记weak"
    - "认知落差钩是否真的利用了读者后见之明？"
    - "结尾钩是否与史观包情绪基调冲突？"
    - "结尾钩是否为空洞的'历史告诉我们'式说教？"
```

---

## 阶段二补充：冲击力注入规则（完整版）

### 投放位置与格式规则

```yaml
impact_injection:
  # 四类投放位置
  positions:
    - name: "opening_hook"
      condition: "节点 impact_potential.counter_intuitive_score > 0.7"
      format: "raw_data + contrast_context"
      example: "当李自成军队攻入北京时，他们发现国库里只剩2300两白银——还不够给每位士兵发一枚铜钱。"
      refrain: "禁止使用'令人震惊'等元描述词，让数据本身说话"
    
    - name: "conflict_escalation"
      condition: "tension_level 处于 0.4→0.7 上升阶段"
      format: "precision_data（数字+来源）"
      example: "据《明实录·崇祯朝》记载，京营士兵已连续七个月未领到饷银，逃亡率达六成。"
      source_annotation: required  # 必须标注出处
    
    - name: "pre_climax_silence"
      condition: "在 is_chapter_climax=true 的单元之前一个单元末尾"
      format: "极简数据，打断抒情，制造窒息感"
      example: "崇祯在谕旨中写下的最后一个数字是：2300。"
      pacing: "单句成段，前后空行，制造视觉停顿"
    
    - name: "ending_hook"
      condition: "结尾钩类型为 contemporary_echo"
      format: "precision_data 指向当下的映射"
      example: "2300两白银——这大约相当于今天一个县级政府三个月的办公经费。历史从不重复，但数字会说话。"
  
  # 硬约束
  hard_constraints:
    - "require_primary_source: true  # 所有精确数据必须标注史料出处"
    - "forbid_superlative_distortion: true  # 禁止'史上最……'式夸张"
    - "forbid_emotional_amplifier: true     # 禁止'令人震惊''难以置信'等元描述"
    - "source_context_required: true        # 数据必须有上下文对比"
    - "severity: error  # 违反即阻断生成"
```

---

## 阶段三：对抗评审（完整 implementation 规格）

### 3.4 五个 Agent 的 Prompt/规则模板

#### Agent 1: Historiography Auditor（史观审计员）

```yaml
agent:
  id: "historiography_auditor_v1"
  role: "史观一致性审查员"
  
  # 注入的上下文（每次评审传入）
  injected_context:
    - historiography_profile（当前使用的史观参数包完整配置）
    - series_profile.series_id
  
  # 评审规则
  review_rules:
    # 规则1：检查禁用词
    - check: "text_contains_any(HP.value_keywords.forbidden)"
      severity: error
      action: "阻断，标记具体违禁词及位置"
    
    # 规则2：检查 discouraged 词使用频率
    - check: "freq_of(HP.value_keywords.discouraged) > threshold(3_per_10000_words)"
      severity: warning
      action: "标记警告，建议替换"
    
    # 规则3：检查情绪基调漂移
    - check: "emotional_tone_deviation(HP.emotional_tone.default) > threshold(0.3)"
      severity: warning
      action: "标记漂移段落，指出当前 tone 与目标 tone 的差异"
    
    # 规则4：检查立场向量一致性
    - check: "stance_vector_violation_detected()"
      description: "如果文本中存在明显违背 HP.stance_vector 的表述"
      example: "HP 设置 individual_agency=-0.3，但文本将历史进程完全归因于个人品德 → 违规"
      severity: error
      action: "阻断，标记违规段落并提供修改方向"
  
  # 输出格式
  output_schema:
    passed: boolean
    issues:
      - dimension: string
        severity: "error" | "warning"
        location: string（精确到单元）
        issue: string
        suggestion: string
        auto_fixable: boolean
    overall_comment: string
```

#### Agent 2: Reader Advocate（读者代言人）

```yaml
agent:
  id: "reader_advocate_v1"
  role: "目标读者代言人"
  
  injected_context:
    - reader_persona（完整画像）
    - target_chapter_id
  
  review_rules:
    # 规则1：检查知识门槛
    - check: "knowledge_gate_assessment()"
      description: "文本中使用的概念是否超出 reader_persona.knowledge_assumptions.unknown"
      severity: error
      action: "标记超纲概念，要求插入 cognitive_bridge"
    
    # 规则2：检查类比有效性
    - check: "analogy_effectiveness()"
      description: "类比是否来自读者偏好的 domain（prefers_analogy_from），是否牵强"
      severity: warning
      action: "标记失效类比，建议替换为更贴近读者经验的类比"
    
    # 规则3：检查情感连接
    - check: "emotional_resonance_check()"
      description: "情感桥接是否真实触达 reader_persona.emotional_archetype.resonates_with"
      severity: warning
      action: "标记错位情感连接，建议调整方向"
    
    # 规则4：检查排斥标签
    - check: "repelled_by_detection()"
      description: "是否有被 reader_persona.emotional_archetype.repelled_by 标记的内容类型"
      severity: error
      action: "阻断，标记具体触发内容"

    # 规则5：检查阻抗触发
    - check: "resistance_map_check()"
      description: "是否触发了 reader_persona.resistance_map.triggers"
      severity: warning
      action: "标记触发位置，提示修改策略"
```

#### Agent 3: Narrative Critic（叙事评论家）

```yaml
agent:
  id: "narrative_critic_v1"
  role: "叙事结构/编剧审稿人"

  injected_context:
    - tension_profile（当前章节的张力曲线数据）
    - chapter_archetype（编排模式类型）

  review_rules:
    # 规则1：检查张力曲线合理性
    - check: "tension_curve_validity()"
      description: "tension_level 是否在章节中呈现合理的上升/保持/呼吸模式"
      severity: warning
      exceptions: "pattern_b_tragedy 的结尾可低于中间峰值（悲剧回响）"
      action: "标记异常点，给出调整建议"
    
    # 规则2：检查高潮唯一性
    - check: "climax_uniqueness()"
      description: "is_chapter_climax=true 的单元是否唯一"
      severity: error

...(truncated)...

之前的输出在**文风包逆向工程SOP**处被截断。以下继续补完剩余的工程规格。

---

# SOP 补完（接续）

## 附录二：读者连接点自动挖掘引擎（完整算法）

这是体系中实现"为不同读者找到共鸣"的核心模块，需要比前述更细的工程规格。

### 认知桥（Cognitive Bridge）挖掘算法

```yaml
cognitive_bridge_engine:
  # 输入
  inputs:
    - knowledge_node: 当前填槽的知识节点
    - reader_persona: 目标读者画像
    - analogy_pool: 知识节点中标注的类比池
  
  # 算法
  algorithm:
    step_1: "判断是否需要认知桥"
      condition: "node 涉及的概念在 reader_persona.knowledge_assumptions 中属于 unknown 或 fuzzy"
      if_not_needed: "跳过，标记桥接槽位为 optional"
    
    step_2: "在 analogy_pool 中筛选目标域"
      filter: "analogy.source_domain IN reader_persona.cognitive_style.prefers_analogy_from"
      if_empty: "在通用类比池中搜索（fallback 到 daily_life domain）"
    
    step_3: "类比质量评分"
      scoring:
        - "source_domain_fitness: 读者偏好域匹配度（精确匹配=1.0，相关域=0.5，不匹配=0）"
        - "conceptual_accuracy: 类比与概念核心的对应精度（防止过度简化）"
        - "narrative_fit: 类比在当前 tension 下的风格适合度（高潮不适合轻佻类比）"
      formula: "AnalogyScore = 0.5×domain_fitness + 0.3×accuracy + 0.2×narrative_fit"
    
    step_4: "生成桥接文本"
      format: "类比引入标记（来自文风包）+ 类比核心 + 落回概念"
      example: {
        target_concept: "明代内阁票拟制度",
        reader_domain: "corporate_structure",
        generated: "你可以把明代内阁想象成一个没有最终签字权的'总经办'，所有方案都要送到皇帝——这位永远'已读不回'的董事长——那里。"
      }
    
    step_5: "质量阀"
      checks:
        - "类比不歪曲概念核心（对比节点 formal_expr 字段）"
        - "类比不在 tension_level>0.8 时使用轻佻风格"
        - "类比长度不超过 max_chars 约束（通常 100 字）"
      if_fails: "标记并回退到 fallback 类比"
```

### 情感桥（Emotional Bridge）挖掘算法

```yaml
emotional_bridge_engine:
  inputs:
    - knowledge_node: 当前知识节点
    - reader_persona: 读者画像
  
  algorithm:
    step_1: "提取节点情感基调"
      extraction:
        - "从 node 的 emotional_valence 字段读取"
        - "从 node 的 narrative_hooks 中提取隐含情感"
        - "从 node 涉及的 actor.dilemma 中提取心理冲突"
    
    step_2: "匹配读者情感原型"
      match:
        - "node 情感基调 IN reader_persona.emotional_archetype.resonates_with？"
        - "是否回避 repelled_by 标签中的情感类型？"
      score: "match ? 1.0 : 0"
    
    step_3: "生成情感连接文本"
      strategy:
        - if "node_emotion == systemic_frustration 且 reader 有相同共鸣标签":
            template: "就像你明知流程有问题，却无力推动变革时的那种倦怠。"
        - if "node_emotion == career_ceiling 且 reader 为 ambitious_but_trapped_professional":
            template: "如果你是那个既要完成老板指标，又要安抚团队情绪的部门经理，你会理解这种深夜批阅奏折时的无力感。"
        - if "node_emotion == overworked_leader 且 reader 为 burned_out_professional":
            template: "就像你在凌晨三点修改一份注定会被董事会驳回的方案，每一个标点符号都充满了疲惫和无力。"
      fallback: "如果无精确匹配，使用通用现代场景替代，但必须标注 low_confidence 以待编辑确认"
    
    step_4: "质量阀"
      checks:
        - "情感桥是否真实反映节点内容（不歪曲古人心理）"
        - "是否落入 reader_persona.resistance_map.triggers（如不能触发'道德说教'）"
        - "是否与当前 tension 一致（tension>0.7 时不能使用轻松类比）"
      if_fails: "标记 emotional_bridge 槽位为 low_confidence，提请编辑介入"
```

---

## 附录三：多系列 IP 管理规范

当机构同时运营多个系列时，需要以下隔离与复用机制：

### 配置隔离规则

```yaml
multi_series_management:
  # 隔离（每个 Series 独立空间）
  isolation_rules:
    - "每个 Series 拥有独立的配置数据库"
    - "Series Profile 之间的全部字段互不继承"
    - "一个 Series 的模板偏好/禁用项不影响另一个"
  
  # 复用（共享资产）
  sharing_rules:
    - "通用知识节点（如'明代内阁制度'定义基础版）可跨系列共享"
    - "文风包可跨系列引用（但每个 Series 可锁定 custom forbidden 项）"
    - "读者画像可跨系列复用"
    - "对抗 Agent 基础规则可跨系列共享"
  
  # 冲突检测
  conflict_detection:
    - "当同一机构运营的多个系列需在同一年内发布时，自动检查风格相似度"
    - "相似度度量：JS 散度计算两个 Series Profile 中文风包 Lexical Pool 分布差异"
    - "JS 散度 < 0.2 触发品牌稀释警告"
    - "JS 散度 < 0.1 阻断生成（除非显式申请并行发布并人工确认差异化路径）"
  
  # 品牌稀释的自动缓解建议
  mitigation_suggestions:
    - "为系列 B 更换 primary motif（主旋律差异化）"
    - "为系列 B 调整模板角色偏好（如 A 偏好 TPL-01，B 主用 TPL-04）"
    - "为系列 B 锁定不同的 forbidden_tags"
    - "为系列 B 设置不同的冲击力政策（如 A 高反常识密度，B 低密度）"
```

---

## 附录四：选材品味档案（Editor Taste Profile）

这是将编辑/作者的"选材偏好"显式化的机制——每次人工干预都会被记录，形成可复用的品味画像。

```yaml
editor_taste_profile:
  editor_id: "editor_wang_v1"
  
  # 历史 override 记录（自动累计）
  override_history:
    - timestamp: "2026-07-08T14:30:00"
      decision_point: "selection"
      node_id: "event_wanli_zhangju_funeral"
      action: "boost +0.3"
      reason: "仪式违背事件是全书结构困境的最佳象征"
      context: "INTENT_TRAGEDY, HP=structural_materialist_v1"
    
    - timestamp: "2026-07-08T15:10:00"
      decision_point: "template"
      section: "ch_02_sec_03"
      original: "TPL_08"
      modified: "TPL_10"
      reason: "多视角更符合本章'多方博弈'基调"
  
  # 自动提炼的品味特征（引擎在每次 override 后更新）
  derived_taste_profile:
    - trait: "偏好象征性强的微观事件作为锚点"
      evidence: "多次 boost 带有 high symbolic_power 的 micro_event 节点"
      confidence: 0.85
    
    - trait: "倾向于使用 TPL-10 替代 TPL-08"
      evidence: "在 counterpoint 角色中 4/6 次 override TPL-08→TPL-10"
      confidence: 0.75
    
    - trait: "偏好 high data_richness 节点"
      evidence: "选材阶段 consistently 优先确认 high 评级节点"
      confidence: 0.90
  
  # 下次推荐时的应用
  application:
    - "当编辑的 taste_profile 置信度 > 0.7 时，选材/模板推荐可将品味特征作为额外修正项"
    - "修正幅度不超过 ±0.1，保留选择器的主体权重"
    - "始终保留编辑'surprise me'选项（临时关闭品味档案影响）"
```

---

## 附录五：运行时数据流与模块间接口契约

### 完整数据流

```
[User/Editor]
   │ 创建 Series Profile、Book Config
   ▼
┌──────────────────┐
│ 冷启动配置服务     │ ← 人工定义：史观包/读者画像/文风包/模板/标签
└──────┬───────────┘
   │ Series Profile + Book Config JSON
   ▼
┌──────────────────┐
│ 选材引擎           │
│ 输入: INTENT, HP, RP, 约束条件
│ 处理: 知识库节点评分 (SelectionScore公式)
│      约束过滤 (coverage/time_order/drama_cap/source_min)
│ 输出: 选定节点序列 + 评分明细 + 编辑override接口
└──────┬───────────┘
   │ 选定节点序列
   ▼
┌──────────────────┐
│ 模板选择器         │
│ 输入: 节点标签 + scale + narrative_potential + HP + chapter_position
│ 处理: Layer1硬性过滤 → Layer2加权评分 → Layer3语境修正
│ 输出: 模板ID + 角色指派 + 完整decision_trace
└──────┬───────────┘
   │ 模板序列 + 角色指派
   ▼
┌──────────────────┐
│ COG + PDL 编排器   │
│ 输入: 模板序列 + 章节角色 + 史观包 + 读者画像 + 节点impact数据
│ 处理: 过渡规则注入 → 张力曲线 → 钩子投放到 → 冲击力点位 → 主旋律变奏计划
│ 输出: 完整章节编排JSON (含所有单位/槽位/PDL标记)
└──────┬───────────┘
   │ 编排JSON
   ▼
┌──────────────────┐
│ 对抗评审层         │
│ 输入: 编排JSON + HP + RP + Series Profile
│ 处理: 5 Agent 并行评审 → 汇总输出
│ 输出: 评审报告 (passed/issues/modifications)
└──────┬───────────┘
   │ (if not passed) → 返回修改
   │ (if passed)
   ▼
┌──────────────────┐
│ 受控生成层          │
│ 输入: 编排JSON + 知识节点 + 文风包 + HP + RP + PDL标记
│ 处理: 4层注入引擎 → 逐单元填槽 → 输出后校验
│ 输出: 结构化文本
└──────┬───────────┘
   │ 结构化文本
   ▼
┌──────────────────┐
│ 多模态派生层        │
│ 输入: 结构化文本 + 情绪标签 + 冲击力标记 + 主旋律标记
│ 处理: SSML生成规则 → 动画分镜规则 → 知识卡片打包
│ 输出: Markdown文本 + SSML脚本 + 动画分镜JSON + 知识卡片JSON
└──────────────────┘
```

### 关键接口契约

```yaml
interfaces:
  # 选材引擎 → 模板选择器
  selection_to_templator:
    payload: {
      selected_nodes: [KnowledgeNode],   # 选定节点序列
      hp_id: string,                     # 史观包ID
      rp_id: string,                     # 读者画像ID
      intent: string,                    # 叙事意图
      chapter_position: string,          # 开篇/中间/结尾
      previous_template: string|null     # 前一节模板（用于去重）
    }
    response: {
      template_id: string,
      role: string,                      # anchor_event/deep_dive/...
      confidence: float,                 # 0-1
      decision_trace: object,            # 三层评分明细
      runner_up: {template: string, score: float}
    }

  # 编排器 → 对抗评审
  orchestrator_to_review:
    payload: {
      chapter_orchestration: {           # 完整编排JSON
        chapter_id: string,
        sections: [{
          template_id, role, knowledge_node,
          tension_level, density, transition_from_previous,
          units: [unit_type, fill_slots_schema, pdl_markers]
        }],
        melody_plan: object,             # 主旋律变奏计划
        hook_plan: object                # 钩子计划
      },
      hp: HistoriographyProfile,
      rp: ReaderPersona,
      series_id: string
    }
    response: {
      passed: boolean,
      issues: [{
        dimension, severity, location,
        issue, suggestion, auto_fixable
      }],
      overall_comment: string
    }

  # 编排器 → 受控生成
  orchestrator_to_generation:
    payload: {
      units_to_fill: [{
        unit_type: string,
        fill_slots: object,              # 待填槽位Schema
        knowledge_context: object,       # 对应知识节点
        style_pack: StylePack,           # 当前文风包
        hp_constraints: object,          # 史观约束
        rp_slots: object,        
...(truncated)...

好的，之前的对话输出因篇幅被截断。现在我从**接口契约**的断点处接上，并补完所有后续附录。

---

## 接续：附录五 运行时数据流与模块间接口契约（续）

### 关键接口契约（续）

```yaml
interfaces:
  # --- 续：编排器 → 受控生成 ---
  orchestrator_to_generation:
    payload: {
      units_to_fill: [{
        unit_type: string,                     # context_unit / event_unit / actor_unit / structure_unit / reflection_unit
        fill_slots: object,                    # 待填槽位Schema（每个槽位的required / max_chars / constraint）
        knowledge_context: {                   # 对应知识节点
          node_id: string,
          summary: string,
          structural_insights: [string],
          impact_potential: object,
          narrative_hooks: [string],
          analogy_pool: [object]
        },
        style_pack: {                          # 当前文风包（完整五层）
          id: string,
          lexical_pool: object,
          syntax_bias: object,
          rhetoric: object,
          layout_pref: object,
          tension_default_map: object
        },
        hp_constraints: {                      # 史观约束
          forbidden_keywords: [string],
          approved_keywords: [string],
          stance_guidance: string,
          tone_requirement: string
        },
        rp_slots: {                            # 读者连接点指令
          cognitive_bridge: {                   # 是否必填、类比域、max_chars
            required: boolean,
            source_domain: [string],
            max_chars: int
          },
          emotional_bridge: {
            required: boolean,
            target_emotion: string,
            max_chars: int
          }
        },
        pdl_markers: {                         # PDL标记
          tension_current: float,              # 当前tension_level
          tension_target: float,               # 目标tension_level(本单元后应达到)
          hook_type: string|null,              # 如果是钩子位置，钩子类型
          is_climax: boolean,
          impact_injection: {                  # 冲击力数据（如适用）
            required: boolean,
            data: object|null,
            format: string
          },
          motif_variation: {                   # 主旋律变奏（如适用）
            variation_type: string|null,       # statement / rhetorical_question / thesis / epigram
            motif_statement: string
          }
        },
        template_global_constraints: {         # 模板全局约束
          forbidden_tags: [string],
          required_tags: [string],
          density: string,                     # high / medium / low
          role: string                         # anchor_event / deep_dive / counterpoint / macro_frame / synthesis / bridge
        }
      }],
      model: string,                           # 模型标识
      regression_check_id: string|null         # 模型回归测试ID
    }
    response: {
      filled_units: [{                         # 填槽结果
        unit_id: string,
        filled_text: string,
        confidence: float                      # 0-1
      }],
      post_checks: {                           # 输出后校验
        forbidden_keywords_hit: [string],      # 命中禁用词的列表（空=通过）
        tension_consistency: boolean,          # 输出文本tension是否匹配预期
        style_deviation: float,                # 文风偏离度检测（JS散度）
        motif_present: boolean                 # 主旋律变奏是否正确填入
      },
      warnings: [string]
    }

  # --- 受控生成 → 多模态输出 ---
  generation_to_multimodal:
    payload: {
      rendered_chapter: {                      # 结构化文本
        chapter_id: string,
        sections: [{
          section_id: string,
          template_id: string,
          units: [{
            unit_type: string,
            text: string,
            pdl_markers_applied: object,       # 实际注入的PDL标记
            tension_level_at_unit: float
          }]
        }]
      },
      pdl_markers_global: {                    # 全局PDL标记（用于SSML/动画）
        climax_unit_id: string,
        hook_positions: [{unit_id, hook_type, text}],
        impact_positions: [{unit_id, data, source}],
        motif_positions: [{unit_id, variation_type, text, is_epigram: boolean}]
      },
      emotion_arc: [{                          # 情绪弧线时序数据
        unit_id: string,
        tension: float,
        emotional_tone: string,                # sober_tragic / calm_analytical / dramatic_irony + 细分
        pace: string                           # brisk / moderate / slow / x_slow
      }]
    }
    response: {
      ssml_script: string,                     # 完整SSML脚本
      animation_storyboard: {                  # 动画分镜JSON
        scenes: [{
          timestamp: string,                   # 对应文本位置
          animation_type: string,              # static_scene / timeline_zoom / data_pulse / institutional_diagram / ...
          visual_elements: [string],
          emotional_sync: string,              # 与SSML情绪标签同步的标记
          duration_seconds: float
        }]
      },
      knowledge_cards: [{                      # 交互知识卡片
        card_id: string,
        concept: string,
        summary: string,
        key_data: object,
        source: string,
        related_concepts: [string]
      }]
    }
```

---

### 模块间事件总线（Event Bus）定义

系统采用事件驱动架构，模块间通过以下事件异步通信：

```yaml
event_bus:
  events:
    - event: "selection.completed"
      payload: { book_id, intent, selected_nodes: [node_ids], editor_overrides: [object] }
      consumers: [templator]
    
    - event: "templator.assigned"
      payload: { book_id, chapter_id, sections: [{template_id, role, node_id}] }
      consumers: [orchestrator]
    
    - event: "orchestration.completed"
      payload: { book_id, chapter_id, orchestration_json: object }
      consumers: [adversarial_review]
    
    - event: "review.passed"
      payload: { book_id, chapter_id, review_report: object }
      consumers: [generation_engine]
    
    - event: "review.failed"
      payload: { book_id, chapter_id, issues: [object], return_to: string }
      consumers: [orchestrator, editor_notification]
    
    - event: "generation.completed"
      payload: { book_id, chapter_id, output_paths: object }
      consumers: [multimodal_derivation, series_consistency_check]
    
    - event: "series_consistency.violation"
      payload: { book_id, chapter_id, violations: [object] }
      consumers: [editor_notification, series_manager]
```

---

## 附录六：全自动生产状态监控指标（完整版）

### 实时监控面板指标

```yaml
monitoring:
  # ─── 生产效率指标 ───

  - metric_group: "efficiency"
    metrics:
      - id: "cold_start_completion_rate"
        name: "冷启动配置完成率"
        definition: "Series Profile 配置项完成百分比（史观包/读者画像/文风包/模板/标签体系）"
        target: "100%（新系列上线前）"
        measurement: "配置界面进度条"
      
      - id: "node_to_first_draft_time"
        name: "知识点入库到初稿输出时长"
        definition: "从知识节点完成标注入库到首版结构化文本输出的端到端分钟数"
        target: "≤5分钟"
        measurement: "P95 延时统计"
      
      - id: "multi_version_derivation_time"
        name: "多版本派生时长"
        definition: "切换文风包生成另一版本（大众版→学术版）所需时间"
        target: "≤1分钟"
        measurement: "P95 延时统计"
      
      - id: "parallel_chapter_throughput"
        name: "并行章节吞吐量"
        definition: "无依赖冲突时，同时编排/渲染的最大章节数"
        target: "≥10章/小时（标准配置下）"
        measurement: "压测数据"

  # ─── 质量指标 ───

  - metric_group: "quality"
    metrics:
      - id: "adversarial_first_pass_rate"
        name: "对抗评审首次通过率"
        definition: "章节编排提交对抗评审后，不经过人工修改直接通过的百分比"
        target: "≥80%"
        trend: "↑（随对抗规则优化和品味档案积累应上升）"
        alert: "连续 3 本书低于 60% 时触发冷启动配置复核"
      
      - id: "human_override_rate"
        name: "编辑手动干预率"
        definition: "编辑手动 override（选材/模板/编排/渲染）占全部决策动作的比例"
        target: "稳态 ≤15%"
        trend: "↓（随品味档案优化应下降）"
        alert: "新系列启动前三个月可接受 ≤30%，稳定后 ≤15%"
      
      - id: "series_consistency_pass_rate"
        name: "系列一致性校验通过率"
        definition: "所有章节通过系列一致性校验（主旋律/文风/模板偏好/冲击力政策）的比例"
        target: "≥95%"
      
      - id: "impact_integrity_violations"
        name: "冲击力约束违规次数"
        definition: "require_primary_source / forbid_superlative_distortion 等硬约束违规次数"
        target: "0"
        severity: "error-level"
        action: "阻断生成，自动通知编辑"
      
      - id: "forbidden_keyword_hit_rate"
        name: "禁用词命中率"

...(truncated)...