# SPDT-005 媒体内容 SOP v1.1
## 元结构：弹性供应链型管线

---

## 1. 核心设计理念

SPDT-005 媒体内容管线**不是一条刚性装配线**，而是一套**弹性供应链**。

| 对比维度 | SPDT-004 教育管线 | SPDT-005 媒体管线 |
|:---|:---|:---|
| 类比 | 刚性装配线 | 弹性供应链 |
| 输入差异 | 科目不同（语文/数学/历史） | 内容类型不同（快讯/报告/科普/评论） |
| 管线行为 | 同一套固定工序序列 | 同一套阶段名，内部模块按类型动态切换 |
| 复杂性来源 | 知识内容本身的复杂度 | 准确性 × 文学性 × 专业性 × 渠道组合 |
| SOP 形态 | 一套固定工序 | **元结构**（工序选择器 + 内容类型注册表） |
| 交付视角 | 交付知识内容 | 交付**内容产品**（文字+元数据+排版+渠道适配） |

---

## 2. 元结构总览

```
ContentSpec (content_type)
        │
        ▼
┌─────────────────────────────┐
│   pipeline_router.py         │  ← 读取 content_type
│   (管线路由器)               │     查询 registry
└──────────┬──────────────────┘
           │ content_type → route
           ▼
┌─────────────────────────────┐
│  content_type_registry.yaml │  ← mini-SOP 定义表
│  (内容类型注册表)            │     每种类型定义：
└──────────┬──────────────────┘     · 阶段模块路径
           │ route                  · 三维分类（准确性/文学性/专业性）
           ▼                       · 质量阈值
    ┌──────────────────────────┐   · 人类检查点策略
    │  1_ingest ───────────────┼─→ radar.breaking / radar.industry / smartext / ...
    │  2_structure ────────────┼─→ article / genre / knowledge_graph / ...
    │  3_render ───────────────┼─→ engines/text.[engine_a / engine_b / ...]
    │  4_adapt ────────────────┼─→ scorecard / agent_templates / orchestration
    │  5_deliver ──────────────┼─→ publish.[fast / standard / multi_channel]
    └──────────────────────────┘
           │
           ▼
    人类检查点（M1/M2/M4/M6）     ← 按 content_type 选择检查强度
           │
           ▼
    Content（内容稿）
           │
           ▼
    Content Product（内容产品）   ← product_formatter + metadata_generator + channel_adapter
           │
           ▼
    多渠道发布
```

**管线骨架（5阶段）永远存在**，但每个阶段内部调用的具体模块由 `content_type` 决定。

---

## 3. 管线三维分类体系

> 这是 SPDT-005 的核心设计维度。所有内容类型的差异，都可以从这三个维度解释和推导。

### 3.1 维度定义

| 维度 | 定义 | 衡量指标 |
|:---|:---|:---|
| **准确性（Accuracy）** | 内容的事实陈述是否经得起验证 | 来源等级（A/B/C）、引用标注、交叉验证比例 |
| **文学性（Literary）** | 文本的表达力、情感感染力和阅读体验 | 语气风格、场景描写密度、情感词频、结构自由度 |
| **专业性（Professional Depth）** | 内容对专业受众的理解深度和专业规范 | 术语密度、行业模板遵守、数据引用规范、专家审核需求 |

### 3.2 维度对管线各阶段的影响

#### 准确性 → 影响 ingest / structure / adapt 层

```
准确性高（science_fact / deep_report / breakdown_news）
  → ingest：多源交叉验证 / A/B级来源强制 / 来源分级标记
  → structure：知识图谱支撑 / 引用标注生成 / 事实核查点插入
  → adapt：事实性权重≥30% / 灰区工单触发阈值严格

准确性低（creative / oped）
  → ingest：单源或二手资料可接受
  → structure：模板化结构为主，减少人工编排约束
  → adapt：事实性权重≤25%，情感/逻辑权重上升
```

#### 文学性 → 影响 render / structure / deliver 层

```
文学性高（creative / oped_argument）
  → structure：非线性叙事结构 / 人物弧线设计 / 场景节奏规划
  → render：文学化语言 / 感官描写 / 情感节奏 / 大字数（3000-10000字）
  → deliver：排版优化（对话格式/引言样式/场景分隔符/长文适配）

文学性低（breakdown_news / product_review）
  → structure：固定模板 / 紧凑段落 / 要点列表
  → render：清晰高效 / 信息密度优先 / 短字数（300-1500字）
  → deliver：格式化输出 / 移动端优先 / 图文混排
```

#### 专业性 → 影响全链路

```
专业性高（deep_report / product_review / oped_argument）
  → ingest：行业数据库 / 财报解析 / 政策文件 / 专家访谈采集
  → structure：六段式报告模板 / 五段式评测模板 / 术语表生成
  → render：专业术语运用 / 数据引用规范 / 行业黑话适度使用
  → adapt：专家审核灰区触发 / 来源质量门槛高
  → deliver：PDF优先 / 长文图表 / 专业受众排版

专业性低（breakdown_news / creative）
  → ingest：大众媒体 / 社交媒体 / 科普来源可接受
  → structure：通用模板 / 无术语要求
  → render：术语必须解释 / 类比替代抽象概念
  → adapt：大众可读性优先
  → deliver：移动端/社交优先 / 短段落
```

### 3.3 六类型三维定位

```
                    高准确性
                        │
           ┌────────────┼────────────┐
           │  deep_    │  science_ │
           │  industry_ │   fact   │
           │  report   │          │
           │           │          │
高文学性 ──┼────────────┼────────────┼─ 低文学性
           │   oped_   │ breakdown_│
           │ argument  │   news   │
           │           │          │
           │           │          │
           └────────────┼────────────┘
                        │
                    低准确性
            低专业性 ←───┼───→ 高专业性
```

### 3.4 类型扩展方法论

新增内容类型时，只需回答三个问题：

```
1. 准确性 → 高/中/低 → 影响 ingest 严格度和 adapt 阈值
2. 文学性 → 高/中/低 → 影响 render 语气和 deliver 排版
3. 专业性 → 高/中/低 → 影响 ingest 采集范围和 structure 模板

→ 三个答案 → 自动映射到 registry 中的模块选择和质量权重
→ 无需修改管线架构
```

---

## 4. 阶段定义

### 阶段 1：Ingest（情报摄取）

| 职责 | 说明 |
|:---|:---|
| radar | 多源情报扫描（行业动态/竞品/热点/故事素材） |
| router | 内容类型分类 + 三维优先级判定 |
| channels | 多渠道内容抓取（RSS/API/Webhook/数据库） |
| smartext | 智能文本抽取（PDF/公众号/网页正文提取） |

**人类检查点 M1**：ContentSpec 确认
- 内容方向是否符合选题策略？
- 是否有授权来源？来源等级是否满足该类型的准确性要求？

---

### 阶段 2：Structure（结构化）

| 职责 | 说明 |
|:---|:---|
| article | 文章结构化（标题/导语/正文/结尾），固定模板为主 |
| genre | 体裁模板填充（六段报告/五段评测/四段评论/非线性叙事） |
| knowledge_graph | 知识点抽取与关联，用于高准确性类型 |

**人类检查点 M2**：知识结构验证
- 核心知识点是否完整？
- 专业类型的术语表/引用清单是否生成？
- 是否存在未授权引用？

---

### 阶段 3：Render（内容生成）

| 职责 | 说明 |
|:---|:---|
| engines/text | LLM 渲染引擎，按 content_type 的文学性和专业性配置选择 |

**Render 引擎选择依据：**

| 文学性 | 专业性 | 引擎特征 |
|:---|:---|:---|
| 低 | 低 | 客观快速、事实密集、禁止推测 |
| 低 | 高 | 专业术语、数据驱动、引用规范 |
| 高 | 低 | 文学化语言、类比丰富、情感共鸣 |
| 高 | 高 | 专业深度 + 文学表达（高难度组合） |

---

### 阶段 4：Adapt（质量适配）

| 职责 | 说明 |
|:---|:---|
| scorecard | 质量记分卡，按三维分类配置权重 |
| agent_templates | 体裁特定 agent 模板 |
| orchestration | 多 agent 编排（研究/写作/审核） |

**人类检查点 M4**：质量阈值检查
- 综合评分 ≥ 阈值 → 直接进入 M6
- 综合评分 < 阈值 → 触发修改流程
- 灰区内容 → 触发灰区工单（按该类型的准确性要求判断严格度）

---

### 阶段 5：Deliver（触达交付）

```
注意：Deliver 层交付的不只是"内容"，而是"内容产品"。

Content（内容稿）
  └→ product_formatter  ──→ 排版 + 视觉元素 + 格式适配
  └→ metadata_generator  ──→ SEO元数据 + 摘要 + 封面图建议
  └→ channel_adapter     ──→ 各渠道格式转换 + 渠道配置
  └→ autopublish         ──→ 多渠道发布
```

详见第6节「内容产品框架」。

**人类检查点 M6**：最终交付确认
- 内容产品化是否完成（排版/元数据/渠道配置）？
- 敏感内容品牌确认
- 渠道匹配确认

---

## 5. 人类检查点矩阵

| 内容类型 | M1 | M2 | M4 | M6 | 核心维度 |
|:---|:---:|:---:|:---:|:---:|:---|
| breakdown_news | 跳过 | 跳过 | 阈值70 | 快速确认 | 准确★ |
| science_fact | 确认 | 确认 | 阈值75 | 标准确认 | 准确★★★★★ |
| deep_industry_report | 主编确认 | 主编确认 | 阈值85 | 主编签批 | 准确★★★★ / 专业★★★★★ |
| oped_argument | 确认 | 确认 | 阈值80 | 主编签批 | 文学★★★★★ / 专业★★★★ |
| product_review | 确认 | 跳过 | 阈值80 | 标准确认 | 准确★★★★ / 专业★★★★ |
| creative | 确认 | 确认 | 阈值75 | 标准确认 | 文学★★★★★ |

**灰区工单规则**（所有类型通用）：
- 灰区触发 → 暂停发布 → 人工审核
- 准确性高的类型（science_fact / deep_report）→ 灰区工单更严格
- 涉及政治/敏感话题 → 强制主编 + 合规双重签批
- 3次灰区触发 → 自动升级主编审核

---

## 6. 内容产品框架（Content Product）

> 这是 SPDT-005 与 SPDT-004 的核心区别之一：
> **SPDT-004 交付知识内容，SPDT-005 交付内容产品。**

### 6.1 两层交付模型

| 层级 | 定义 | 交付物 |
|:---|:---|:---|
| **Content（内容）** | 纯文字稿，与渠道无关 | article_v2 JSON（标题/正文/元信息） |
| **Content Product（内容产品）** | 面向读者的完整产品，包含所有触达元素 | Content + 元数据 + 排版 + 渠道配置 |

### 6.2 Content Product 完整结构

```
ContentProduct = {
  # ── 核心内容 ────────────────────────────────────
  content: {
    article_v2,          // 文字稿（阶段3输出）
    word_count: number,
    reading_time: number, // 估算阅读时间
  },

  # ── 元数据 ──────────────────────────────────────
  metadata: {
    title: string,           // 标题
    SEO_title: string,        // SEO优化标题（可与标题不同）
    description: string,     // 摘要（150-300字）
    keywords: string[],      // 关键词（5-10个）
    tags: string[],          // 标签（内容归类）
    author: {
      name: string,
      bio: string,
      avatar: string,        // 头像URL
    },
    publish_time: string,    // 发布时间
    update_time: string,     // 更新时间
    language: "zh-CN",       // 语言
    cover_image: {
      url: string,
      alt: string,
      credit: string,        //图片来源
    },
    thumbnail: string,       // 缩略图URL（社交分享用）
  },

  # ── 产品化 ──────────────────────────────────────
  formatting: {
    typography: {
      font_family: string,   // 正文字体
      font_size: string,     // 字号
      line_height: number,   // 行距
      paragraph_spacing: number,
    },
    layout: {
      type: "single_column" | "double_column" | "mixed",
      max_width: string,     // 最大宽度
      has_toc: boolean,      // 是否有目录
    },
    visual_elements: {
      images: [{ url, alt, caption, position }],
      pullquotes: [{ text, attribution }],
      infoboxes: [{ title, content }],
      charts: [{ type, data, title, source }],
      code_blocks: [{ language, code }],
    },
    special_sections: {
      abstract: string,     // 摘要（专业报告用）
      references: [{ title, url, type }],
      appendix: string,      // 附录
    },
  },

  # ── 渠道配置 ────────────────────────────────────
  channel_config: {
    web: {
      permalink: string,
      category: string,
      featured: boolean,
      related_articles: string[],
    },
    wechat_mp: {
      original_mark: boolean,   // 原创标识
      cover_image_id: string,
      digest: string,           // 摘要（不超过54字）
      source: string,           // 来源
      tags: string[],
    },
    feishu: {
      doc_format: "docx" | "bitable",
      share_permission: "viewer" | "editor" | "public",
      comment_enabled: boolean,
    },
    feeds: {
      excerpt_length: number,   // 摘要长度（通常120字）
      include_images: boolean,
      thumbnail: string,
    },
    mobile: {
      push_title: string,      // ≤50字
      push_summary: string,    // ≤100字
      deep_link: string,       // App跳转链接
    },
  },

  # ── 互动设计 ────────────────────────────────────
  engagement: {
    related_articles: string[],
    cta: {
      type: "subscribe" | "comment" | "share" | "download" | "none",
      copy: string,            // CTA文案
      url: string,             // 跳转链接
    },
    comments_enabled: boolean,
    share_buttons: string[],   // ["weibo","wechat","twitter"]
  },
}
```

### 6.3 三层生成关系

```
阶段3 Render 输出
  │
  │  article_v2 JSON
  ▼
阶段4 Adapt 输出
  │
  │  scorecard 结果 + 质量确认
  ▼
阶段5 Deliver
  │
  ├──→ ProductFormatter    ──→ 排版 + 视觉元素
  ├──→ MetadataGenerator   ──→ SEO元数据 + 摘要 + 封面图建议
  ├──→ ChannelAdapter       ──→ 各渠道格式转换
  └──→ Autopublish          ──→ 多渠道发布
```

### 6.4 各类型内容产品差异

| 类型 | 排版 | 渠道配置重点 | 互动设计 |
|:---|:---|:---|:---|
| breakdown_news | 极简、要点列表、时间线 | web+mobile优先，推送优先 | 评论关闭，share优先 |
| science_fact | 图文混排、术语解释框 | web+公众号+feeds | 评论开启、相关科普文推荐 |
| deep_report | PDF/长文、图表丰富、目录 | 多渠道同步 | CTA（订阅/报告下载） |
| oped_argument | 文学排版、引言框突出 | web+公众号+feeds | 评论开启、讨论引导 |
| product_review | 对比表格、评分矩阵、图片 | 公众号为主、SEO优化 | affiliate披露、CTA购买链接 |
| creative | 文学排版、对话格式、场景分隔 | web+飞书+公众号 | 赞赏/打赏入口 |

---

## 7. 管线接口体系

> 接口定义来源：MODLIB `interface_protocols/IF-P_pipeline_interfaces.yaml`
> Schema 定义：MODLIB `schemas/*.schema.json`

### 7.1 接口设计的核心原则

1. **阶段间传递 JSON Artifact**：每个阶段输出的不是函数调用，而是自包含的 JSON 工件
2. **协议头统一**：所有 Artifact 都携带标准 header（artifact_id / content_type / pipeline_dimensions / produced_at）
3. **Schema 版本化**：接口 Schema 有明确版本号（当前 v1.0.0 draft）
4. **灰区跨阶段传递**：灰区标记不局限于某阶段，在 Artifact 中流转直至关闭

### 7.2 五阶段接口流

```
IF-P-1                IF-P-2               IF-P-3               IF-P-4              IF-P-5
Ingest ─────→ Structure ────→ Render ────→ Adapt ────→ Deliver ──→ ContentProduct
              │              │             │            │
Intelligence  ArticleOutline  Article_v2   Article_v2  Autopublish
Brief         (蓝图)         (稿件)       +Scorecard  (发布)
                           ↑               │
                           │               │
                     Schema版本:        Schema版本:
                     article_v2.schema  quality_scorecard.schema
```

### 7.3 五大接口详解

| 接口 | Artifact | Schema | 关键字段 |
|:---|:---|:---|:---|
| **IF-P-1** | IntelligenceBrief | `intelligence_brief.schema.json` | signals（情报信号）/ sources（来源分级A/B/C）/ knowledge_gaps |
| **IF-P-2** | ArticleOutline | `article_outline.schema.json` | sections（章节蓝图）/ word_count_target / knowledge_graph |
| **IF-P-3** | Article_v2 | `article_v2.schema.json` | blocks（内容块数组）/ terms（术语表）/ gray_zones |
| **IF-P-4** | Article_v2 + QualityScorecard | `quality_scorecard.schema.json` | total_score / dimensions / gray_zones / action |
| **IF-P-5** | ContentProduct | `content_product.schema.json` | metadata / formatting / channel_packages |

### 7.4 协议头的标准结构

所有 Artifact 的 header 必须包含：

```
header:
  artifact_id:      "ART-{type}-{content_type}-{date}-{uuid8}"   # 全局唯一
  artifact_type:    "intelligence_brief / article_outline / article_v2 / quality_scorecard"
  version:          Schema版本（如 "1.0.0"）
  content_type:     内容类型（对应 registry.yaml）
  pipeline_dimensions:
    accuracy:       1-5
    literary:       1-5
    professional_depth: 1-5
  pipeline_id:      管线实例ID（用于追踪）
  produced_at:      ISO 8601 时间戳
  producer:         生产模块路径
```

### 7.5 质量门控规则（Gate Rules）

每个阶段的输出必须通过 Schema 校验：

```
IF-P-1 → IF-P-2 门控：
  · signals.length >= 1
  · 所有 sources 必须有 grade（A/B/C）

IF-P-2 → IF-P-3 门控：
  · sections.length >= 1
  · 每个 section 必须有 section_id / title / target_words

IF-P-3 → IF-P-4 门控：
  · blocks.length >= 1
  · blocks 必须包含 required_blocks（由 outline 定义）
  · 所有 citations.source_id 必须在 IF-P-1 sources 中存在（禁止幻觉引用）

IF-P-4 → IF-P-5 门控：
  · total_score >= threshold → PASS → 进入 product 化
  · total_score < threshold → FAIL → 退回 Render 修改
  · gray_zones.length > 0 AND unresolved → HOLD → 等待人工确认
```

### 7.6 灰区工单生命周期

```
灰区触发 → 工单创建（ticket_id = GRAY-{stage}-{content_type}-{timestamp}）
    │
    ├──→ [open]        人工审核中
    │        │
    │        ├──→ [approved]  关闭，管线继续
    │        ├──→ [rejected]   拒绝，内容退回对应阶段
    │        └──→ [escalated]  升级至主编/合规
    │
    └──→ 自动关闭（如果内容修改后灰区消失）
```

灰区类型：G-POLITICAL / G-SOURCE / G-TIMELINESS / G-FACTUAL / G-LEGAL

路由依据：`ContentSpec.content_type` 字段

```
pipeline_router.py 执行逻辑：

1. 读取 ContentSpec.content_type
2. 在 content_type_registry.yaml 中查找对应路由
3. 提取三维分类标签（accuracy / literary / professional_depth）
4. 若未找到 → 回退到默认路由（article + standard）
5. 按顺序执行各阶段模块（模块选择由路由决定）
6. 各阶段输出作为下一阶段输入（JSON artifact）
7. M1/M2/M4/M6 人类检查点按注册表配置执行
8. Render 完成后，进入 Content Product 化流程
9. 通过 ChannelAdapter 适配各渠道后发布
```

---

## 8. 与 SPDT-004 的关系

| 共享层 | 说明 |
|:---|:---|
| 5阶段管线骨架 | ingest/structure/render/adapt/deliver |
| 质量记分卡框架 | content_scorecard_v1（三维权重配置） |
| 灰区工单机制 | signoff.py（签批工作流） |
| 发布引擎 | autopublish（飞书/微信） |
| MODLIB | 共享 schema、模板、协议 |

**SPDT-005 特有层**：
- 三维分类体系（准确性/文学性/专业性）
- 多 radar / render / structure 模块（按类型切换）
- 内容产品化层（ProductFormatter + MetadataGenerator + ChannelAdapter）
- 排版和视觉元素管理

---

## 10. 文件索引

| 文件 | 用途 |
|:---|:---|
| `governance/SPDT-005_SOP.md` | 本文档 — SOP 总纲 v1.1 |
| `platform/kb/content_type_registry.yaml` | 内容类型注册表 — mini-SOP 定义 + 三维分类 |
| `platform/1_ingest/router/pipeline_router.py` | 管线路由器 — 执行引擎 |
| `platform/5_deliver/checkpoint/signoff.py` | 灰区工单签批工作流 |
| `platform/5_deliver/checkpoint/deliver_checklist.yaml` | M6 交付检查清单 |
| `platform/5_deliver/product/` | 内容产品化模块（ProductFormatter / MetadataGenerator / ChannelAdapter） |
| `docs/pipeline_module_matrix.md` | 管线模块选择矩阵 — 各类型的模块执行路径 |

### MODLIB 接口文件（跨 SPDT 共享）

| 文件 | 用途 |
|:---|:---|
| `D:/1_omas/MODLIB/interface_protocols/IF-P_pipeline_interfaces.yaml` | 管线接口协议 — 五阶段接口定义 |
| `D:/1_omas/MODLIB/schemas/article_v2.schema.json` | Article_v2 工件 Schema v2.0 |
| `D:/1_omas/MODLIB/schemas/intelligence_brief.schema.json` | IntelligenceBrief Schema v1.0 |
| `D:/1_omas/MODLIB/schemas/article_outline.schema.json` | ArticleOutline Schema v1.0 |
| `D:/1_omas/MODLIB/schemas/quality_scorecard.schema.json` | QualityScorecard Schema v1.0 |
| `D:/1_omas/MODLIB/schemas/content_product.schema.json` | ContentProduct Schema v1.0 |

---

## 11. SOP 版本历史

| 版本 | 日期 | 变更 |
|:---|:---|:---|
| v1.0 | 2026-07-29 | 初版：元结构 + 内容类型注册表 |
| v1.1 | 2026-07-30 | 新增三维分类体系（准确性/文学性/专业性）；新增内容产品框架（Content Product三层结构）；新增模块选择矩阵文档；更新人类检查点矩阵 |
| v1.2 | 2026-07-30 | 新增管线接口体系（§7五阶段接口+Gate Rules+灰区工单生命周期）；引用MODLIB IF-P接口协议；新增MODLIB接口文件索引 |
