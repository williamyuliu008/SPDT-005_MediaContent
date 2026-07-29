# ICM-SR: SR-TEXT-001
# 发送方: CDO-CONTENT（文字产品域） → 接收方: CDO-DESIGN-001
# 优先级: P0
# 日期: 2026-06-15

request:
  id: SR-TEXT-001
  type: SingleAgentDesign
  priority: P0
  title: 文字作品分类智能体设计
  summary: >
    设计一个分类智能体，输入为对文字作品的自由描述（自然语言），
    首先将描述转化为高度结构化的规格，然后根据六套文字生产集群
    的分类体系进行判断，输出对应的集群类别和 L2 配置文件。
    该智能体是文字作品生产线的"入口路由器"。

# ============================================================
# 功能规格
# ============================================================
spec:
  task_type: SingleAgentDesign

  input:
    description: >
      用户在自然语言中描述其文字作品需求。典型输入示例：
      - "我需要一篇关于新能源电池技术路线的深度分析，面向投资人群，要求数据驱动"
      - "帮我写一篇今日A股收盘快评，300字以内，面向散户"
      - "写一份面向开发者的 REST API 接口文档，需要包含认证、端点、错误码"
      - "写一篇科普文章解释量子计算，面向高中生，要有类比"
    format: "自由文本（1-5000字）"
    complexity: "含歧义、隐含需求、专业术语混用"

  process:
    step_1_structure:
      name: 描述结构化
      description: >
        将自由文本描述转化为结构化规格。提取以下维度：
        
        ① 核心意图：用户到底要什么？（一句话提炼）
        ② 产品类型：新闻/分析/报告/文档/科普/评论/营销文案/其他
        ③ 目标受众：专业人群/投资人群/技术人群/普通大众/学生/决策者
        ④ 深度要求：快讯级(≤500字)/短篇(500-2000字)/中篇(2000-5000字)/深度(≥5000字)
        ⑤ 时效要求：实时(分钟)/日内(小时)/日级/周级/无时限
        ⑥ 风格倾向：数据驱动/叙事为主/论证导向/通俗易懂/技术准确/文学性
        ⑦ 领域标签：金融/科技/医疗/政策/法律/教育/消费/制造/综合...
        ⑧ 特殊约束：合规敏感/需引用来源/需多立场/需图表/需代码示例/有模板...
        ⑨ 发布渠道：网站/公众号/研报平台/社交媒体/邮件/内部文档/API文档平台...
        ⑩ 显式需求 vs 隐含需求：标记哪些是用户明确说的，哪些是推理出的
      output: "JSON 结构化规格（10 个维度，每个维度含置信度）"

    step_2_classify:
      name: 集群分类
      description: >
        根据 Step 1 的结构化规格，映射到六套文字生产集群之一：
        
        ┌─────────────────────────────────────────────────────────┐
        │ 分类决策树（优先级从高到低）                             │
        │                                                         │
        │ ① 时效要求 ≤ 日内 AND 深度 ≤ 短篇                        │
        │    → A（实时快反集群）                                   │
        │                                                         │
        │ ② 产品类型 ∈ {API文档, PRD, 架构文档, 算法说明, 用户手册} │
        │    → D（技术文档集群）                                   │
        │                                                         │
        │ ③ 深度 ≥ 中篇 AND 产品类型 ∈ {分析, 报告, 研究, 调研,     │
        │    解读, 时政, 政策}                                     │
        │    → B（深度生产集群）                                   │
        │                                                         │
        │ ④ 核心意图 包含 {卖货, 转化, 投放, 广告, 获客, 营销}      │
        │    → C（创意转化集群）                                   │
        │                                                         │
        │ ⑤ 风格倾向 = 通俗易懂 AND 受众 ∈ {普通大众, 学生}         │
        │    AND 领域为专业领域                                     │
        │    → E（知识科普集群）                                   │
        │                                                         │
        │ ⑥ 产品类型 ∈ {评论, 社论, 辩论, 演讲, 观点}              │
        │    → F（观点论证集群）                                   │
        │                                                         │
        │ ⑦ 默认 → B（深度生产集群，最通用）                       │
        └─────────────────────────────────────────────────────────┘
      output: "集群类别 + 分类置信度 + 备选集群（置信度接近时）"

    step_3_configure:
      name: 配置推荐
      description: >
        在确定的集群下，选择最匹配的 L2 配置文件：
        
        - A 集群配置：breaking_news / market_flash / tech_brief / sports_live
        - B 集群配置：equity_research / industry_analysis / policy_analysis / 
                       political_analysis / academic_survey / investigative_report
        - C 集群配置：feed_ad / brand_copy / social_media / email_marketing
        - D 集群配置：prd / arch_doc / algo_spec / api_doc / user_manual
        - E 集群配置：science_pop / business_explainer / health_edu / history_narrative
        - F 集群配置：opinion_piece / editorial / speech
        
        推荐逻辑：基于 Step1 的 ⑪领域标签 + ③目标受众 + ⑥风格倾向 
        做多维匹配，输出最佳匹配的配置文件路径和参数建议
      output: "配置文件路径 + 参数调整建议 + 备选配置"

    step_4_interrogate:
      name: 澄清反问（仅当不确定时触发）
      description: >
        当分类置信度 < 0.85 或配置匹配度 < 0.80 时：
        生成 1-3 个精准反问，帮助用户澄清歧义。
        
        反问应聚焦于：
        - "你的核心目标是让读者理解、行动还是被说服？"
        - "这篇文章最不能被牺牲的是什么？速度、深度还是趣味性？"
        - "你提到的 XX 领域知识，是否需要引用权威来源？"
        
        → 用户回答后重新走 Step 1-3
      output: "反问列表（仅低置信度时）+ 更新后的分类结果"

  output:
    final_delivery:
      format: JSON
      schema:
        structured_spec:
          intent: "string"
          product_type: "string"
          audience: ["string"]
          depth: "string"
          urgency: "string"
          style: ["string"]
          domain_tags: ["string"]
          constraints: ["string"]
          channels: ["string"]
          explicit_needs: ["string"]
          inferred_needs: ["string"]
          confidence_per_dimension: "object"
        classification:
          cluster: "A|B|C|D|E|F"
          cluster_name: "string"
          confidence: "float (0-1)"
          alternative_cluster: "string (if confidence < 0.85)"
          decision_path: "string (explainable trace)"
        configuration:
          config_name: "string"
          config_path: "string"
          parameter_overrides: "object"
          alternative_config: "string"
          match_confidence: "float (0-1)"
        interrogations:
          questions: ["string"]  # empty if high confidence
        metadata:
          agent_version: "string"
          processing_time_ms: "int"
          model_used: "string"

# ============================================================
# 质量要求
# ============================================================
  quality_requirement:
    min_cqs: 4.0
    must_pass:
      - "structure_completeness"     # 10 个维度全部提取
      - "classification_accuracy"     # 与人工标注一致率 ≥ 95%
      - "explainability"              # 决策路径可解释
      - "low_confidence_interrogate"  # 低置信度时触发反问
    golden_tests: 15
    edge_cases:
      - "同时包含分析和营销需求的混合描述"
      - "极简输入（≤10字）"
      - "中英混杂描述"
      - "包含矛盾需求的描述（既要深度又要快）"
      - "新手用户的模糊需求"

# ============================================================
# 集成要求
# ============================================================
  integration:
    upstream:
      - "接收来自任何渠道的自然语言输入"
      - "可作为 API / CLI / IM Bot 调用"
    downstream:
      - "输出直接对接对应集群的 Execution Orchestrator"
      - "结构化规格写入 Knowledge Cell 的用户画像子系统"
    knowledge_cell:
      depends_on:
        - "CDO-DATA-001: 领域本体（术语识别与消歧）"
        - "已有六套集群的 L2 配置元数据"

# ============================================================
# SLA
# ============================================================
  sla:
    target_latency: "2s"        # 分类必须快，不能成为瓶颈
    max_latency: "5s"
    quality_bar: "cqs >= 4.0"
    sla_level: "Standard"

# ============================================================
# 上下文说明
# ============================================================
consumer_notes:
  background: >
    文字作品生产线规划了 6 套集群（实时快反/深度生产/创意转化/
    技术文档/知识科普/观点论证），每套集群下有 2-8 份 L2 配置文件。
    总计 ~25 份配置覆盖全品类文字产品。
    
    这个分类智能体是所有文字生产集群的"统一入口路由器"。
    用户在任何一个触点（Web/API/IM）描述需求后，经由该智能体
    完成"需求结构化 → 集群分类 → 配置推荐"三步，
    然后直接路由到对应集群的 Execution Orchestrator 开始生产。
    
    该智能体设计为 SingleAgent，逻辑上是一个"意图路由器"，
    而非完整的集群——它的核心能力是结构化分类，不是内容生成。
  
  existing_assets:
    - "附录C-文字作品生产线规划（含6套集群的完整 Guild/配置/工作流定义）"
    - "数据内阁 Knowledge Cell（领域本体 + 术语映射）"
  
  related_designs:
    - "SR-TEXT-002（深度生产集群设计）—— 分类智能体的主要下游消费者"
