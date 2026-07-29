# ICM-SR: SR-TEXT-004
# 发送方: CDO-CONTENT → 接收方: CDO-DESIGN-001
# 优先级: P2
# 日期: 2026-06-15

request:
  id: SR-TEXT-004
  type: AgentClusterDesign
  priority: P2
  title: 创意转化智能体集群设计（文字生产线 · 集群 C）
  summary: >
    设计一套面向营销/广告/社交媒体场景的多 Agent 创意转化集群。
    核心逻辑是"转化优先"——从 Brief 到效果复盘形成完整闭环——
    追求 CTR/CVR/ROAS 等硬指标，而非文学质量。

spec:
  task_type: AgentClusterDesign
  cluster:
    name: "Creative Conversion Swarm"
    code: "CLUSTER-C"
    domain: "content_production.creative"

    guilds:
      # ===== Guild 1: Brief Parser =====
      - id: BRIEF_PARSE
        name: Brief 解析 Guild
        agents:
          - role: BriefInterpreter
            description: >
              解析 Brief（自然语言/结构化均可），提取 8 个关键维度：
              产品信息 / 目标受众 / 核心卖点 / 品牌调性 / 预算范围 /
              投放平台 / KPI 目标 / 禁忌与红线
              对缺失维度生成精准反问（不超过 3 个）
          - role: AudienceMatcher
            description: >
              将目标受众描述匹配到 Knowledge Cell 的受众 persona 库。
              输出：受众画像（年龄/兴趣/消费力/决策模式/内容偏好）
              + 平台匹配度（抖音 vs 小红书 vs 微信 vs Google）

        gate: BRIEF_GATE
        gate_conditions:
          - "8 维 Brief 完整度 ≥ 80%（缺的自动生成反问） ✓"
          - "受众 persona 匹配成功（置信 ≥ 0.7） ✓"

      # ===== Guild 2: Creative =====
      - id: CREATIVE
        name: 创意生成 Guild
        agents:
          - role: HookDesigner
            description: >
              基于受众画像 + 产品特性 + 平台特征，生成 3-5 个不同的"钩子"：
              - 好奇心钩子："这个电池的缺陷，花了 10 年才被发现"
              - 利益钩子："月省 ¥300 电费的秘密"
              - 恐惧钩子："90% 的人不知道自己的数据在裸奔"
              - 故事钩子："我们跟踪了一位外卖员 24 小时..."
          - role: CopyVariantGen
            description: >
              为每个 Hook 生成完整的文案变体：
              - 标题变体（3-5 个/每 Hook）
              - 正文变体（长短版）
              - CTA 变体（立即购买/了解更多/免费试用/限时优惠）
              - 视觉 Brief（供设计师/图片生成 Agent 使用）
          - role: CompetitorAnalyzer
            description: >
              检索竞品同类产品的文案策略：
              - 竞品在目标平台的投放内容采样
              - 提取竞品策略特征（情感诉求 vs 理性诉求 / 价格锚定 / 社交证明）

        gate: CREATIVE_GATE
        gate_conditions:
          - "≥ 3 个差异化 Hook ✓"
          - "每个 Hook 含完整文案 + CTA ✓"
          - "品牌调性合规（不违反 VI 规范） ✓"
          - "广告法合规（无禁用词/虚假宣传/比较广告违规） ✓"

      # ===== Guild 3: A/B Test =====
      - id: AB_TEST
        name: A/B 测试 Guild
        agents:
          - role: VariantDeployer
            description: >
              将 Creative Guild 产出的变体部署到目标平台进行小流量 A/B 测试。
              与数据内阁集成，自动创建投放实验。
          - role: StatAnalyzer
            description: >
              实时监控 A/B 测试数据回流，进行统计显著性判断：
              - CTR / CVR / CPC / ROAS 等核心指标
              - 样本量是否达到统计显著（p < 0.05）
              - 自动终止表现差的变体

        gate: AB_GATE
        gate_conditions:
          - "A/B 测试达到统计显著 ✓"
          - "至少 1 个变体 ROAS ≥ 目标值 ✓"

      # ===== Guild 4: Gate =====
      - id: FINAL_GATE
        name: 终审 Gate
        gate_conditions:
          - "品牌调性一致性 ✓"
          - "广告法 + 平台政策全合规 ✓"
          - "无侵犯第三方 IP（版权/商标/肖像权） ✓"
          - "目标受众匹配度 ≥ 0.7 ✓"

      # ===== Guild 5: Optimize =====
      - id: OPTIMIZE
        name: 优化与再创作 Guild
        agents:
          - role: PerformanceAnalyzer
            description: >
              分析投放效果数据，生成优化洞察：
              - 哪个 Hook 类型表现最好？→ 更新 Hook 偏好权重
              - 哪个受众群体转化率最高？→ 调优 AudienceMatcher
              - 哪个平台 ROAS 最优？→ 调整平台预算分配
          - role: CreativeRefresher
            description: >
              基于 PerformanceAnalyzer 的洞察，自动触发新一轮创作：
              - 保留高表现创意的核心要素
              - 替换疲劳素材（CTR 持续下降 → 触发刷新）
              - 生成新变体 → 回到 AB_TEST Guild

    integration:
      knowledge_cell:
        provider: CDO-DATA-001
        assets:
          - "受众 persona 库"
          - "竞品文案特征库（特征本体：Hook 类型/情感诉求/CTA 模式）"
          - "平台算法特征（各平台的内容推荐机制差异）"
          - "广告法规则库 + 禁用词列表"
      data_agent:
        services:
          - "情报挖掘：竞品投放素材采集 + 策略特征提取"
          - "数据反馈：CTR/CVR/ROAS 实时回流"
          - "A/B 实验框架集成"

    l2_configs:
      configs:
        - id: feed_ad
          name: 信息流广告
          key_differences: "强 Hook 前置（前 3 秒/前 15 字决胜负）+ 单 CTA"
        - id: brand_copy
          name: 品牌文案
          key_differences: "调性优先于转化 + 品牌 VI 严格校验 + 长线叙事"
        - id: social_media
          name: 社交媒体内容
          key_differences: "互动优先 + 平台格式适配 + 蹭热点能力"
        - id: email_marketing
          name: 邮件/私域营销
          key_differences: "个人化 + 分段叙事 + 软 CTA + GDPR/CAN-SPAM 合规"

    workflow:
      type: "Sequential with Optimization Loop"
      description: "BRIEF → CREATIVE → AB_TEST → GATE → 投放 → OPTIMIZE → 回到 CREATIVE"

    phases:
      - milestone: M1
        scope: "BRIEF + CREATIVE + GATE"
        target: "从 Brief 到合规文案交付"
      - milestone: M2
        scope: "+ AB_TEST + OPTIMIZE"
        target: "A/B 测试 + 效果驱动自动再创作"

  quality_requirement:
    min_cqs: 3.5
    must_pass:
      - "topology_check / role_uniqueness / message_protocol_check"
      - "compliance_check（广告法 + 平台政策全覆盖）"
      - "creative_diversity（同一 Brief ≥ 3 个差异化方向）"
    golden_tests: 6
    acceptance:
      - "一份真实 Brief → 3 个差异化完整文案"
      - "AB Test 自动运行并产出统计显著结论"
      - "低表现变体自动终止，新变体自动生成"

  sla:
    target_latency: "12h"
    max_latency: "36h"
    sla_level: "High"

consumer_notes:
  background: >
    创意转化集群是六套集群中与数据反馈结合最紧密的一套——
    A/B → 数据回流 → 优化 → 再创作形成自驱动闭环。
    它也是 OMAS 体系中"内生能力可商品化对外盈利"的典型。
