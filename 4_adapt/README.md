# 4_adapt · 自适应编排层
## 协调型架构 — 品牌化编排

---

## 定位

协调型流水线的**自适应编排阶段**。消费渲染产出，执行品牌化自适应编排和质量记分卡。

## 核心职责

| 职责 | 说明 |
|:---|:---|
| **M5 质量记分卡** | content_scorecard_v1 综合评分（品牌/受众/时效/结构） |
| **品牌自适应** | 目标受众和品牌定位匹配（PT-040 DeepProd 等按品牌分发） |
| **知识资产注册** | 稿件元数据注册到 KB（spdt_content_registry） |

## 质量记分卡（content_scorecard_v1）

| 维度 | 权重 | 说明 |
|:---|:---|:---|
| 品牌一致性 | 25% | 与目标受众/品牌定位匹配 |
| 时效性 | 20% | 发布时机评估（快讯优先） |
| 受众覆盖 | 20% | 目标读者群匹配度 |
| 内容质量 | 20% | G-SOURCE / G-FACTUAL 综合 |
| 结构完整性 | 15% | G-STRUCTURE / G-FORMAT |

| 评分区间 | 判定 | 处理 |
|:---|:---|:---|
| ≥85分 | **直接发布** | 输出到 5_deliver |
| 70-84分 | **需修订** | 打回 2_structure 重写 |
| <70分 | **内容失败** | 归档，记录原因，重新发起 |

## 协调型说明

> 本层在 ManuscriptsEngine 的 agents/review 和 orchestration 模块中实现。
> SPDT-005 通过 junction 引用，不复制代码。

## 五阶段映射

| 阶段 | 对应 SOP | 本层实现 |
|:---|:---|:---|
| 4_adapt | M5 | agents/review + orchestration（引用 ManuscriptsEngine） |

## 与 SPDT-004 4_adapt 的关系

| 维度 | SPDT-004（教育） | SPDT-005（媒体） |
|:---|:---|:---|
| 核心逻辑 | 薄弱点驱动（知识图谱） | 品牌化记分卡（content_scorecard） |
| 自适应方向 | 学习者薄弱点 → 训练推荐 | 品牌定位 → 受众匹配 + 发布时机 |
| 编排引擎 | AdaptivePrepPlatform | ManuscriptsEngine agents |
| 核心差异 | **学习者视角** | **品牌/受众视角** |
