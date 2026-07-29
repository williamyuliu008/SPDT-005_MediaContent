# SPDT-005 管理规范

> 版本: v1.0 | 生效: 2026-07-10
> 适用范围: 媒体内容制造产品线 (7 PDT)

## 一、PDT 生命周期

```
提议 → 注册 → 开发 → 验收 → 运行 → 扩张
  │                        │
  └── 驳回                  └── 退役/合并
```

### 注册条件
1. 明确的媒体定位（受众 / 内容类型 / 发布频率，与现有 PDT 不重叠）
2. 指定 PDT 负责人
3. PDT.yaml 就位（领域定义 + 内容规范 + 发布渠道）
4. 首篇试生产通过质量门禁（事实核查 + 风格一致性均 ≥80%）

### 验收标准
1. 端到端管线可运行（路由 → 加工 → 审核 → 发布）
2. 连续 10 篇自动产出（质量门禁通过率 ≥90%）
3. 发布渠道对接完成（至少 1 个渠道）
4. 编辑 Review 工作流就位（人工兜底）

### 退役条件
- 连续 30 天无产量
- 或合并到更成熟 PDT

## 二、目录规范

```
SPDT-005_MediaContent/
├── README.md                # 产品线概览
├── SPDT.yaml                # SPDT 注册 + PDT 清单
├── MANAGEMENT.md             # 本文件
├── pdt-registry.yaml        # PDT 详细注册表
├── docs/                    # 跨 PDT 文档
│   └── architecture.md      # 总体架构
├── pdt/                     # PDT 注册文件
│   └── {PT-ID}/
│       └── PDT.yaml         # PDT 快照
├── shared/                  # 共享引擎
│   └── smarttext_router/    # 路由器 + 6 集群核心
├── common/                  # 公共模块
│   ├── fact_checker/        # 事实核查引擎
│   ├── style_guide/         # 风格指南引擎
│   └── seo_tools/           # SEO 优化工具
├── channels/                # 发布通道配置
│   ├── feishu/
│   ├── wechat_mp/
│   └── website/
├── templates/               # 文风包 & 结构模板
│   ├── deep_prod/           # 深度长文模板
│   ├── flash_news/          # 快讯模板
│   ├── scipop/              # 科普转化模板
│   ├── oped/                # 论证结构模板
│   ├── creativex/           # 创意文案模板
│   └── techdoc/             # 技术文档模板
└── PT-0XX_{Name}/           # 各 PDT 独立目录
    ├── README.md
    ├── PDT.yaml
    ├── config/              # 领域配置
    ├── output/              # 内容产出
    └── reports/             # 质量报告
```

## 三、PDT 间协作规则

### 共享路由 (shared/smarttext_router/)
- 统一入口：所有内容需求通过 TextClassifier 10 维结构化 → 路由到对应 PDT
- 路由器由 SPDT owner 统一维护，PDT 不得私自修改分派逻辑
- 新增 PDT 需在 router/ 注册其分类特征

### 风格一致性
- 每个 PDT 定义自己的风格配置（语调/文风/结构模板），在 templates/ 下维护
- 跨 PDT 复用：如 TechDoc 可复用 SciPop 的"通俗化转化"模块
- 风格一致性由 content_quality_gate 的 style_check 模块兜底

### 发布节奏
- PT-041 (FlashNews)：实时，监测 → 15 分钟内撰稿 → 自动发布
- PT-040 (DeepProd)：日更或周更，6 Stage 全流程
- PT-042/043/044/045：日更或按需
- 所有 PDT 共享 channels/ 下的发布配置

## 四、当前 PDT 负责人

| PDT | Agent | 状态 | 成熟度 |
|---|---|---|---|
| PT-040 DeepProd | agent-e926h | 运行中 | 60% |
| PT-041 FlashNews | agent-e926h | 运行中 | 50% |
| PT-042 SciPop | agent-e926h | 运行中 | 30% |
| PT-043 OpEd | agent-e926h | 运行中 | 25% |
| PT-044 CreativeX | agent-e926h | 运行中 | 25% |
| PT-045 TechDoc | agent-e926h | 运行中 | 35% |
| PT-046 DataNews | — | 规划中 | — |

## 五、日常运营

### 内容日历
- PT-040：日更（深度长文 1 篇 / 天）
- PT-041：实时触发（无限量，自动发布）
- PT-042/045：日更（各 1-2 篇 / 天）
- PT-043/044：周更（各 3-5 篇 / 周）

### 质量门禁日检
- daily cron：全 PDT 最新产出抽样质检
- 检查项：事实核查 / 风格一致性 / 原创度 / 合规
