# ICM-SR: SR-TEXT-006
# 发送方: CDO-CONTENT → 接收方: CDO-DESIGN-001
# 优先级: P2
# 日期: 2026-06-15

request:
  id: SR-TEXT-006
  type: AgentClusterDesign
  priority: P2
  title: 知识科普智能体集群设计（文字生产线 · 集群 E）
  summary: >
    设计一套面向知识科普创作的多 Agent 集群。核心逻辑是"降维优先"——
    将专业领域知识翻译为大众可理解的语言——核心资产是术语→通俗映射表。
    覆盖科学科普、商业通识、健康科普、历史解读四大类。

spec:
  task_type: AgentClusterDesign
  cluster:
    name: "Knowledge Popularization Swarm"
    code: "CLUSTER-E"
    domain: "content_production.popularization"

    guilds:
      # ===== Guild 1: Topic Selector =====
      - id: TOPIC_SELECT
        name: 选题 Guild
        agents:
          - role: CuriosityGapFinder
            description: >
              发现"公众好奇但不懂"的话题：
              - 搜索引擎趋势分析（什么在飙升？）
              - 问答平台热点（知乎/Quora 高频问题）
              - 社交媒体讨论（什么概念被频繁误解？）
              - 新闻事件中的"知识缺口"（熔断是什么？mRNA 疫苗怎么工作？）
          - role: AudienceLevelMatcher
            description: >
              评估选题的目标受众知识水平：
              - L1 零基础（没有任何先验知识）
              - L2 有兴趣（有模糊概念，需要系统化）
              - L3 入门者（有一定基础，需要深化）
              匹配对应的解释深度和前提知识量

        gate: TOPIC_GATE
        gate_conditions:
          - "选题有真实需求证据（搜索趋势/问答热度/事件关联） ✓"
          - "受众知识水平明确标注 ✓"

      # ===== Guild 2: Research =====
      - id: RESEARCH
        name: 调研 Guild
        agents:
          - role: ExpertSourceCollector
            description: >
              从权威来源收集专业资料：
              - 学术文献（PubMed/arXiv/Google Scholar）
              - 权威教科书/百科（领域标准定义）
              - 官方机构（WHO/NASA/央行/统计局）
              - 领域专家公开讲座/访谈
              
          - role: ConceptMapper
            description: >
              构建概念关系图谱：
              - 核心概念 → 子概念 → 前置知识
              - 标注概念之间的依赖关系（理解 B 必须先理解 A）
              - 识别"最简知识路径"（最少需要解释几个概念才能说清主题）

        gate: RESEARCH_GATE
        gate_conditions:
          - "每个核心概念 ≥ 1 个权威源 ✓"
          - "概念关系图谱完整（无孤立概念） ✓"

      # ===== Guild 3: Translate（核心 Guild） =====
      - id: TRANSLATE
        name: 术语降维 Guild（★ 核心）
        description: 这是整个集群的灵魂——将专业术语翻译为通俗表达
        
        agents:
          - role: JargonDecoder
            description: >
              逐层翻译（3 层降维策略）：
              
              原始术语："卷积神经网络通过卷积核在输入数据上滑动进行特征提取"
              
              L1 降维（替换术语）：
              "CNN 用一个小窗口在图片上滑动，每次只看一小块区域，提取这块的特征"
              
              L2 降维（引入类比）：
              "就像用放大镜逐块扫描一张照片——先看左上角有没有猫耳朵，
              再看右上角有没有猫尾巴，最后拼起来判断是只猫"
              
              L3 降维（极致简化）：
              "让电脑像拼拼图一样，一块一块地认出照片里是什么"
              
              译后检查：
              - 是否保持了核心准确性？（不能为了通俗而错误）
              - 是否引入了误导性类比？
              - 是否在合适处标注了"简化说明"？
              
          - role: AnalogyGenerator
            description: >
              为每个核心概念生成 2-3 个生活化类比：
              - 要求：用目标受众日常生活经验中的事物
              - 约束：类比不能扭曲原概念的核心逻辑
              - 示例："API 就像餐厅的服务员——你（客户端）看菜单点菜（发请求），
                服务员去厨房（服务器）取菜，再端给你（返回数据）"
                
          - role: Simplifier
            description: >
              全文降维处理：
              - 句子复杂度控制（Flesch-Kincaid 可读性指标）
              - 段落长度控制（≤ 5 句/段）
              - 专业术语首次出现时强制解释
              - 抽象概念必须配具体例子

        gate: TRANSLATE_GATE
        gate_conditions:
          - "每个专业术语有通俗解释 ✓"
          - "类比准确（不引入误解） ✓"
          - "可读性指标达标（按受众 L1/L2/L3 不同阈值） ✓"

      # ===== Guild 4: Creative =====
      - id: CREATIVE
        name: 创意表达 Guild
        agents:
          - role: NarrativeDesigner
            description: >
              设计叙事结构：
              - 问题驱动："你有没有想过，为什么..."
              - 故事驱动："1998 年，一位物理学家在喝咖啡时突然想到..."
              - 历史线："从伽利略到爱因斯坦，人类对引力的理解经历了..."
              - 对比冲击："你以为 X 是这样的，实际上完全相反"
          - role: VisualExplainer
            description: >
              生成可视化解释（描述/DSL，非直接画图）：
              - 信息图结构
              - 流程图
              - 对比表
              - 时间线
              - 动画脚本

        gate: CREATIVE_GATE
        gate_conditions:
          - "叙事结构完整 ✓"
          - "趣味性与准确性权衡合理 ✓"

      # ===== Guild 5: Review =====
      - id: REVIEW
        name: 审校 Guild
        agents:
          - role: AccuracyChecker
            description: "逐条核实：每个科学/事实声明是否有权威源支撑"
          - role: AccessibilityTester
            description: "以目标受众视角阅读：能看懂吗？哪里卡住了？"

        gate: REVIEW_GATE
        gate_conditions:
          - "准确性 100%（无误导） ✓"
          - "可读性达标（目标受众能理解） ✓"
          - "趣味性 ≥ 阈值（不枯燥） ✓"

    integration:
      knowledge_cell:
        provider: CDO-DATA-001
        assets:
          - "术语→通俗映射表（★ 核心资产，种子注入 + AIGC 自动扩展）"
          - "类比库（已验证准确的生活化类比）"
          - "受众知识水平评估模型"
          - "领域本体（概念依赖关系）"
      data_agent:
        services:
          - "情报挖掘：搜索趋势 + 问答平台热点"
          - "学术文献检索（PubMed/arXiv 集成）"

    l2_configs:
      configs:
        - id: science_pop
          name: 科学科普
          key_differences: "准确 > 有趣（牺牲趣味也不能牺牲准确） + 物理/生物/化学本体"
        - id: business_explainer
          name: 商业通识
          key_differences: "案例驱动 + 数据可视化 + 避免商业术语轰炸"
        - id: health_edu
          name: 健康科普
          key_differences: "极高准确率要求 + 避免恐慌/误导 + 引用权威医学源 + 免责声明强制"
        - id: history_narrative
          name: 历史解读
          key_differences: "时间线驱动 + 多角度呈现 + 避免以今释古"

    workflow:
      type: "Sequential with Translate as Central Hub"
      description: "TOPIC → RESEARCH → TRANSLATE（核心） → CREATIVE → REVIEW"

    phases:
      - milestone: M1
        scope: "TOPIC + RESEARCH + TRANSLATE（种子术语映射表注入）"
        target: "单篇科普，术语翻译准确，人类只审阅不重写"
      - milestone: M2
        scope: "+ CREATIVE + REVIEW + 类比库 AIGC 自动扩展"
        target: "从选题到发布全自动，术语映射表自我增长"

  quality_requirement:
    min_cqs: 4.0
    must_pass:
      - "topology_check / role_uniqueness / message_protocol_check"
      - "accuracy_check（无误导性内容）"
      - "accessibility_check（可读性达标）"
      - "jargon_coverage（每个术语有通俗解释）"
    golden_tests: 6
    acceptance:
      - "选一个专业概念，产出 L1/L2/L3 三级降维文本"
      - "类比准确（领域专家认可 '没有引入误解'）"
      - "术语映射表从 100 条种子自动增长到 500+"

  sla:
    target_latency: "18h"
    max_latency: "48h"
    sla_level: "Standard"

consumer_notes:
  background: >
    知识科普集群的核心差异化能力是"术语→通俗"的降维翻译。
    这与数据内阁的"领域术语→通用信号（Universal Signals）"
    理念一脉相承——本质上是做同一个方向的工作：把专业语言的噪声
    剥离，留下可传递的信号。术语映射表既是输入也是产出，通过
    AIGC 闭环自我增长。
