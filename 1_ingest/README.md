# 1_ingest · 知识摄入层
## 协调型架构 — 路由入口

---

## 定位

协调型流水线的**入口阶段**。不直接生产内容，而是通过 smarttext_router 判定内容类型并将任务分发到对应 PDT。

## 核心职责

| 职责 | 说明 |
|:---|:---|
| **M0 入口判别** | smarttext_router 判断输入类型（快讯/深度/科普/评论） |
| **M1 路由分发** | 按 B1-B4 形态路由到对应 PDT（PT-040~PT-046） |
| **ContentSpec 生成** | 为每条内容任务生成需求规格（供下游使用） |

## 输入来源

- 实时数据源（radar_platform / SPDT-009 SemiIntelligence 情报触发）
- 用户手动提交（编辑器/内容运营）
- 定时任务（PT-041 FlashNews 每日简报）

## 核心组件

### smarttext_router
```
platform/infrastructure/smarttext_router/
```
- **SOP 阶段**：M0 + M1
- **输入**：原始文本 / 数据信号 / URL
- **输出**：ContentSpec YAML（路由决策 + 内容规格）
- **路由目标**：PT-040（深度）/ PT-041（快讯）/ PT-042（科普）/ PT-043（评论）/ PT-046（数据新闻）

## 协调型说明

> 本阶段**不生产内容**，仅做路由决策。
> 实际生产由对应 PDT（外部 PT 仓库）的 ManuscriptsEngine 执行。

```
外部 PDT（PT-040~PT-046）
    ↑
smarttext_router（M0+M1路由）
    ↑
外部数据源（radar / SemiIntelligence / 人工提交）
```

## 五阶段映射

| 阶段 | 对应 SOP | 本层实现 |
|:---|:---|:---|
| 1_ingest | M0+M1 | smarttext_router（路由分发） |

## 与 SPDT-004 1_ingest 的关系

| 维度 | SPDT-004（教育） | SPDT-005（媒体） |
|:---|:---|:---|
| 入口判别 | ingest_entry_judge（课程包） | smarttext_router（文本/数据信号） |
| 预处理 | ingest_raw_material（PDF/OCR/古籍） | 路由+格式化（无需OCR） |
| 质量校准 | 双Agent对抗（书法/历史专业） | 快速可信度打分（G-SOURCE/G-TIMELINESS） |
| 核心差异 | **自含生产型** | **协调分发型** |
