# ICM-SR: SR-TEXT-007
# 发送方: CDO-CONTENT → 接收方: CDO-DESIGN-001
# 优先级: P2
# 日期: 2026-06-15

request:
  id: SR-TEXT-007
  type: AgentClusterDesign
  priority: P2
  title: 观点论证智能体集群设计（文字生产线 · 集群 F）
  summary: >
    设计一套面向观点表达与论证说服场景的多 Agent 集群。
    核心逻辑是"说服优先"——从立场定义到论证构建到反方预演，
    确保逻辑严密、修辞有力、偏见可控。覆盖评论/社论/演讲稿三大类。

spec:
  task_type: AgentClusterDesign
  cluster:
    name: "Opinion & Argument Swarm"
    code: "CLUSTER-F"
    domain: "content_production.opinion"

    guilds:
      # ===== Guild 1: Position Definer =====
      - id: POSITION_DEFINE
        name: 立场定义 Guild
        agents:
          - role: StanceCalibrator
            description: >
              从输入中精确提取和校准立场：
              - 区分"事实陈述"与"价值判断"（前者可验证，后者不可）
              - 将模糊立场转化为可论证的命题
              - 标注立场的隐含前提（如"自由市场更有效率"隐含了哪些假设）
              
              示例：
              输入："我认为 AI 监管应该更严格"
              转化：
                可论证命题①：当前 AI 监管存在 X/Y/Z 漏洞
                可论证命题②：这些漏洞导致了 A/B/C 实际损害
                可论证命题③：更严格的监管能在不扼杀创新的前提下弥补漏洞
                
          - role: AudienceProfiler
            description: >
              分析目标受众：
              - 已有立场（支持/中立/反对/不知情）
              - 核心关切（他们最在意什么？）
              - 可能被说服的杠杆点（什么论据最可能打动他们？）
              - 可能引发抵触的雷区（什么论据会适得其反？）

        gate: POSITION_GATE
        gate_conditions:
          - "立场可转化为 ≥ 2 个可论证命题 ✓"
          - "隐含前提已标注 ✓"
          - "受众画像包含可说服杠杆点和雷区 ✓"

      # ===== Guild 2: Argument Builder =====
      - id: ARGUMENT_BUILD
        name: 论证构建 Guild
        agents:
          - role: PremiseCollector
            description: >
              为每个可论证命题搜集支持性证据：
              - 统计/研究数据（标注来源和可信度）
              - 历史案例（标注相似度与关键差异）
              - 专家观点（标注专家立场和潜在偏见）
              - 逻辑推理（演绎/归纳/类比/因果）
              
              每类证据标注强度：强/中/弱
              
          - role: LogicChainBuilder
            description: >
              将证据串联为逻辑链：
              前提① + 前提② → 中间结论 A
              中间结论 A + 前提③ → 中间结论 B
              中间结论 B + 前提④ → 最终结论
              
              显式标注每个推理步骤的类型（演绎/归纳/类比）
              
          - role: EvidenceRanker
            description: >
              按说服力对证据进行排序：
              - 最强证据放在开头（锚定效应）还是结尾（近因效应）？
              - 弱势证据是否需要主动暴露？（诚实策略 vs 聚焦优势）
              - 情感证据 vs 理性证据的比例（按受众类型调整）

        gate: ARGUMENT_GATE
        gate_conditions:
          - "每个可论证命题 ≥ 2 类证据 ✓"
          - "逻辑链可追溯（每步推理有依据） ✓"
          - "数据来源标注完整 ✓"

      # ===== Guild 3: Counter-Argument（★ 核心差异化） =====
      - id: COUNTER_ARGUMENT
        name: 反方预演 Guild（★ 核心）
        description: 预演反方最强论据并逐一回应——这是好论证与差论证的分水岭
        
        agents:
          - role: DevilsAdvocate
            description: >
              站在反方立场，生成最强反驳：
              - 对每个核心论据提出反证
              - 指出逻辑链中的薄弱环节
              - 质疑证据的可靠性/代表性/时效
              - 提出替代解释（同一数据，不同解读）
              
              约束：反方论据必须真实有力，不能制造稻草人
              
          - role: StrawmanDetector
            description: >
              检测论证中是否存在逻辑谬误：
              - 稻草人：歪曲对方观点再攻击
              - 滑坡：极端化后果链条
              - 诉诸权威：用不相关权威支持论点
              - 诉诸多数：因为大家都信所以对
              - 假二分：制造非此即彼的假对立
              - 循环论证：结论藏在前提里
              - 以偏概全：个案→普遍规律
              
          - role: RebuttalWriter
            description: >
              对反方最强论据逐一回应：
              - 承认对方正确之处（诚实加分）
              - 指出对方论据的局限（不否认事实，但限制范围）
              - 用更强证据反驳（你的数据对，但我的数据更新/更全/更相关）
              - 提升论证层次（从事实争论到价值框架争论）

        gate: COUNTER_GATE
        gate_conditions:
          - "反方最强论据 ≥ 3 个（非稻草人） ✓"
          - "无逻辑谬误检出 ✓"
          - "每个反方论据有实质性回应（非回避） ✓"

      # ===== Guild 4: Polish =====
      - id: POLISH
        name: 修辞打磨 Guild
        agents:
          - role: RhetoricEnhancer
            description: >
              修辞优化：
              - 开头：钩子设计（提问/数据冲击/故事/反常识）
              - 节奏：长短句交替 + 高潮布局
              - 金句：提炼 3-5 个可引用的核心金句
              - 结尾：回响（呼应开头/行动号召/开放问题）
              
          - role: ToneCalibrator
            description: >
              语气校准：
              - 按配置调整：理性克制 / 激昂澎湃 / 冷静嘲讽 / 温暖共情
              - 避免越界：攻击性言论 / 人格攻击 / 煽动暴力
              - 受众适配：学术受众 → 严谨；大众 → 亲和

        gate: POLISH_GATE
        gate_conditions:
          - "开头含有效钩子 ✓"
          - "金句可独立引用（脱离上下文仍有力量） ✓"
          - "语调与配置一致 ✓"

      # ===== Guild 5: Final Gate =====
      - id: FINAL_GATE
        name: 终审 Gate
        gate_conditions:
          - "逻辑自洽（无循环论证/偷换概念/因果倒置） ✓"
          - "偏见指数在可接受范围（显式标注未消除的偏见） ✓"
          - "语调不越界（无攻击性/煽动性/歧视性语言） ✓"
          - "高敏话题（政治/宗教/种族）→ 强制人工审批 ✓"

    integration:
      knowledge_cell:
        provider: CDO-DATA-001
        assets:
          - "逻辑谬误检测模型（分类体系 + 识别模式）"
          - "论证模式库（演绎/归纳/类比/因果的经典结构）"
          - "历史论战案例库（经典辩论的论据结构和胜负因素）"
          - "Red Flag 词库（攻击性/歧视性/煽动性语言）"
      data_agent:
        services:
          - "情报挖掘：话题相关的最新数据/研究/事件（支撑 PremiseCollector）"

    l2_configs:
      configs:
        - id: opinion_piece
          name: 评论文章
          key_differences: "强调个人视角 + 允许适度偏见 + 修辞重于结构"
        - id: editorial
          name: 社论/机构立场
          key_differences: "代表机构而非个人 + 更高合规要求 + 立场一致性校验"
        - id: speech
          name: 演讲稿
          key_differences: "口语化 + 节奏感优先 + 互动设计（停顿/设问/呼应） + 时长控制"

    workflow:
      type: "Sequential with Dialectical Loop"
      description: >
        POSITION → ARGUMENT → COUNTER → 如果反方论据太强 → 回到 ARGUMENT 补充证据
        → POLISH → GATE

    phases:
      - milestone: M1
        scope: "POSITION + ARGUMENT + POLISH"
        target: "从立场到完整论证文章"
      - milestone: M2
        scope: "+ COUNTER + 逻辑谬误检测模型"
        target: "含反方预演和回应的完整论证"

  quality_requirement:
    min_cqs: 4.0
    must_pass:
      - "topology_check / role_uniqueness / message_protocol_check"
      - "logic_fallacy_check（无逻辑谬误）"
      - "counter_argument_quality（反方论据非稻草人）"
      - "bias_transparency（未消除的偏见已标注）"
    golden_tests: 6
    acceptance:
      - "给定一个争议话题 + 立场 → 产出含反方预演的完整论证"
      - "逻辑谬误检测准确率 ≥ 90%"
      - "反方论据经人工评估 ≥ 3 条为'真实有力'（非稻草人）"

  sla:
    target_latency: "12h"
    max_latency: "36h"
    sla_level: "Standard"

consumer_notes:
  background: >
    观点论证集群的核心差异化是 DevilsAdvocate（反方预演）——
    大多数 AI 写作只会顺着你的立场堆论据，不会主动找自己论证的漏洞。
    这套集群强制要求在发布前，先让"魔鬼代言人"以反方最强姿态攻击
    自己的论证，只有扛住了才算合格。这项能力需要逻辑谬误检测模型 +
    历史论战案例库作为 Knowledge Cell 支撑。
