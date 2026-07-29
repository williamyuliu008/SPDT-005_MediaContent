# SPDT-005：媒体内容制造

> Media Content Manufacturing | 7 PDT · SmartText 路由 · 全渠道分发

## 一句话定位

从数据源到成品文章的一键转化——覆盖深度长文、实时快讯、知识科普、观点评论、品牌创意和技术文档的全媒体矩阵。

## 核心理念

**内容即产品。** 通过 SmartText 路由引擎对自然语言需求做 10 维结构化，然后精准分派到最适合的 PDT 集群，实现不同内容类型的专业化自动生产。

## 覆盖领域

| PDT | 内容类型 | 受众 | 当前状态 |
|---|---|---|---|
| PT-040 深度长文 | 深度分析/行业报告 | 专业人士 | 运行中（DeepProd 6 Stage） |
| PT-041 实时快讯 | 短新闻/动态 | 大众 | 运行中（FlashNews 4 Stage） |
| PT-042 知识科普 | 科普文章/图解 | 大众 | 运行中（SciPop 4 Stage） |
| PT-043 观点评论 | 评论/社论 | 思想读者 | 运行中（OpEd 4 Stage） |
| PT-044 品牌创意 | 广告/社媒/文案 | 品牌方 | 运行中（CreativeX 4 Stage） |
| PT-045 技术文档 | API 文档/技术手册 | 开发者 | 运行中（TechDoc 4 Stage） |
| PT-046 数据新闻 | 数据驱动报道 | 大众 | 规划中 |

## 技术架构

```
NL 需求 / 数据源
  → TextClassifier (10维结构化)
  → PDT 路由 (6 集群匹配)
  → 内容加工 (多 Stage 管道)
  → 质量门禁 (事实核查 + 风格校验)
  → autopublish 分发 (飞书/微信/网站)
```

详见 [docs/architecture.md](docs/architecture.md)

## 快速链接

- [SPDT.yaml](SPDT.yaml) — 产品线注册信息
- [MANAGEMENT.md](MANAGEMENT.md) — 管理规范
- [pdt-registry.yaml](pdt-registry.yaml) — PDT 详细注册表
