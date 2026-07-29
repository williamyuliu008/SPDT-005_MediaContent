# ICM-SR: SR-TEXT-003
# 发送方: CDO-CONTENT → 接收方: CDO-DESIGN-001
# 优先级: P1（仅次于 SR-TEXT-002）
# 日期: 2026-06-15

request:
  id: SR-TEXT-003
  type: AgentClusterDesign
  priority: P1
  title: 实时快反智能体集群设计（文字生产线 · 集群 A）
  summary: >
    设计一套面向高时效文字产品（新闻快讯/市场速报/科技快讯/体育赛报/
    天气预警）的多 Agent 协同创作集群。速度优先——从事件触发到内容发布
    目标分钟级——在"快"的约束下最大化准确性和信息密度。

spec:
  task_type: AgentClusterDesign
  cluster:
    name: "Rapid Response Swarm"
    code: "CLUSTER-A"
    domain: "content_production.rapid"

    # ===== Guild 1: Source & Sensing =====
    guilds:
      - id: SOURCE_SENSING
        name: 信源感知 Guild
        description: 7×24 监测信源，自动分级，过滤噪音
        
        agents:
          - role: HotspotMonitor
            description: >
              持续监听多个信源（RSS/API/社交媒体/数据内阁情报挖掘），
              对事件进行自动分级：
              - 🔴 突发：地震/恐袭/熔断/重大政策（需 3min 内响应）
              - 🟠 重要：财报发布/产品发布/人事变动（需 15min 内响应）
              - 🟡 常规：行业动态/公司新闻/数据更新（需 30min 内响应）
              - ⚪ 噪音：过滤
              
          - role: SourceTriage
            description: >
              对 HotspotMonitor 标记的事件进行首次信源评估：
              - 信源可信度查询（Knowledge Cell：信源评分）
              - 同一事件的多源报道聚合
              - 标记"需核实"vs"可快写"的事件特征

        gate: SENSING_GATE
        gate_conditions:
          - "🔴 突发事件 3min 内完成分级 ✓"
          - "信源评分 ≥ 0.6（可信），否则标记为需核实 ✓"

      # ===== Guild 2: Verify =====
      - id: VERIFY
        name: 核实 Guild
        description: 多源交叉验证 + 谣言检测
        
        agents:
          - role: FactCrossChecker
            description: >
              对关键事实进行多源交叉验证：
              - 至少 2 个独立信源确认同一事实
              - 信源之间的独立性评估（同一集团的不同媒体不算独立源）
              - 验证失败的降级策略：标记为"未经独立核实"并限缩传播范围
              
          - role: RumorDetector
            description: >
              对信息进行谣言特征检测：
              - 情绪化措辞（"震惊""传疯了"等）
              - 缺乏具体时间/地点/人物
              - 信源匿名或不可追溯
              - 与历史已知谣言的文本相似度

        gate: VERIFY_GATE
        gate_conditions:
          - "🔴 突发：≥ 2 个独立信源 ✓"
          - "🟠 重要：≥ 1 个可信信源（评分 ≥ 0.8） ✓"
          - "谣言检测清除（无 Red Flag 命中） ✓"
        on_gate_fail: "延迟发布 + 标记'正在核实' + 仅限内部可见"

      # ===== Guild 3: Write =====
      - id: WRITE
        name: 快写 Guild
        description: 结构化模板填充，目标是"准确 + 够快"
        
        agents:
          - role: QuickWriter
            description: >
              按事件类型匹配写作模板：
              - 新闻快讯：倒金字塔（最重要→次重要→背景）
              - 市场速报：数字驱动（关键指标→变动幅度→原因→影响）
              - 体育赛报：结果→关键节点→数据→点评
              - 天气预警：预警级别→影响范围→持续时间→应对建议
              
              模板由 L2 配置注入，QuickWriter 做结构化填充
              
          - role: TemplateFiller
            description: >
              将交叉验证后的事实填入模板：
              - 5W1H 核心要素提取
              - 自动生成标题（≤ 20 字，含核心信息）
              - 自动生成摘要（≤ 100 字，含关键数据）

        gate: WRITE_GATE
        gate_conditions:
          - "5W1H 全部填充 ✓"
          - "标题含核心信息 ✓"
          - "篇幅符合配置的深度要求 ✓"

      # ===== Guild 4: Gate =====
      - id: FINAL_GATE
        name: 终审 Gate
        description: 发布前的最后一道防线
        
        gate_conditions:
          - "所有声明的事实已通过 VERIFY_GATE ✓"
          - "无诽谤/泄密/违规措辞（Compliance Red Flag 词库） ✓"
          - "无歧视性/煽动性语言 ✓"
          - "从事件触发到 Gate 通过 < SLA（🔴3min / 🟠15min / 🟡30min） ✓"

      # ===== Guild 5: Publish & Monitor =====
      - id: PUBLISH_MONITOR
        name: 发布与追踪 Guild
        description: 多平台发布 + 传播效果追踪
        
        agents:
          - role: MultiChannelPublisher
            description: >
              自动适配各平台格式并发布：
              - Web：HTML + SEO 元数据
              - App Push：≤ 50 字推送文案
              - 社交媒体：适配各平台字数/格式限制
              - 邮件：Newsletter 格式
              
          - role: ImpactTracker
            description: >
              追踪发布后效果，数据回流至 Knowledge Cell：
              - 阅读量/UV/PV 分钟级回流
              - 互动数据（评论/分享/收藏）
              - 传播路径追踪
              - 重大舆情反转检测（自动触发更正流程）

    # ===== 集成 =====
    integration:
      knowledge_cell:
        provider: CDO-DATA-001
        assets:
          - "信源可信度评分（基于历史准确率，CrossValidator 模式）"
          - "历史谣言库（文本相似度匹配）"
          - "写作模板库（各事件类型的结构化模板）"
          - "Red Flag 词库（合规/诽谤/歧视检测）"
      data_agent:
        provider: CDO-DATA-001
        services:
          - "情报挖掘：热点趋势实时监控 + 异常事件检测"
          - "数据反馈：传播效果实时回流"
      classification:
        provider: SR-TEXT-001
        interface: "接收分类智能体的结构化指令（含深度=快讯级、时效=分钟级等标记）"

    # ===== L2 配置 =====
    l2_configs:
      configs:
        - id: breaking_news
          name: 综合新闻快讯
          key_differences: "5W1H 模板 + 倒金字塔结构 + 信源 ≥ 2 独立"
        - id: market_flash
          name: 金融市场速报
          key_differences: "数字驱动 + 关键指标模板 + 数据内阁 DSP 自动提取行情数据"
        - id: tech_brief
          name: 科技行业快讯
          key_differences: "技术术语库 + 公司产品关系图检索"
        - id: sports_live
          name: 体育赛事快报
          key_differences: "赛事数据模板 + 关键节点自动检测 + 历史对阵检索"
        - id: weather_alert
          name: 天气/灾害预警
          key_differences: "预警分级模板 + 影响范围地理标注 + 应对建议自动生成"

    workflow:
      type: "Straight Pipeline"
      description: "SOURCE → VERIFY → WRITE → GATE → PUBLISH。无反馈回路（速度优先），异常降级而非重做"

    phases:
      - milestone: M1
        scope: "SOURCE + WRITE + GATE（基础快写链路）"
        target: "5W1H 填充 + 单信源 + 人类 Gate 审批"
      - milestone: M2
        scope: "+ VERIFY（交叉验证）+ PUBLISH_MONITOR"
        target: "多信源验证 + 多平台自动发布"

  quality_requirement:
    min_cqs: 3.5
    must_pass:
      - "topology_check / role_uniqueness / message_protocol_check"
      - "timeliness_sla（分级 SLA 机制可验证）"
      - "accuracy_degradation（速度优先下的准确率底线 ≥ 95%）"
    golden_tests: 8
    acceptance:
      - "使用一条真实突发新闻跑通全流程"
      - "从事件触发到内容发布 ≤ 5min"
      - "人类仅出现在监测启动和异常升级"

  sla:
    target_latency: "12h"
    max_latency: "36h"
    sla_level: "High"

consumer_notes:
  background: >
    六套文字集群中，实时快反集群是最简单但最考验"速度-准确"平衡的。
    它的 Guild 结构不同于深度生产——没有 Research 和 Review 的
    深度环节，工作流是单向流水线（不做反馈回路，异常降级而非重做）。
  related:
    - "SR-TEXT-001（分类智能体——上游）"
    - "SR-TEXT-002（深度生产集群——互补，快反提供选题线索）"
