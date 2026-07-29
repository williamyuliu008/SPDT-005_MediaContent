# SPDT-005 管线模块选择矩阵
## 各内容类型的 mini-SOP 执行图谱

> 用途说明：
> - **横向**：了解某种内容类型的完整执行路径
> - **纵向**：了解某个模块需要支持哪些功能需求（从而判断模块设计边界）

---

## 一、总览：5阶段 × 6模块矩阵

```
阶段        │ 快讯    │ 深度报告  │ 科普     │ 评论     │ 产品评测  │ 创意写作
────────────┼─────────┼───────────┼──────────┼──────────┼───────────┼──────────
① Ingest    │ radar.  │ radar.    │ smartext │ radar.   │ channels. │ radar.
            │ breaking│ industry  │ .paper   │ opinion  │ product   │ story
────────────┼─────────┼───────────┼──────────┼──────────┼───────────┼──────────
② Structure │ article.│ genre.    │ kg.      │ article. │ article.  │ genre.
            │ breaking│ report    │ science  │ oped     │ review    │ creative
────────────┼─────────┼───────────┼──────────┼──────────┼───────────┼──────────
③ Render    │ engine. │ engine.   │ engine.  │ engine.  │ engine.   │ engine.
            │ breaking│ deep_report│ science  │ argument │ review    │ creative
────────────┼─────────┼───────────┼──────────┼──────────┼───────────┼──────────
④ Adapt     │ score.  │ score.    │ score.   │ score.   │ score.    │ score.
            │ breaking│ deep_report│ science  │ argument │ review    │ creative
────────────┼─────────┼───────────┼──────────┼──────────┼───────────┼──────────
⑤ Deliver   │ publish.│ publish.  │ publish. │ publish. │ publish.  │ publish.
            │ fast    │ multi_ch  │ standard │ multi_ch │ standard  │ standard
```

---

## 二、逐类型详细说明

### 类型 1：突发快讯（breakdown_news）

**定位**：时效性最强的内容，15分钟完成全流程。

#### 执行路径

| 阶段 | 模块 | 功能需求 | 为什么这样选择 |
|:---|:---|:---|:---|
| ① Ingest | `radar.breaking` | 关键词触发 + 多源实时监控 | 突发事件关键词识别（政策/危机/事故） |
| ② Structure | `article.breaking` | 极简结构模板（标题+导语+事实点+时间线） | 速度优先，预设结构，无需编排 |
| ③ Render | `engine.breaking` | 客观、快速、专业语气；禁止推测 | 快讯不允许AI生成推测性内容 |
| ④ Adapt | `scorecard.breaking` | 阈值70；时效性权重25% | 快速通道降门槛，但来源和事实性仍严格 |
| ⑤ Deliver | `publish.fast` | 自动发布，无需等待 | SLA 15分钟，人工确认来不及 |

#### 人类检查点策略
- M1：跳过（选题自动通过）
- M2：跳过（结构预设）
- M4：70分阈值
- M6：值班编辑快速确认

#### 模块功能需求汇总
```
radar.breaking    → 关键词监控 / 突发事件识别 / SLA计时
article.breaking  → 极简模板（4段式）/ 时间线生成
engine.breaking   → 客观语气 / 禁止推测 / 字数控制（300-500字）
scorecard.breaking→ 时效性权重↑ / 来源权重↓ / 70分阈值
publish.fast      → 自动发布 / 渠道静默推送 / 发布日志
```

---

### 类型 2：深度行业报告（deep_industry_report）

**定位**：3000-8000字专业分析，面向行业从业者。

#### 执行路径

| 阶段 | 模块 | 功能需求 | 为什么这样选择 |
|:---|:---|:---|:---|
| ① Ingest | `radar.industry` | 行业媒体 + 财报 + 政策文件 + 专家访谈采集 | 多源交叉验证，确保深度 |
| ② Structure | `genre.report` | 摘要+背景+核心发现+深度分析+趋势预判+结论建议 | 六段式结构，逻辑严谨 |
| ③ Render | `engine.deep_report` | 专业语气 / 数据驱动 / 有洞察 / 避免套话 | 面向专业受众，拒绝空话 |
| ④ Adapt | `scorecard.deep_report` | 阈值85；来源权重25%；深度权重20% | 高标准，来源质量和洞察深度并重 |
| ⑤ Deliver | `publish.multi_channel` | web + feeds + 飞书 + 公众号同步 | 最大化触达，多渠道分发 |

#### 人类检查点策略
- M1：主编确认（选题深度评估）
- M2：主编确认（大纲结构）
- M4：85分阈值，低于则退回修改
- M6：主编强制签批

#### 灰区规则
- 涉及竞争对手负面 → 法务审核
- 数据来源为C级 → 要求升级来源
- 涉及政策预测 → 专家签字

#### 模块功能需求汇总
```
radar.industry    → 多源采集（媒体/财报/政策/访谈）/ 数据交叉验证 / 来源分级
genre.report      → 六段式结构 / 摘要生成 / 图表标注点 / 结论建议生成
engine.deep_report→ 专业语气 / 数据引用格式 / 洞察生成提示词 / 8000字级支持
scorecard.deep   → 来源权重↑ / 深度权重↑ / 85分高阈值 / 专家审核触发
publish.multi_ch → 多渠道同时发布 / 格式适配（公众号长文/飞书文档）
```

---

### 类型 3：科普知识（science_fact）

**定位**：面向大众，准确性与可读性并重。

#### 执行路径

| 阶段 | 模块 | 功能需求 | 为什么这样选择 |
|:---|:---|:---|:---|
| ① Ingest | `smartext.paper_extraction` | 学术论文/权威科普来源抽取 | 准确性是底线，优先一手权威来源 |
| ② Structure | `kg.science` | 知识点图谱抽取 + 知识关联 | 科普需以知识点为核心组织，非线性展开 |
| ③ Render | `engine.science` | 生动有趣 / 类比清晰 / 术语需解释 | 大众读者，专业术语必须解释 |
| ④ Adapt | `scorecard.science` | 阈值75；事实性权重40%；可读性权重30% | 准确性最重要（40%），其次是读懂（30%） |
| ⑤ Deliver | `publish.standard` | web + feeds + 公众号 | 标准分发节奏 |

#### 人类检查点策略
- M1：来源权威性确认
- M2：知识准确性初步确认
- M4：75分阈值
- M6：标准确认

#### 灰区规则
- 涉及医疗/健康/药物 → 医疗审核
- 涉及食品安全 → 安全检查

#### 模块功能需求汇总
```
smartext.paper   → PDF/论文解析 / 摘要抽取 / 关键数据提取 / 参考文献追踪
kg.science       → 知识点抽取 / 知识图谱构建 / 类比关系推荐 / 可视化标注
engine.science   → 类比生成 / 术语解释插入 / 生动语气 / 避免恐吓式科普
scorecard.science→ 事实性权重40% / 可读性权重30% / 术语解释检查
publish.standard → 标准格式 / 图片嵌入 / 公众号长图适配
```

---

### 类型 4：观点评论（oped_argument）

**定位**：有明确立场和论点，面向公共讨论。

#### 执行路径

| 阶段 | 模块 | 功能需求 | 为什么这样选择 |
|:---|:---|:---|:---|
| ① Ingest | `radar.opinion` | 相关事件背景 + 对立观点 + 反驳预判采集 | 评论需要知道对立面是什么 |
| ② Structure | `article.oped` | 论点+论据+反驳预判+结论 | 四段式，有立场、有理据、有预判反驳 |
| ③ Render | `engine.argument` | 鲜明立场 / 有理有据 / 不人身攻击 | 立场鲜明但不失理性和建设性 |
| ④ Adapt | `scorecard.argument` | 阈值80；逻辑权重30%；事实权重25% | 逻辑严密性最重要（30%），事实也不能少 |
| ⑤ Deliver | `publish.multi_channel` | web + feeds + 飞书 + 公众号 | 评论需要广泛讨论 |

#### 人类检查点策略
- M1：选题评论价值确认
- M2：论点大纲确认
- M4：80分阈值
- M6：主编签批（强制）

#### 灰区规则
- 涉及政治/宗教/民族 → 合规审核（强制）
- 点名批评具体人物 → 法务审核

#### 模块功能需求汇总
```
radar.opinion    → 事件背景采集 / 反方观点收集 / 读者反驳预判 / 情绪热度追踪
article.oped     → 论点-论据-反驳-结论四段式 / 反方标注 / 情感落点设计
engine.argument  → 立场鲜明语气 / 逻辑连贯性 / 反驳预判嵌入 / 禁止人身攻击
scorecard.argument→ 逻辑权重30% / 事实权重25% / 品牌调性权重10%
publish.multi_ch → 多渠道 / 评论功能开启 / 社交分享优化
```

---

### 类型 5：产品评测（product_review）

**定位**：含购买建议的评测，诚实中立是核心。

#### 执行路径

| 阶段 | 模块 | 功能需求 | 为什么这样选择 |
|:---|:---|:---|:---|
| ① Ingest | `channels.product_specs` | 官方参数 + 用户评价 + 竞品对比数据采集 | 评测需要多源对比，参数+口碑双验证 |
| ② Structure | `article.review` | 开箱印象+核心体验+优缺点+竞品对比+购买建议 | 五段式，结构固定，无需灵活编排 |
| ③ Render | `engine.review` | 诚实中立 / 具体数据支撑 / 有购买建议 | 评测核心价值：不说空话，有数据有建议 |
| ④ Adapt | `scorecard.review` | 阈值80；客观性权重30%；事实权重30% | 客观性（30%）和事实性（30%）并重 |
| ⑤ Deliver | `publish.standard` | web + feeds + 公众号 | 标准节奏 |

#### 人类检查点策略
- M1：产品是否值得评测（选题把关）
- M2：跳过（结构固定）
- M4：80分阈值
- M6：标准确认

#### 灰区规则
- 涉及 affiliate/返佣链接 → 利益披露检查
- 竞品对比数据 → 数据来源核实

#### 模块功能需求汇总
```
channels.product  → 官方参数API / 用户评价爬取（电商/论坛）/ 竞品数据库对比
article.review    → 五段式模板 / 评分矩阵生成 / 优缺点可视化标注
engine.review    → 中立语气 / 数据引用格式 / 购买建议生成 / 避免软文感
scorecard.review  → 客观性权重30% / 事实权重30% / affiliate披露检查
publish.standard  → 标准格式 / 图片对比图嵌入 / 相关文章推荐
```

---

### 类型 6：创意写作（creative）

**定位**：非虚构创意写作（人物特稿/故事化报道）。

#### 执行路径

| 阶段 | 模块 | 功能需求 | 为什么这样选择 |
|:---|:---|:---|:---|
| ① Ingest | `radar.story` | 人物访谈/一手素材/背景资料采集 | 创意写作依赖一手素材，故事感来自细节 |
| ② Structure | `genre.creative` | 非线性叙事：场景切入+冲突展开+人物弧线+情感落点 | 文学结构，不是论文结构 |
| ③ Render | `engine.creative` | 文学化语气 / 有画面感 / 情感真实 | 非虚构创意写作 = 真实+文学性 |
| ④ Adapt | `scorecard.creative` | 阈值75；可读性权重30%；情感权重30%；创意权重15% | 文学性评分权重更高（创意15%，其他类型无此维度） |
| ⑤ Deliver | `publish.standard` | web + 飞书 + 公众号 | 标准节奏 |

#### 人类检查点策略
- M1：选题故事性评估
- M2：大纲叙事结构确认
- M4：75分阈值
- M6：标准确认

#### 灰区规则
- 涉及真实人物 → 当事人授权确认
- 涉及未成年人 → 监护人授权

#### 模块功能需求汇总
```
radar.story      → 人物访谈素材管理 / 场景细节采集 / 背景资料关联
genre.creative    → 非线性叙事结构 / 人物弧线设计 / 场景-对话-叙述节奏
engine.creative  → 文学化语言 / 感官细节描写 / 情感真实 / 场景蒙太奇
scorecard.creative→ 文学性多维评分（可读性30%/情感30%/创意15%/事实性25%）
publish.standard → 排版优化（引言/对话/场景分割）/ 长文适配 / 飞书文档格式
```

---

## 三、模块功能需求汇总（按模块维度）

### Ingest 层模块需求

| 模块 | 必须支持 | 差异化能力 |
|:---|:---|:---|
| `radar.breaking` | 关键词触发 / 15分钟SLA计时 | 突发事件识别 / 危机等级判断 |
| `radar.industry` | 多源采集（≥3种源） / 来源分级 | 财报解析 / 政策文件抽取 / 专家访谈 |
| `radar.opinion` | 事件背景 / 反方观点收集 | 情绪热度追踪 / 反驳预判生成 |
| `radar.story` | 一手素材管理 / 人物资料库 | 场景细节采集 / 访谈记录整理 |
| `smartext.paper_extraction` | PDF解析 / 摘要抽取 | 参考文献追踪 / 关键数据提取 |
| `channels.product_specs` | 官方参数API / 用户评价爬取 | 竞品数据库对比 / 价格追踪 |

### Structure 层模块需求

| 模块 | 结构类型 | 关键能力 |
|:---|:---|:---|
| `article.breaking` | 极简4段式 | 标题生成 / 时间线自动构建 |
| `article.oped` | 论点4段式 | 论点-论据映射 / 反方标注 |
| `article.review` | 评测5段式 | 评分矩阵生成 / 优缺点提取 |
| `genre.report` | 深度6段式 | 摘要生成 / 图表建议 / 结论生成 |
| `genre.creative` | 非线性叙事 | 人物弧线设计 / 场景节奏规划 |
| `kg.science` | 知识点图谱 | 知识点抽取 / 知识关联 / 类比推荐 |

### Render 层模块需求

| 模块 | 语气风格 | 字数范围 | 特殊要求 |
|:---|:---|:---|:---|
| `engine.breaking` | 客观、快速、专业 | 300-500字 | **禁止推测性内容** |
| `engine.deep_report` | 专业、数据驱动、有洞察 | 3000-8000字 | 数据引用格式 / 洞察提示 |
| `engine.science` | 生动、类比清晰 | 1000-3000字 | 术语解释插入 / 恐吓式规避 |
| `engine.argument` | 鲜明、有理、不攻击人 | 1500-4000字 | 反驳预判嵌入 / 逻辑连贯性 |
| `engine.review` | 诚实中立、有数据 | 2000-5000字 | 购买建议 / affiliate提示 |
| `engine.creative` | 文学化、画面感、情感真实 | 3000-10000字 | 感官描写 / 场景蒙太奇 |

### Adapt 层评分权重配置

| 模块 | 事实性 | 可读性 | 来源 | 时效性 | 深度 | 逻辑 | 情感 | 创意 | 客观性 | 阈值 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `scorecard.breaking` | 35% | 20% | 20% | **25%** | - | - | - | - | - | 70 |
| `scorecard.deep_report` | 30% | 15% | **25%** | 10% | **20%** | - | - | - | - | 85 |
| `scorecard.science` | **40%** | **30%** | 20% | - | - | - | - | - | - | 75 |
| `scorecard.argument` | 25% | 20% | 15% | - | - | **30%** | - | - | - | 80 |
| `scorecard.review` | 30% | 20% | 20% | - | - | - | - | - | **30%** | 80 |
| `scorecard.creative` | 25% | **30%** | - | - | - | - | **30%** | **15%** | - | 75 |

> 注：各维度权重总和为100%，加粗为该类型的核心权重维度

### Deliver 层发布策略

| 模块 | 渠道 | 发布模式 | SLA | 特殊处理 |
|:---|:---|:---|:---|:---|
| `publish.fast` | web+mobile+feishu | 自动立即发布 | 15分钟 | 无需人工确认 |
| `publish.multi_channel` | web+feeds+feishu+wechat | 多渠道同步 | 4小时+ | 格式适配（各渠道） |
| `publish.standard` | web+feeds+wechat | 定时/队列发布 | 24-48小时 | 标准格式适配 |

---

## 四、模块开发优先级建议

| 优先级 | 模块 | 理由 |
|:---|:---|:---|
| P0 | `radar.breaking` + `article.breaking` + `publish.fast` | 快讯是媒体内容最高频类型 |
| P0 | `engine.breaking` + `scorecard.breaking` | 渲染和评分是全类型共享 |
| P1 | `smartext.paper_extraction` + `kg.science` + `engine.science` | 科普是第二大高频类型 |
| P1 | `scorecard` 通用框架 + 各类型权重覆盖 | 所有类型共用，分数可比 |
| P2 | `radar.industry` + `genre.report` + `engine.deep_report` | 深度报告，媒体品牌核心 |
| P2 | `channels.product_specs` + `engine.review` | 产品评测，流量型内容 |
| P3 | `radar.opinion` + `article.oped` + `engine.argument` | 评论，高门槛但高价值 |
| P3 | `radar.story` + `genre.creative` + `engine.creative` | 创意写作，高门槛低频 |
