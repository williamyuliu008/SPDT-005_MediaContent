# ICM-SR: SR-TEXT-005
# 发送方: CDO-CONTENT → 接收方: CDO-DESIGN-001
# 优先级: P1
# 日期: 2026-06-15

request:
  id: SR-TEXT-005
  type: AgentClusterDesign
  priority: P1
  title: 技术文档智能体集群设计（文字生产线 · 集群 D）
  summary: >
    设计一套面向软件/技术文档创作的多 Agent 集群。覆盖 PRD、架构设计文档、
    算法说明、API 参考文档、用户手册五大文档类型。该集群是文字生产线与
    软件生产线的"桥接集群"——输出既可被人类阅读，也可被机器消费。

spec:
  task_type: AgentClusterDesign
  cluster:
    name: "Technical Documentation Swarm"
    code: "CLUSTER-D"
    domain: "content_production.technical"

    guilds:
      # ===== Guild 1: Intent Structurer =====
      - id: INTENT_STRUCTURE
        name: 意图结构化 Guild
        agents:
          - role: RequirementsInterpreter
            description: >
              输入：会议纪要/用户故事/口头描述/设计草图描述/已有代码
              → 输出：结构化需求文档（PRD）
              
              提取步骤：
              ① 功能需求提取（用户能做什么）
              ② 非功能需求提取（性能/安全/兼容/可维护）
              ③ 约束条件提取（时间/预算/技术栈/合规）
              ④ 优先级排序（P0/P1/P2，含排序理由）
              ⑤ 隐含需求推理（用户没说但工程上必须的）
              
          - role: ScopeDefiner
            description: >
              定义文档范围和边界：
              - 明确本文档覆盖什么、不覆盖什么
              - 识别与其他文档的交叉引用关系
              - 生成术语表（统一全文用词）

        gate: INTENT_GATE
        gate_conditions:
          - "所有需求可追溯到原始输入 ✓"
          - "P0/P1/P2 优先级含明确理由 ✓"
          - "隐含需求推理已标注（区别于用户显式提出） ✓"

      # ===== Guild 2: Doc Writers =====
      - id: DOC_WRITERS
        name: 文档撰写 Guild
        agents:
          - role: ArchDocWriter
            description: >
              架构文档撰写：
              - 系统分层描述（展示层/业务层/数据层/基础设施）
              - 模块划分与接口定义
              - 技术选型与选型理由
              - 依赖拓扑（生成依赖关系图 ASCII/DSL）
              - 与 Design SOP 的 DesignSpec 保持一致性（自动比对）
              
              输入可来自：DesignSpec / API Schema / 代码仓库
              
          - role: AlgoSpecWriter
            description: >
              算法文档撰写：
              - 问题形式化定义（输入/输出/约束）
              - 算法描述（自然语言 + 伪代码 + 流程图）
              - 复杂度分析（时间复杂度/空间复杂度/通信复杂度）
              - 关键假设与边界条件
              - 替代方案对比（为什么选 A 而不是 B/C）
              
          - role: APIDocWriter
            description: >
              API 文档撰写：
              - 自动从代码 Schema/OpenAPI 提取端点定义
              - 生成：端点路径 + HTTP 方法 + 请求参数 + 响应格式 + 错误码
              - 为每个端点生成 2+ 代码示例（curl / Python / JS）
              - 认证机制说明
              
          - role: UserManualWriter
            description: >
              用户手册撰写：
              - 按用户角色（管理员/普通用户）分路径
              - 按场景组织（首次设置 / 日常使用 / 故障排除）
              - 截图/示意图标注需求（生成图片 Brief）
              - FAQ 自动聚合

        gate: DOC_GATE
        gate_conditions:
          - "架构文档与 DesignSpec 一致（自动比对） ✓"
          - "API 文档与代码 Schema 一致（自动比对） ✓"
          - "算法复杂度已标注且无遗漏 ✓"
          - "代码示例可运行（语法正确） ✓"

      # ===== Guild 3: Review =====
      - id: REVIEW
        name: 审阅与校验 Guild
        agents:
          - role: ConsistencyChecker
            description: >
              交叉校验各文档之间的一致性：
              - PRD 中的功能是否在架构文档中有对应模块？
              - API 文档的端点是否覆盖了 PRD 中所有数据需求？
              - 算法文档的接口是否与 API 文档一致？
          - role: TraceabilityChecker
            description: >
              需求可追溯性校验：
              PRD 需求 → 架构设计 → API 定义 → 代码实现 → 测试用例
              每个需求在整个链条中可正向追溯和反向追溯
          - role: SMEReviewer
            description: >
              领域专家审阅（高风险/核心模块强制人工）：
              - 安全相关模块强制人工审阅
              - 合规相关模块强制人工审阅
              - 算法核心逻辑强制人工审阅

        gate: REVIEW_GATE
        gate_conditions:
          - "一致性检查通过 ✓"
          - "需求可追溯性 100%（每个 PRD 需求能找到对应设计/代码） ✓"
          - "高风险模块人工 Sign-off ✓"

    integration:
      knowledge_cell:
        provider: CDO-DATA-001
        assets:
          - "架构模式库（分层/Microservices/Event-Driven 等）"
          - "算法模板库（基于数学建模类型学）"
          - "API 规范模板（OpenAPI/GraphQL/gRPC）"
          - "术语标准化映射（同义词→统一术语）"
      design_sop:
        provider: CDO-DESIGN-001
        interface: "消费 DesignSpec 作为输入 + 将 PRD 反馈为新的 SR 输入"
      software_line:
        interface: "产出的 PRD/Arch Doc 可直接被软件生产线的 Code Generator 消费"

    l2_configs:
      configs:
        - id: prd
          name: 产品需求文档
          key_differences: "需求→功能→优先级为主 + 可追溯性强制 + 输出可被 Design SOP 消费"
        - id: arch_doc
          name: 架构设计文档
          key_differences: "分层描述 + 与 DesignSpec 自动比对一致性"
        - id: algo_spec
          name: 算法设计说明
          key_differences: "复杂度必标注 + 伪代码 + 数学建模三闸门校验"
        - id: api_doc
          name: API 参考文档
          key_differences: "自动从代码生成 + Schema 一致性自动校验"
        - id: user_manual
          name: 用户手册
          key_differences: "按角色/场景组织 + 可读性优先 + FAQ 生成"

    workflow:
      type: "Sequential with Cross-Document Verification"
      description: "INTENT → DOC_WRITE → REVIEW。REVIEW 跨文档交叉校验"

    phases:
      - milestone: M1
        scope: "INTENT + PRD Writer + API Doc Writer + REVIEW（基础版）"
        target: "需求文档+API文档自动撰写"
      - milestone: M2
        scope: "+ Arch Doc + Algo Spec + User Manual + 全量交叉校验"
        target: "五类文档全覆盖 + 跨文档一致性自动校验"

  quality_requirement:
    min_cqs: 4.0
    must_pass:
      - "topology_check / role_uniqueness / message_protocol_check"
      - "consistency_check（文档与代码/Schema 自动比对）"
      - "traceability_check（需求→设计→代码可追溯）"
    golden_tests: 8
    acceptance:
      - "从一段会议纪要到完整 PRD + API 文档"
      - "PRD 的需求 100% 可追溯到原始输入"
      - "API 文档与代码 Schema 自动比对一致"

  sla:
    target_latency: "18h"
    max_latency: "48h"
    sla_level: "High"

consumer_notes:
  background: >
    技术文档集群是六套集群中唯一"桥接两个生产线"的——它产出的 PRD
    和架构文档可以直接进入软件生产线，使文字线和软件线形成无缝衔接。
    其核心差异化能力是"文档与代码一致性自动校验"——这是传统人工
    写文档最痛苦的维护环节。
