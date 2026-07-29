# SPDT-005 媒体内容 SOP v1.0
## 元结构：弹性供应链型管线

---

## 1. 核心设计理念

SPDT-005 媒体内容管线**不是一条刚性装配线**，而是一套**弹性供应链**。

| 对比维度 | SPDT-004 教育管线 | SPDT-005 媒体管线 |
|:---|:---|:---|
| 类比 | 刚性装配线 | 弹性供应链 |
| 输入差异 | 科目不同（语文/数学/历史） | 内容类型不同（快讯/报告/科普/评论） |
| 管线行为 | 同一套固定工序序列 | 同一套阶段名，内部模块按类型动态切换 |
| 复杂性来源 | 知识内容本身的复杂度 | 内容类型 × 渠道 × 时效性 × 来源质量的组合爆炸 |
| SOP 形态 | 一套固定工序 | **元结构**（工序选择器 + 内容类型注册表） |

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
           │ route                  · 质量阈值
           ▼                       · SLA 时限
    ┌──────────────────────────┐   · 人类检查点策略
    │  1_ingest ───────────────┼─→ radar.breaking / radar.industry / smartext / ...
    │  2_structure ────────────┼─→ article / genre / knowledge_graph / ...
    │  3_render ───────────────┼─→ engines/text.[engine_a / engine_b / ...]
    │  4_adapt ────────────────┼─→ scorecard / agent_templates / orchestration
    │  5_deliver ──────────────┼─→ publish.[auto / multi_channel / fast]
    └──────────────────────────┘
           │
           ▼
    人类检查点（M1/M2/M4/M6）     ← 按 content_type 选择检查强度
```

**管线骨架（5阶段）永远存在**，但每个阶段内部调用的具体模块由 `content_type` 决定。

---

## 3. 阶段定义

### 阶段 1：Ingest（情报摄取）

| 职责 | 描述 |
|:---|:---|
| radar | 多源情报扫描（行业动态/竞品/热点） |
| router | 内容类型分类 + 优先级判定 |
| channels | 多渠道内容抓取（RSS/API/Webhook） |
| smartext | 智能文本抽取（PDF/公众号/网页正文提取） |

**人类检查点 M1**：ContentSpec 确认
- 内容方向是否符合选题策略？
- 是否有授权来源？

### 阶段 2：Structure（结构化）

| 职责 | 描述 |
|:---|:---|
| article | 文章结构化（标题/导语/正文/结尾） |
| genre | 体裁模板填充（快讯模板/报告模板/科普模板） |
| knowledge_graph | 知识点抽取与关联 |

**人类检查点 M2**：知识结构验证
- 核心知识点是否完整？
- 是否存在未授权引用？

### 阶段 3：Render（内容生成）

| 职责 | 描述 |
|:---|:---|
| engines/text | LLM 渲染引擎（按内容类型选择） |

**无固定人类检查点**（由内容类型决定）

### 阶段 4：Adapt（质量适配）

| 职责 | 描述 |
|:---|:---|
| scorecard | 质量记分卡评估（可读性/事实性/来源/时效性） |
| agent_templates | 体裁特定 agent 模板 |
| orchestration | 多 agent 编排（研究/写作/审核） |

**人类检查点 M4**：质量阈值检查
- 综合评分 ≥ 阈值 → 直接进入 M6
- 综合评分 < 阈值 → 触发修改流程
- 灰区内容 → 触发灰区工单

### 阶段 5：Deliver（触达交付）

| 职责 | 描述 |
|:---|:---|
| publish | autopublish 多渠道发布 |
| channels | 渠道配置与适配 |

**人类检查点 M6**：最终交付确认
- 敏感内容品牌确认
- 发布时机确认
- 渠道匹配确认

---

## 4. 人类检查点矩阵

```
│ 内容类型      │ M1   │ M2   │ M4         │ M6         │ SLA      │
│:-------------|:----:|:----:|:----------:|:----------:|:--------:|
│ breakdown_news│ 跳过 │ 跳过 │ 阈值70    │ 快速确认   │ 15分钟   │
│ science_fact  │ 确认 │ 确认 │ 阈值75    │ 标准确认   │ 4小时    │
│ deep_report   │ 确认 │ 确认 │ 阈值85    │ 主编签批   │ 4小时+   │
│ oped_argument │ 确认 │ 确认 │ 阈值80    │ 主编签批   │ 3小时+   │
│ product_review│ 确认 │ 跳过 │ 阈值80    │ 标准确认   │ 24小时   │
```

**灰区工单规则**（所有类型通用）：
- 灰区触发 → 暂停发布 → 人工审核
- 敏感话题 → 强制主编 + 合规双重签批
- 3次灰区触发 → 自动升级主编审核

---

## 5. 内容类型路由规则

路由依据：`ContentSpec.content_type` 字段

```
pipeline_router.py 执行逻辑：

1. 读取 ContentSpec.content_type
2. 在 content_type_registry.yaml 中查找对应路由
3. 若未找到 → 回退到默认路由（article + standard）
4. 按顺序执行各阶段模块
5. 各阶段输出作为下一阶段输入（JSON artifact）
6. M1/M2/M4/M6 人类检查点按注册表配置执行
```

---

## 6. 与 SPDT-004 的关系

| 共享层 | 说明 |
|:---|:---|
| 5阶段管线骨架 | ingest/structure/render/adapt/deliver |
| 质量记分卡框架 | content_scorecard_v1 |
| 灰区工单机制 | signoff.py（签批工作流） |
| 发布引擎 | autopublish（飞书/微信） |
| MODLIB | 共享 schema、模板、协议 |

**SPDT-005 特有层**：
- 多 radar 模块（按类型切换）
- 多 render 引擎（按类型切换）
- 多 deliver 策略（快/标准/多渠道）
- 时效性管理（SLA 追踪）

---

## 7. 文件索引

| 文件 | 用途 |
|:---|:---|
| `governance/SPDT-005_SOP.md` | 本文档 — SOP 总纲 |
| `platform/kb/content_type_registry.yaml` | 内容类型注册表 — mini-SOP 定义 |
| `platform/1_ingest/router/pipeline_router.py` | 管线路由器 — 执行引擎 |
| `platform/5_deliver/checkpoint/signoff.py` | 灰区工单签批工作流 |
| `platform/5_deliver/checkpoint/deliver_checklist.yaml` | M6 交付检查清单 |

---

## 8. SOP 版本历史

| 版本 | 日期 | 变更 |
|:---|:---|:---|
| v1.0 | 2026-07-29 | 初版：元结构 + 内容类型注册表 |
