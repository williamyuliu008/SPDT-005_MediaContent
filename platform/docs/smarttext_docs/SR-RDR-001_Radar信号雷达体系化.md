# SR-RDR-001：Radar 信号雷达体系化

**发件方：** MKT内阁  
**收件方：** 交付内阁  
**文档类型：** 设计需求规格  
**优先级：** P0（Phase 2 前置依赖）  
**日期：** 2026-06-17  
**版本：** v1.0  
**关联文档：** 设计需求规格书 v1.0、MKT 内阁 Phase 1 验收意见

---

## 一、需求背景

Phase 1 验收发现：SmartTextPlatform 的文字创作能力（SmartText 轴）已体系化，但信号发现与价值评估能力（Radar 轴）仍处于"拍脑袋"阶段——依赖 CI Engine 的 10 家公司硬编码 + Survey 关键词搜索，缺乏系统化的信源管理、信号分类、评分准则和覆盖审计。

**核心认知：** AI 瞭望台的竞争力 = Radar（信息发现与价值评估）× SmartText（文字创作与表达）。两条轴需要同步体系化，否则频道的质量天花板受限于较弱的 Radar 轴。

### 两条能力轴的定位

```
Radar 轴（本 SR 范围）                    SmartText 轴（已有 STP V3）
─────────────────────────                ─────────────────────────
Q1: 看什么？（信源矩阵）                  Q1: 怎么写？（六赛道分类）
Q2: 什么类型？（信号分类法）              Q2: 什么风格？（差异化 Stage Prompt）
Q3: 有多重要？（评分准则）                Q3: 什么结构？（内容模板）
Q4: 可信吗？（可验证性阶梯）              Q4: 给谁看？（频道×内阁映射）
Q5: 漏了什么？（覆盖审计）                Q5: 写得好吗？（六维质量评分）
```

---

## 二、Radar Pipeline 架构

```
                    ┌──────────────────────────┐
                    │     Source Registry       │
                    │     信源注册中心           │
                    │  一手/二手/三手 × 5种信号  │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        CI Engine            Survey            ModLib 扫描
        10家公司事件          web_search         GitHub/HF
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Signal Ingestion         │
                    │   信号摄入                  │
                    │  原始事件 → 标准化信号      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
          ┌──────────────┐          ┌──────────────┐
          │  Classifier  │          │   Scorer     │
          │  信号分类器   │          │  评分引擎     │
          │              │          │              │
          │ 能力/结构/    │          │ 按类型拆维    │
          │ 供应链/生态/  │          │ 加权聚合      │
          │ 范式/风险     │          │              │
          └──────┬───────┘          └──────┬───────┘
                 │                         │
                 └──────────┬──────────────┘
                            ▼
                 ┌──────────────────┐
                 │  Verifiability    │
                 │  Ladder           │
                 │  L1-L4 验证标注   │
                 └────────┬─────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ 竞争频道    │  │ 芯事频道   │  │ 设计频道   │
   │ 能力+结构   │  │ 供应链信号 │  │ 范式信号   │
   └────────────┘  └────────────┘  └────────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                 ┌──────────────────┐
                 │  SmartText V3    │
                 │  六赛道文字生成   │
                 └──────────────────┘
```

---

## 三、模块详细规格

### 3.1 Source Registry（信源注册中心）

#### 概述

管理全部信源的元数据，包括信源层级（一手/二手/三手）、覆盖的信号类型、更新频率、可靠性评分。不再由各频道各自"搜一下"，而是统一注册、统一调度。

#### 数据结构

```yaml
# radar/source_registry.yaml
sources:
  - source_id: "nvidia_newsroom"
    name: "NVIDIA Newsroom"
    url: "https://nvidianews.nvidia.com/"
    tier: "primary"                    # primary | secondary | tertiary
    signal_types: ["capability", "supply_chain", "structural"]
    update_frequency: "realtime"       # realtime | daily | weekly
    reliability: 0.98                  # 历史准确率
    companies_covered: ["nvidia"]
    fetch_method: "rss"                # rss | web_search | page_fetch | api
    last_verified: "2026-06-17"

  - source_id: "semianalysis"
    name: "Semianalysis"
    url: "https://www.semianalysis.com/"
    tier: "secondary"
    signal_types: ["capability", "supply_chain"]
    update_frequency: "weekly"
    reliability: 0.85
    companies_covered: ["nvidia", "tsmc", "intel", "amd"]
    fetch_method: "page_fetch"

  - source_id: "sec_edgar"
    name: "SEC EDGAR"
    url: "https://www.sec.gov/cgi-bin/browse-edgar"
    tier: "primary"
    signal_types: ["structural"]
    update_frequency: "daily"
    reliability: 1.0
    companies_covered: ["openai", "microsoft", "nvidia", "google"]
    fetch_method: "api"
```

#### 信源层级定义

| 层级 | 定义 | 示例 | 默认置信度 |
|:----:|------|------|:----------:|
| **primary** | 官方一手信源，数据不可篡改 | 公司官网、SEC/EDGAR、财报、GitHub release | 0.95+ |
| **secondary** | 可信行业媒体或分析师，有待交叉验证 | AnandTech、Semianalysis、Bloomberg | 0.80-0.95 |
| **tertiary** | 社交媒体/传言，需谨慎对待 | Twitter/X、Reddit、脉脉、知乎 | < 0.60 |

#### 输出

- `radar/source_registry.yaml` — 信源注册表（手动维护，MKT 内阁定期更新）
- 每个信源附带 `reliability` 历史准确率（基于覆盖审计的验证回环更新）

---

### 3.2 Signal Taxonomy（信号分类法）

#### 概述

将原始事件按**影响类型**而非主题标签分类。六种信号类型各自对应不同的评分维度和目标频道。

#### 分类体系

| 信号类型 | 定义 | 核心问题 | 目标频道 |
|----------|------|----------|----------|
| **capability** 能力信号 | 技术能力的阶跃变化 | "谁能做什么以前做不了的事？" | 竞争态势 |
| **structural** 结构信号 | 行业结构的重组变化 | "谁和谁的关系变了？游戏规则变了吗？" | 竞争态势、芯事 |
| **supply_chain** 供应链信号 | 硬件/产能/价格变化 | "造 AI 的物理基础变了没有？" | 芯事 |
| **ecosystem** 生态信号 | 开源/平台/开发者变化 | "谁在建设生态？开发者在往哪里走？" | 开源雷达 |
| **paradigm** 范式信号 | 交互模式/设计语言变化 | "用户怎么和 AI 交互的方式变了吗？" | 设计前线 |
| **risk** 风险信号 | 安全/合规/伦理变化 | "什么东西可能出问题？" | 公益（未来） |

#### 自动分类规则

```
如果 event_type == "product_launch" AND tags 含 "model_release" | "hardware"
  → capability 信号

如果 event_type == "funding" | "ipo" | "acquisition"
  → structural 信号

如果 tags 含 "supply_chain" | "manufacturing" | "产能" | "价格"
  → supply_chain 信号

如果 tags 含 "open_source" | "github" | "huggingface" | "platform"
  → ecosystem 信号

如果 tags 含 "ux" | "design" | "interaction" | "agent"
  → paradigm 信号

如果 tags 含 "safety" | "regulation" | "security" | "ethics"
  → risk 信号
```

#### 输出

- 每条标准化信号增加 `signal_type` 字段
- 未分类信号进入 `unclassified` 队列，每周由 MKT 内阁打标

---

### 3.3 Scoring Rubric（评分准则）

#### 概述

不再使用单一 `importance_score`，而是按信号类型拆分为 2-3 个维度分，加权聚合。每个分数都有解释力。

#### 分类型评分维度

| 信号类型 | 维度 1（权重） | 维度 2（权重） | 维度 3（权重） |
|----------|:---:|:---:|:---:|
| **capability** | 性能提升幅度(40%) | 与竞品差距变化(30%) | 落地时间(30%) |
| **structural** | 影响范围·公司数(40%) | 资本规模(30%) | 不可逆程度(30%) |
| **supply_chain** | 产能变化%(50%) | 价格变化%(30%) | 替代方案可用性(20%) |
| **ecosystem** | 采用速度(30%) | 网络效应潜力(40%) | 护城河深度(30%) |
| **paradigm** | 新颖度(50%) | 可复制性(25%) | UX 改善幅度(25%) |
| **risk** | 危害严重度(50%) | 发生概率(30%) | 可控性(20%) |

#### 评分输出格式

```json
{
  "signal_id": "sig_20260617_001",
  "signal_type": "capability",
  "dimension_scores": {
    "performance_leap": {"score": 0.90, "rationale": "1 petaflop → 首次在笔记本形态实现"},
    "competitive_gap": {"score": 0.95, "rationale": "Apple/AMD 无同类产品，差距 12-18 个月"},
    "time_to_market": {"score": 0.85, "rationale": "今年秋季量产，OEM 已确认"}
  },
  "importance_score": 0.90,    // 加权聚合: 0.90×0.4 + 0.95×0.3 + 0.85×0.3
  "confidence": 0.95,
  "verifiability_level": "L4"
}
```

#### 评分实现

- Phase 2a：基于 CI Engine 现有 `importance_score` + 信号类型做规则映射（快速上线）
- Phase 3：接入 LLM 按维度逐项评分（准确性提升）
- 评分准则定期由 MKT 内阁校准（月度回顾中检查"高评分信号是否真的重要"）

---

### 3.4 Verifiability Ladder（可验证性阶梯）

#### 概述

每条信号标注其可验证性等级（L1-L4），影响该信号在日报中的呈现方式（标注/降权/延迟发布）。

#### 阶梯定义

| 等级 | 名称 | 条件 | 置信度基数 | 日报呈现 |
|:----:|------|------|:----------:|------|
| **L4** | 可验证 | 有一手公开数据源（财报/SEC/官方公告） | 0.95 | 正常展示 |
| **L3** | 可交叉验证 | 2+ 个独立二级信源一致 | 0.80 | 正常展示 |
| **L2** | 单一信源 | 仅 1 个可靠信源，无交叉验证 | 0.65 | 标注 [待交叉验证] |
| **L1** | 传言 | 社交媒体/匿名来源，无可靠信源支撑 | 0.40 | 标注 [传言] 或延迟发布 |

#### 自动标注规则

```
如果 source_level == "primary" AND source_url 域名在 primary_domains 白名单
  → L4

如果 source_level == "primary" 但来源不在已验证白名单
  → L3

如果 source_level == "secondary"
  → L3（如果该信源 reliability > 0.85）
  → L2（如果该信源 reliability ≤ 0.85）

如果 source_level 缺失或来源无法追溯
  → L1
```

#### 输出

- 每条信号的 `verifiability_level` 字段
- 日报底部增加"信号可信度分布"摘要

---

### 3.5 Coverage Audit（覆盖审计）

#### 概述

每周自动生成覆盖审计报告，回答"我们漏了什么"。这是 Radar 体系化的"兜底机制"——不追求覆盖一切，但必须知道自己没覆盖什么。

#### 审计维度

```
1. 按公司维度
   过去 7 天每家公司捕获的信号数量
   → 标记"信号密度异常低"的公司（低于周均 50%）
   → 例："本周 Anthropic 0 条信号——该公司的信源管道是否中断？"

2. 按信号类型维度
   过去 7 天每种信号类型的捕获数量
   → 标记"零信号"的类型
   → 例："本周 0 条 risk 信号——但 EU AI Act 正在执法阶段，我们的 risk 信源是盲区"

3. 按信源层级维度
   过去 7 天各级信源的贡献比例
   → 标记"一手信源不足"的频道
   → 例："竞争频道本周 14/16 条信号来自 secondary——一手信源覆盖率仅 12.5%"

4. 按地域维度
   过去 7 天各地区的信号密度
   → 标记"地域盲区"
   → 例："欧洲仅 1 条信号——Mistral/Aleph Alpha 等欧洲 AI 公司未被追踪"
```

#### 输出

```
文件路径: D:\92_products\SmartTextPlatform\radar\audit\YYYY-MM-DD.md
频次: 每周一 08:00 自动生成
接收方: MKT 内阁（用于调整信源注册表）
```

#### 审计 → 信源优化闭环

```
覆盖审计发现盲区 → MKT 内阁评估 → 更新 source_registry.yaml → Radar 覆盖改善
     ↑                                                              │
     └──────────────── 下期审计验证改善效果 ←────────────────────────┘
```

---

## 四、Radar Pipeline 实现

### 4.1 文件组织

```
D:\92_products\SmartTextPlatform\radar\
├── source_registry.yaml           ← 信源注册表（手动维护）
├── signal_taxonomy.py             ← 信号分类器
├── scoring_rubric.py              ← 评分引擎（按类型拆维）
├── verifiability.py               ← 可验证性阶梯标注
├── coverage_audit.py              ← 每周覆盖审计
├── ingest.py                      ← 信号摄入（CI Engine JSON → 标准化信号）
├── pipeline.py                    ← Radar Pipeline 主控（ingest → classify → score → verify）
├── dispatch.py                    ← 信号分发（capability→竞争频道, supply_chain→芯事频道...）
│
├── schemas/
│   ├── signal.json                ← 标准化信号 schema
│   └── source.json                ← 信源元数据 schema
│
├── audit/
│   └── YYYY-MM-DD.md              ← 覆盖审计报告归档
│
└── tests/
    └── test_taxonomy.py           ← 分类准确率测试
```

### 4.2 标准化信号 Schema

```json
{
  "signal_id": "sig_20260617_001",
  "ingested_at": "2026-06-17T22:52:00+08:00",
  "source_event": "evt_20260617_003",       // 来自 CI Engine 的原始事件 ID
  "company": "nvidia",
  "title": "NVIDIA发布RTX Spark超级芯片",
  "summary": "...",
  "date": "2026-06-04",
  "signal_type": "capability",              // ← 分类器标注
  "dimension_scores": {...},                // ← 评分引擎产出
  "importance_score": 0.90,
  "confidence": 0.95,
  "verifiability_level": "L4",              // ← 验证标注
  "source_url": "https://nvidianews.nvidia.com/...",
  "source_tier": "primary",
  "source_reliability": 0.98,
  "tags": ["hardware", "edge_ai", "personal_agents"],
  "dispatched_to": ["compete"]              // ← 分发目标频道
}
```

### 4.3 Pipeline 主流程

```python
# radar/pipeline.py 伪代码

def run_radar_pipeline(date_str: str) -> dict:
    """每日 Radar Pipeline：摄入 → 分类 → 评分 → 验证 → 分发"""

    # 1. 摄入：从各数据源拉取原始事件
    raw_events = ingest(date_str)
    # → 读取 CI Engine JSON + Survey 搜索 + ModLib 扫描

    # 2. 分类：每条事件标注 signal_type
    for event in raw_events:
        event.signal_type = classify(event)
        # → signal_taxonomy.py: 规则 + LLM fallback

    # 3. 评分：按信号类型拆维评分
    for event in raw_events:
        event.dimension_scores = score(event)
        event.importance_score = aggregate(event.dimension_scores)
        # → scoring_rubric.py

    # 4. 验证：标注可验证性等级
    for event in raw_events:
        event.verifiability_level = verify(event)
        event.confidence = adjust_confidence(event)
        # → verifiability.py

    # 5. 分发：按信号类型路由到目标频道
    dispatching = dispatch(raw_events)
    # → dispatch.py: capability→compete, supply_chain→chips, ...

    # 6. 输出：标准化信号 + 频道分发清单
    return {
        "signals": raw_events,
        "dispatched": dispatching,
        "stats": {
            "total": len(raw_events),
            "by_type": count_by_type(raw_events),
            "by_verifiability": count_by_level(raw_events),
            "by_company": count_by_company(raw_events),
        }
    }
```

### 4.4 与现有频道的对接

**Phase 2a 改动：** 竞争态势频道的 `build.py` 从直接读 CI Engine JSON → 改为读 Radar Pipeline 输出：

```python
# channels/compete/build.py（改动后）
from radar.pipeline import run_radar_pipeline

radar_output = run_radar_pipeline("2026-06-17")
compete_signals = radar_output["dispatched"]["compete"]  # 只取能力+结构信号

# 后续 SmartText 生成逻辑不变
```

---

## 五、对现有 CI Engine 的影响

### 不替代，而是包装

CI Engine 保持其 10 家公司事件采集的定位不变。Radar Pipeline 在 CI Engine 之上增加一层：

```
CI Engine (采集) → Radar Pipeline (分类+评分+验证+分发) → SmartText (生成)
```

### 具体改动

| 组件 | 改动 |
|------|------|
| CI Engine | **无改动。** 继续产出 `_extracted.json` |
| 竞争频道 build.py | 数据源从 `CI Engine JSON` 改为 `Radar Pipeline 输出` |
| 芯事/开源/设计 build.py | 新建时直接对接 Radar Pipeline |

---

## 六、验收标准

### Phase 2a 验收（Radar 就绪）

| 验收项 | 验收方法 | 通过标准 |
|--------|----------|----------|
| 信源注册表 | 查看 `radar/source_registry.yaml` | ≥ 10 个一手信源 + ≥ 20 个二手信源，覆盖全部 10 家公司 |
| 信号分类准确率 | 运行 `radar/tests/test_taxonomy.py` | 对已有 CI Engine 事件（18条/天）分类准确率 ≥ 85% |
| 评分引擎可用 | 运行 `scoring_rubric.py` 对 6/17 事件评分 | 每条信号输出 ≥ 2 个维度分 + 加权聚合分数 + 简短理由 |
| 验证标注可用 | 运行 `verifiability.py` 对 6/17 事件标注 | 每条信号有 L1-L4 等级 + 调整后置信度 |
| 竞争频道对接 | 竞争频道 build.py 改为读取 Radar 输出 | 日报正常生成，Stage 差异度不退化（≥ 0.50） |
| 覆盖审计报告 | 运行 `coverage_audit.py` 生成 6/17 审计 | 输出 4 维度审计（公司/类型/层级/地域） |

### Phase 2b 验收（频道扩展）

| 验收项 | 通过标准 |
|--------|----------|
| 芯事频道基于 Radar supply_chain 信号生成 | 日报含 4 模块，供应链信号占比 ≥ 60% |
| 开源雷达基于 Radar ecosystem 信号生成 | 日报含 4 模块，对接 ModLib + GitHub 信号 |
| 设计前线基于 Radar paradigm 信号生成 | 周报含鸿蒙启示模块，对接 App Scanner |
| 网站全频道上线 | 9 页全部可浏览 |

---

## 七、交付时间线

```
Phase 2a（本周五-下周一，~3天）
─────────────────────────────────
□ source_registry.yaml 信源注册表
□ signal_taxonomy.py 信号分类器
□ scoring_rubric.py 评分引擎
□ verifiability.py 验证标注
□ pipeline.py + dispatch.py
□ coverage_audit.py 覆盖审计
□ 竞争频道 build.py 改造对接 Radar

Phase 2b（下周二-周五，~4天）
─────────────────────────────────
□ SR-CH-002 芯事频道（基于 Radar supply_chain）
□ SR-CH-003 开源雷达频道（基于 Radar ecosystem）
□ SR-CH-004 设计前线频道（基于 Radar paradigm）
□ SR-WEB-001 网站完整版（全频道页+搜索）
```

---

## 八、两条能力轴的分工

```
              Radar 轴                        SmartText 轴
              ─────────                      ────────────
看护内阁       MKT 内阁（信源策略+评分校准）     MKT 内阁（质量验收+风格把控）
建设内阁       交付内阁（Pipeline 实现）         交付内阁（STP V3 + 频道 build.py）
核心指标       信源覆盖率 / 分类准确率            Stage 差异度 / 六维质量评分
              / 评分一致性 / 审计盲区数
演进方向       更多一手信源 / 自动化评分          更多赛道 / 更多体裁
              / 跨语言信源 / 实时信号             / 个性化风格 / 多语言
```

---

*需求规格书结束。请交付内阁评估 Radar 模块的技术可行性，优先启动 Phase 2a。*
