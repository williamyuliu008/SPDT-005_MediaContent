# ICM-SR: SR-TEXT-002
# 发送方: CDO-CONTENT（文字产品域） → 接收方: CDO-DESIGN-001
# 优先级: P0
# 日期: 2026-06-15

request:
  id: SR-TEXT-002
  type: AgentClusterDesign
  priority: P0
  title: 深度生产智能体集群设计（文字生产线 · 集群 B）
  summary: >
    设计一套面向深度文字产品（研报/行业分析/政策解读/时政分析/学术综述/
    调查报道/企业尽调/产业规划）的多 Agent 协同创作集群。
    该集群是六套文字生产集群中价值最高、工作流最复杂的一套，
    需要在无人类微操下完成从选题发现到审阅交付的完整闭环。

# ============================================================
# 功能规格
# ============================================================
spec:
  task_type: AgentClusterDesign

  input:
    description: >
      该集群接收来自 SR-TEXT-001（分类智能体）的结构化创作指令，
      或直接接收人工提交的创作任务。
      
      输入格式（由分类智能体产出）：
      {
        "structured_spec": { ... },     # 10 维结构化需求
        "configuration": {              # L2 配置信息
          "config_name": "equity_research",  # 或 industry_analysis / policy_analysis 等
          "parameter_overrides": { ... }
        }
      }
      
      输入示例：
      - 股票研报："宁德时代深度研报，覆盖产业链定位、财务模型、
        竞争格局、风险提示，面向机构投资者，2万字"
      - 行业分析："中国半导体设备国产化进程分析，含技术路线对比、
        政策梳理、主要玩家评估，面向产业决策者"
      - 政策解读："新型电力系统建设方案逐条解读，含影响推演、
        受益标的、时间节奏，面向投资人与电力从业者"
      - 调查报道："某上市公司财务疑点调查，含多方信源交叉验证、
        实地调研记录、专家访谈摘要"
    format: JSON（来自 SR-TEXT-001）或自然语言（直接提交）
    complexity: "高——需要多源信息采集、定量建模、多轮验证、风格适配"

  # ==========================================================
  # 集群设计需求
  # ==========================================================
  cluster:
    name: "Deep Production Swarm"
    code: "CLUSTER-B"
    domain: "content_production.deep"

    # ----- 角色核心要求 -----
    roles:
      general:
        - "所有 Agent 之间通过 MessageBus 通信，Operator Agent 负责全局调度"
        - "每个 Guild 内部可有多个并行 Agent 实例（如同时采集多个信源）"
        - "Agent 不直接调用下游 Agent，通过 Gate Agent 的 Artifact 传递"
        - "所有 Agent 的工具调用记录写入决策日志（Decision Log）"

    # ----- Guild 详设 -----
    guilds:

      # ===== Guild 1: Scout & Topic =====
      - id: SCOUT_TOPIC
        name: 选题与侦查 Guild
        description: 发现值得写的选题，评估选题价值，定义研究角度
        
        agents:
          - role: GapAnalyzer
            description: >
              分析目标领域已有的内容覆盖情况，识别信息缺口。
              输入：领域关键词 + Knowledge Cell 中的竞品覆盖数据
              输出：缺口分析报告（含缺口类型：时效缺口/角度缺口/深度缺口/数据缺口）
              
          - role: AngleFinder
            description: >
              基于缺口分析，生成 3-5 个可行的创作角度。
              每个角度含：核心论点、目标受众匹配度、证据可获得性预估、差异化程度
              
          - role: ValueEstimator
            description: >
              对每个候选角度进行价值量化：
              - 时效价值：信息新鲜度半衰期
              - 受众价值：目标受众规模 × 需求强度
              - 差异化价值：与已有内容的差异程度
              - 复用价值：能否衍生为系列/短视频/播客等
              输出：排序后的选题推荐列表

        gate: SCOUT_GATE
        gate_conditions:
          - "至少产出 3 个候选角度 ✓"
          - "每个角度含价值量化 ✓"
          - "缺口分析基于真实数据（非 LLM 臆测） ✓"
        on_gate_fail: "退回 GapAnalyzer 补充数据或降低候选数阈值"

      # ===== Guild 2: Research =====
      - id: RESEARCH
        name: 调研与建模 Guild
        description: 多渠道信息采集、结构化整理、定量建模
        
        agents:
          - role: SourceCollector
            description: >
              按选题需要，从多个渠道并行采集信息：
              - 数据内阁 DSP 原语：financial/valuation/*, financial/stock/* 等
              - 公开网页采集（Scout Agent 模式，参考 SOP-64）
              - 结构化数据库查询（财报、专利、临床试验等）
              - 专家访谈纪要（如有人工提供）
              
              对每条信息标注：来源、可信度、时效性、与选题的相关度
              
          - role: DataCurator
            description: >
              对 SourceCollector 的原始采集结果进行整理：
              - 去重：同一事实多源报道 → 标记所有源
              - 口径对齐：不同来源的同一指标（如"营收"定义差异）→ 标注差异
              - 时序编排：按时间维度排列事件/数据
              - 矛盾标记：不同源数据矛盾 → 标记为待验证
              
          - role: Modeler
            description: >
              当选题需要定量分析时（财务模型、市场预测、技术参数对比等），
              调用建模模板进行定量建模。继承数据内阁的数学建模类型学：
              - 财务建模：DCF/可比公司/情景分析（三闸门自动校验）
              - 技术参数矩阵：多产品 × 多维度对比
              - 市场规模测算：自上而下/自下而上/类比法
              
          - role: FactVerifier
            description: >
              对关键事实声明进行交叉验证：
              - 数值类：多源比对（偏差 ≤ 阈值则通过）
              - 事件类：至少 2 个独立信源确认
              - 引用类：验证原始出处是否存在、是否被曲解

        gate: RESEARCH_GATE
        gate_conditions:
          - "所有关键事实 ≥ 1 条可溯源证据 ✓"
          - "数值类数据偏差验证通过 ✓"
          - "建模假设文档化（记录所有假设及理由） ✓"
          - "信源多样性：至少来自 3 类不同渠道 ✓"
        on_gate_fail: "标记缺口 → 触发 AIGC 主动补采 → 重新验证"

      # ===== Guild 3: Structure & Write =====
      - id: STRUCTURE_WRITE
        name: 架构与撰写 Guild
        description: 搭建文章框架、分段撰写、生成图表、管理引用
        
        agents:
          - role: OutlineBuilder
            description: >
              根据选题和 collected_data，搭建文章结构：
              - 确定叙事框架（问题→分析→结论 / 总→分→总 / 时间线 / 对比）
              - 生成章节大纲（每章含：核心论点 + 支撑证据 + 预估字数）
              - 标注各章的"必含要素"（如财务分析必须含三表摘要）
              
          - role: NarrativeWriter
            description: >
              按大纲逐章撰写正文：
              - 开头：钩子设计 + 核心问题陈述
              - 主体：论点→证据→解读→过渡
              - 结尾：结论 + 展望 + 风险提示
              
              写作约束（由 L2 配置注入）：
              - 风格：数据驱动 / 叙事为主 / 论证导向
              - 语气：客观中立 / 谨慎乐观 / 批判性
              - 长度：按深度要求控制
              - 可读性：专业内容 + 过渡段 + 小结
              
          - role: Visualizer
            description: >
              为文章生成配套图表：
              - 数据图表：折线/柱状/饼图/热力图
              - 关系图：产业链/竞争格局/流程图
              - 对比表：多维度对比矩阵
              - 时间线：事件发展时间轴
              
          - role: CitationManager
            description: >
              管理全文引用：
              - 自动生成脚注/尾注/参考文献
              - 确保每个数据声明后附源标注
              - 引用格式按配置切换（APA/GB/自定义）

        gate: WRITE_GATE
        gate_conditions:
          - "结构与 Outline 一致 ✓"
          - "每章核心论点有 ≥ 1 条证据支撑 ✓"
          - "数据声明后有源标注 ✓"
          - "图表数据与正文一致 ✓"
          - "未引入 Research Guild 未采集的新事实（防幻觉） ✓"
        on_gate_fail: "标记失败章节 → NarrativeWriter 重写 → 重过 Gate"

      # ===== Guild 4: Review =====
      - id: REVIEW
        name: 审阅与品控 Guild
        description: 逻辑自洽检查、证据溯源、偏见检测、首席签批
        
        agents:
          - role: LogicChecker
            description: >
              逐段检查逻辑：
              - 循环论证检测
              - 偷换概念检测
              - 因果倒置检测
              - 以偏概全检测
              - 滑坡谬误检测
              
          - role: EvidenceTracer
            description: >
              反向溯源每个关键论断的证据链：
              论断 → 正文证据 → 原始数据源 → 数据采集记录
              无法溯源的论断标记为"待补充证据"
              
          - role: BiasDetector
            description: >
              检测内容中的偏见：
              - 选择性呈现（只选有利证据，忽略不利）
              - 框架偏差（用特定叙事框架扭曲事实）
              - 确认偏差（只找支持预设结论的证据）
              - 情感倾向（过度使用褒义/贬义词汇）
              
          - role: ChiefReviewer
            description: >
              综合审阅：
              - 整体质量评分（CQS ≥ 4.0）
              - 是否达到发布标准
              - 是否需要人工审阅（高风险配置时强制）
              - 批准 / 退回修改 / 否决

        gate: REVIEW_GATE
        gate_conditions:
          - "逻辑自洽（无循环论证/偷换概念/因果倒置） ✓"
          - "所有关键论断可溯源至原始数据 ✓"
          - "偏见检测通过（偏差指数 < 阈值） ✓"
          - "CQS ≥ 4.0 ✓"
          - "高风险配置（时政/调查报道）→ 强制人工 Sign-off ✓"
        on_gate_fail: "逐条标注失败原因 → 退回对应 Guild 修改 → 重新走 Gate"

      # ===== Guild 5: Distribution =====
      - id: DISTRIBUTION
        name: 分发与适配 Guild
        description: 多格式、多渠道、多权限分发
        
        agents:
          - role: FormatAdapter
            description: >
              将 Markdown 原稿适配为目标格式：
              - PDF（正式研报格式，含封面/目录/免责声明）
              - HTML（Web 发布）
              - 公众号（适配微信编辑器）
              - PPT（提取关键图表和核心结论）
              
          - role: ChannelRouter
            description: >
              根据内容类型和权限配置，路由到发布渠道：
              - 内部平台（全员可见）
              - 客户平台（按订阅等级）
              - 公开平台（网站/公众号/社交媒体）
              - API 交付（结构化数据给下游系统）
              
          - role: MetadataTagger
            description: >
              自动生成元数据：
              - SEO 标签 / 分类标签 / 相关文章推荐
              - 摘要（50字/200字/500字三档）
              - 关键词提取

    # ----- 集成要求 -----
    integration:
      knowledge_cell:
        provider: CDO-DATA-001
        assets:
          - "受众 persona 库（目标读者画像）"
          - "竞品内容库（已有覆盖分析）"
          - "领域本体（术语定义、行业分类、指标口径）"
          - "特征本体（爆款特征、叙事模式、证据强度模式）"
          - "建模模板库（财务模型、技术参数矩阵、市场测算）"
          - "信源可信度评分"
          - "Red Flag 词库（合规审查用）"
      
      data_agent:
        provider: CDO-DATA-001
        services:
          - "情报挖掘：竞品覆盖空白侦测（SOP-64 自发探索模式）"
          - "数据采集：DSP 原语调用（financial/valuation/*, financial/stock/*）"
          - "数据反馈：发布后 CTR/阅读时长/互动数据回流"
          - "Detective Agent：数据源心跳监控 + 异常告警"
      
      classification_agent:
        provider: SR-TEXT-001（待开发）
        interface: "接收分类智能体的结构化创作指令作为输入"

    # ----- L2 配置文件体系 -----
    l2_configs:
      description: >
        同一套集群拓扑，通过 8 份 L2 配置文件适配不同产品类型。
        配置文件在集群启动时加载，影响：
        - 各 Guild 的 system prompt 模板
        - Knowledge Cell 的检索子集
        - Gate 阈值和特殊规则
        - 合规审查的 Red Flag 规则集
      configs:
        - id: equity_research
          name: 股票/公司深度研报
          key_differences: "强制财务建模 + 估值三闸门 + 风险提示模板"
          
        - id: industry_analysis
          name: 行业分析报告
          key_differences: "产业链图谱 + 竞品矩阵 + 波特五力/PEST框架"
          
        - id: policy_analysis
          name: 政策解读
          key_differences: "政策逐条拆解 + 影响推演模板 + 受益标的识别"
          
        - id: political_analysis
          name: 时政分析
          key_differences: "≥3 立场信源 + narrative bias 标注 + 强制人工审批 + 因果链图"
          
        - id: academic_survey
          name: 学术/文献综述
          key_differences: "文献覆盖 ≥ 80% + 引用网络图 + 研究空白标注"
          
        - id: investigative_report
          name: 调查报道
          key_differences: "多源交叉验证 + 实地记录 + 专家访谈 + 强制人工审批"
          
        - id: due_diligence
          name: 企业/项目尽调报告
          key_differences: "尽调清单模板 + 风险矩阵 + 合规审查增强"
          
        - id: industry_planning
          name: 产业规划/白皮书
          key_differences: "长周期视角 + 多情景推演 + 政策建议模板"

    # ----- 工作流定义 -----
    workflow:
      type: "Sequential Chain with Feedback Loops"
      description: >
        默认串行：SCOUT → RESEARCH → WRITE → REVIEW → DISTRIBUTE
        
        反馈回路：
        - REVIEW_GATE 失败 → 退回对应 Guild（可退到 RESEARCH 或 WRITE）
        - RESEARCH_GATE 失败 → 触发 AIGC 主动补采 → 回到 RESEARCH
        - DISTRIBUTION 后 → Analytics 数据回流 → 更新 Knowledge Cell
      exception_handling:
        - "任何 Guild 超时（超过 SLA）→ 降级策略：跳过非关键 Guild，用规则引擎兜底"
        - "LLM 调用失败 → 自动切换备用模型 → 仍失败则 escalate 到人工"
        - "数据源不可用 → 标记数据缺口 → AIGC 尝试替代源 → 仍缺则在交付中声明限制"

    # ----- 分期策略 -----
    phases:
      - milestone: M1（核心链路）
        scope: "SCOUT + RESEARCH + WRITE + REVIEW_GATE（基础版）"
        target: "跑通一篇标准研报从选题到审阅交付"
        validation: "人类未参与选题、调研、撰写、审阅——仅 Gate 审批"
        
      - milestone: M2（完整集群）
        scope: "+ LogicChecker + BiasDetector + DISTRIBUTION"
        target: "完整的质量控制 + 多渠道分发"
        
      - milestone: M3（全配置覆盖）
        scope: "+ 8 份 L2 配置的全部实现 + 时政分析的高风控 Gate"
        target: "一套集群拓扑覆盖 8 种深度文字产品"

# ============================================================
# 质量要求
# ============================================================
  quality_requirement:
    min_cqs: 4.0
    must_pass:
      - "topology_check"              # 拓扑合法性
      - "role_uniqueness"             # 角色不重叠
      - "message_protocol_check"      # 消息协议完整性
      - "gate_condition_check"        # Gate 条件可验证
      - "workflow_completeness"       # 覆盖正常+异常+超时路径
      - "l2_config_isolation"         # 8 份配置独立可切换
    golden_tests: 10
    acceptance_criteria:
      - "用一份真实研报需求跑通全流程（M1 验收）"
      - "人类仅出现在 Vision（提交需求）和 REVIEW_GATE（审批）"
      - "内容质量达到中级分析师水平（CQS ≥ 4.0）"
      - "证据溯源链完整（每个数据声明可追溯到原始信源）"
      - "8 份 L2 配置全部可加载且 Gate 条件不同"

# ============================================================
# SLA
# ============================================================
  sla:
    target_latency: "24h"             # 集群设计本身的目标
    max_latency: "72h"
    quality_bar: "cqs >= 4.0"
    sla_level: "Deep"
    retry_policy:
      max_retries: 2
      backoff: "exponential"

# ============================================================
# 下单方备注
# ============================================================
consumer_notes:
  background: >
    文字作品生产线规划了 6 套集群。其中集群 B（深度生产集群）
    是价值最高、覆盖产品最广的一套——8 份配置覆盖研报、行业分析、
    政策解读、时政分析、学术综述、调查报道、企业尽调、产业规划。
    
    选择这套集群作为首个开发的文字生产集群，原因：
    1. 最复杂 → 做通了能验证完整方法论
    2. 附加值最高 → 深度内容有定价权
    3. 覆盖最广 → 一套集群服务 8 种产品
    
    该集群需要深度集成数据内阁的 Knowledge Cell（领域本体/
    信源评分/建模模板）和情报挖掘能力（竞品覆盖/自发探索）。
    
    之前设计内阁已经完成了 MVS 七角色集群（SR-20260530-001，
    7 分钟交付），这个集群的复杂度与之相当（5 Guild × 19 Agent），
    但有更多 L2 配置文件需要设计。
  
  existing_assets:
    - "附录C-文字作品生产线规划 §三-集群B（Guild/Agent/配置详细定义）"
    - "附录B-数据内阁数据生产线评估（Knowledge Cell 能力基准）"
    - "SR-20260530-001（设计内阁首单交付，可复用设计经验）"
  
  related_designs:
    - "SR-TEXT-001（分类智能体）—— 本集群的上游路由器"
    - "SR-TEXT-003~007（后续其他 5 套集群，待本集群验证后启动）"
  
  contact: "Meta-Agent-Content"
  urgency: "P0——文字生产线的核心集群，优先启动"
