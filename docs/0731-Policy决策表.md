# SPDT-005 Policy 决策表
> 将管线中的隐式决策规则显式化，便于维护、审计和迭代
> 版本：v1.0 | 2026-07-31
>
> **定位：** 这是"元 Agent 的宪法"，不是业务规则手册

---

## 一、Policy 的两层含义

```
业务 Policy（business_policy/）
  └── 业务逻辑规则：来源等级划分、内容安全红线、灰区判断
        ↓ 不写入本表，写入 content_type_registry.yaml gray_zone_rules

管线 Policy（PipelinePolicy — 本表）
  └── 构建期决策：checkpoint 动作、模块加载策略、阈值判定、失败处理
        ↓ 写入本表，由 PolicyAuditLogger 记录和追踪
```

---

## 二、Checkpoint 决策规则

### M1 — 选题阶段（ingest 后）

| checkpoint_action | 触发条件 | 行为 | 审计事件 |
|:---|:---|:---|:---|
| `skip` | 内容类型已预设选题规则 | 自动通过 | `checkpoint_pass_auto` |
| `confirm` | 选题规则尚未模板化 | 创建 CHK 工单，等待编辑确认 | `checkpoint_hold` |
| `fast_confirm` | 选题规则部分模板化 | 创建 CHK 工单，值班编辑快速确认 | `checkpoint_hold` |

**当前配置（breakdown_news）：** `skip` ✅ 无 gap
**当前配置（science_fact）：** `skip` ✅ 无 gap

---

### M2 — 结构阶段（structure 后）

| checkpoint_action | 触发条件 | 行为 | 审计事件 |
|:---|:---|:---|:---|
| `skip` | 结构已模板化（大纲固定）| 自动通过 | `checkpoint_pass_auto` |
| `confirm` | 结构灵活性高，需人工确认 | 创建 CHK 工单 | `checkpoint_hold` |
| `fast_confirm` | 结构大部分模板化 | 创建 CHK 工单，值班编辑快速确认 | `checkpoint_hold` |
| `chief_signoff` | 高风险内容，需主编审批 | 创建 CHK 工单，主编审批 | `checkpoint_hold` |

**当前配置（breakdown_news）：** `skip` ✅ 无 gap
**当前配置（science_fact）：** `skip` ✅ 无 gap

---

### M3 — 渲染阶段（render 后）

| checkpoint_action | 触发条件 | 行为 | 审计事件 |
|:---|:---|:---|:---|
| `skip` | 内容已模板化，语气自动生成 | 自动通过 | `checkpoint_pass_auto` |
| `confirm` | 新语气风格首次使用 | 创建 CHK 工单 | `checkpoint_hold` |
| `standard` | 标准确认流程 | 创建 CHK 工单，编辑确认 | `checkpoint_hold` |

**当前配置（breakdown_news）：** `skip` ✅ 无 gap
**当前配置（science_fact）：** `skip` ✅ 无 gap

---

### M4 — 质量阶段（adapt 后）

| checkpoint_action | 触发条件 | 行为 | 审计事件 |
|:---|:---|:---|:---|
| `threshold_70` | breakdown_news：总分 < 70 | FAIL，停止管线 | `quality_gate_failed` |
| `threshold_70` | breakdown_news：总分 ≥ 70 | 继续 | `quality_gate_passed` |
| `threshold_65` | deep_industry_report：总分 < 65 | FAIL，停止管线 | `quality_gate_failed` |
| `threshold_65` | deep_industry_report：总分 ≥ 65 | 继续 | `quality_gate_passed` |
| `skip` | 测试/开发阶段 | 自动通过 | `checkpoint_pass_auto` |

**分数维度一票否决规则：**

| 内容类型 | 维度 | 阈值 | 超过则 |
|:---|:---|:---|:---|
| breakdown_news | factual | < 60 | FAIL（一票否决）|
| science_fact | factual | < 70 | FAIL（一票否决）|
| science_fact | citation_check | < 50 | WARN + 降级发布 |

---

### M5 — 交付阶段（deliver 后）

| checkpoint_action | 触发条件 | 行为 | 审计事件 |
|:---|:---|:---|:---|
| `skip` | 自动交付 | 自动通过 | `checkpoint_pass_auto` |
| `confirm` | 新渠道首次使用 | 创建 CHK 工单 | `checkpoint_hold` |

**当前配置（breakdown_news）：** `skip` ✅ 无 gap

---

### M6 — 发布阶段（发布前最后确认）

| checkpoint_action | 触发条件 | 行为 | 审计事件 |
|:---|:---|:---|:---|
| `skip` | 自动发布 | 直接发布 | `checkpoint_pass_auto` |
| `fast_confirm` | 值班编辑快速确认 | 值班编辑确认后发布 | `checkpoint_hold` |
| `chief_signoff` | 高风险内容 | 主编审批后发布 | `checkpoint_hold` |

**当前配置（breakdown_news）：** `skip` ✅ 无 gap

---

## 三、路由决策规则

| 场景 | matched_rule | 行为 | 审计事件 |
|:---|:---|:---|:---|
| content_type 在 registry 中注册 | `content_type:<type>` | 使用对应路由配置 | `route_resolved` |
| content_type 未注册 | `default_route` | 回退到通用路由 | `route_fallback`（gap=true）|

**gap 修复流程：** 若出现 `route_fallback` → 在 `content_type_registry.yaml` 中注册该类型 → 下次自动消失

---

## 四、灰区决策规则

| 触发条件（关键词）| 行为 | 审计事件 |
|:---|:---|:---|
| 涉及政治/领导人/领土 | `hold_publish` | `gray_zone_triggered` |
| 伤亡人数/损失规模 | `double_verify` | `gray_zone_triggered` |
| 食品安全/医疗健康（science_fact）| `hold_publish` | `gray_zone_triggered` |
| 仅 arXiv 预印本（science_fact）| `flag_source_grade` | `gray_zone_triggered` |
| source_grade 全为 C 级 | `double_verify` | `gray_zone_triggered` |

**gap 修复流程：** 若出现新的灰区触发 → 评估是否应常态化处理 → 补入 registry 或本表

---

## 五、失败决策规则

| 失败类型 | 触发条件 | 行为 | 审计事件 |
|:---|:---|:---|:---|
| 阶段异常 | 任何阶段抛出 Exception | 停止管线，记录错误 | `stage_failed` |
| LLM 调用失败 | API 返回错误或超时 | 重试 1 次，失败则 FAIL | `stage_failed` |
| 模块加载失败 | `_get_module()` 返回 None | 回退到骨架模式 | `route_fallback` |

**骨架模式回退规则：**

| 阶段 | 回退行为 |
|:---|:---|
| ingest | 返回空骨架 artifact，不崩溃 |
| structure | 返回空大纲 artifact |
| render | 返回空内容 artifact |
| adapt | 返回零分 scorecard |
| deliver | 返回空 channel_packages |

---

## 六、审计 Gap 分类与修复指南

### Gap 类型速查

| gap | 含义 | 立即行动 |
|:---|:---|:---|
| `route_fallback` | 类型未注册 | 注册到 registry.yaml |
| `checkpoint_hold` | 需要人工确认 | 评估是否可 skip / 快速确认 |
| `quality_gate_failed` | 质量不达标 | 调 LLM prompt 或调整阈值 |
| `stage_failed` | 代码异常 | 查看 error 字段，修复代码 |
| `gray_zone_triggered` | 触发灰区 | 人工介入，或升级灰区规则 |
| `decision_unmatched` | 未知 action | 补规则到本表 |

### Policy 覆盖度评分公式

```
覆盖度 = (total_events - gap_events) / total_events × 100%
```

| 覆盖度 | 含义 | 行动 |
|:---|:---|:---|
| ≥ 90% | 优秀，可开始无人值守 | 减少人工介入 |
| 70-89% | 良好，持续迭代 | 优先修复高频 gap 类型 |
| 50-69% | 一般，需重点改进 | 补齐高优先级规则 |
| < 50% | 不足，暂不推荐自治 | 全面补规则后再跑 |

---

## 七、Policy 迭代记录

| 日期 | 版本 | 变更内容 | 原因 |
|:---|:---|:---|:---|
| 2026-07-31 | v1.0 | 初始版本，基于 breakdown_news 运行数据 | 首次系统化整理 |
| | | | |
| | | | |

---

*Policy 表由 PolicyAuditLogger 自动维护，每次运行后检查 gap_events > 0 的事件即可发现新缺口*
