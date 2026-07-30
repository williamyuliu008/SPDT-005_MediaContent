# SPDT-005 内容管线 SOP v1.0
> 自适应 AI 备考智能体内容管线 · 运营标准手册
> 版本：v1.0 | 2026-07-31 | 状态：已验证（P0+P1 双类型实战）

---

## 一、定位与理念

### 1.1 什么是"长程任务自动化"

长程任务指需要多阶段执行、有质量门槛、可能遇到异常的业务流程。

```
传统方式：  设计 → 执行 → 卡住 → 问人 → 继续 → 问人 → 完成
长程方式：  预热（冻结设计）→ 自动执行 → Policy 驱动决策 → 审计闭环
```

**核心原则：把"不确定性"在开始前消耗掉，执行阶段几乎不消耗人工注意力。**

### 1.2 本 SOP 的适用范围

| 场景 | 适用性 |
|:---|:---|
| 新增内容类型（如科学事实、深度报告）| ✅ 直接使用模板 |
| 现有内容类型的配置变更 | ✅ 参照 §四 |
| 新增灰区规则或 checkpoint 策略 | ✅ 参照 §六 |
| 质量问题排查 | ✅ 参照 §八 audit_analyzer |
| 跨团队 SOP 推广 | ✅ 模板可直接复用到其他项目 |

### 1.3 关键设计原则

| 编号 | 原则 | 为什么重要 |
|:---|:---|:---|
| D1 | **设计冻结后执行** | 预热阶段完成后，代码实现无需再问人 |
| D2 | **验证内建于流程** | 每个模块跑通 + Scorecard 评分卡双重验收 |
| D3 | **失败有回滚点** | 每阶段 artifact 持久化，随时可回退 |
| D4 | **Policy 覆盖 90% 才开始自治** | gap_events = 0 是无人值守的前提 |
| D5 | **每次运行后审计** | `policy_audit.jsonl` 是管线的"眼睛" |
| D6 | **通用骨架 + 类型插件分离** | SOP 演进只改骨架，类型插件独立演进 |

---

## 二、三阶段工作流

### 阶段 1：交互预热（冻结设计）

**目标：用对话把最大不确定性消耗掉。开始写代码前，填完 §三的设计模板。**

预热检查清单（7 个子节，必须全部完成）：

```
┌─────────────────────────────────────────────────────────────┐
│  交互预热检查清单                                            │
├─────────────────────────────────────────────────────────────┤
│  1. 定位          内容解决什么问题？受众是谁？成功标准？         │
│  2. 数据来源       数据从哪来？触发条件？有无 Mock 数据？        │
│  3. 结构设计       输出大纲是什么？知识节点有哪些？             │
│  4. 语气与风格     文学性/专业深度？禁止表达？参考风格？         │
│  5. 质量标准       阈值？哪个维度一票否决？                    │
│  6. 交付渠道       需要哪些 channel？特殊格式要求？            │
│  7. 异常与灰区     哪些情况需人工介入？触发规则？              │
└─────────────────────────────────────────────────────────────┘
```

### 阶段 2：自动化执行（Policy 驱动）

**目标：代码实现 + 自动跑通 + 审计日志记录。**

执行顺序（固定顺序，不可跳步）：

```
Step 1  写 content_type_registry.yaml 配置（ humanas checkpoints + gray_zone_rules）
Step 2  实现 ingest 模块（radar_*.py，RadarXXX + RadarXXXRequest）
Step 3  实现 structure 模块（article_*.py，ArticleXXX + ArticleXXXResult）
Step 4  实现 render 模块（render_*.py，RenderXXX + RenderXXXResult）
Step 5  实现 adapt 模块（scorecard_*.py，ScorecardXXX + ScorecardXXXResult）
Step 6  注册到 CONTENT_TYPE_MODULES（pipeline_router.py）
Step 7  运行 pipeline → 采集 audit log
Step 8  运行 audit_analyzer.py → 分析 gap_events
Step 9  修复 gap → 重复 Step 7-8 直至 gap_events = 0
Step 10 验收测试（mock 通过 + score ≥ 阈值 + markdown 输出可读）
```

### 阶段 3：方法论固化

**目标：从实战经验提炼可复用模板。**

- 每次实战后，更新设计模板中的"已完成"条目
- 每次 gap 修复后，更新 Policy 决策表
- 工具改进后，更新 SOP §八

---

## 三、新增内容类型 · 设计模板

> 使用方式：复制本节 → 填写作弊表 → 进入阶段 2

### §3.1 元信息

```yaml
meta:
  name: <snake_case_英文标识符>
  label: <中文显示名称>
  version: "1.0"
  created: "2026-07-31"
  owner: <负责人>
  description: <一句话描述>
```

### §3.2 定位

| 问题 | 答案 |
|:---|:---|
| 这个内容解决什么需求？ | |
| 受众是谁？ | |
| 成功标准是什么？ | |
| 失败代价是什么？ | |

### §3.3 数据来源（ingest）

| 问题 | 答案 |
|:---|:---|
| 主要数据源是什么？ | |
| 触发条件是什么？ | |
| 哪些来源不可用？ | |
| 是否有 Mock 版本？ | |

### §3.4 结构设计（structure）

| 问题 | 答案 |
|:---|:---|
| 标准结构是什么？ | |
| 知识节点有哪些？ | |
| 是否有标准模板？ | 是（由 article_*.py 提供）|

### §3.5 语气与风格（render）

| 问题 | 答案 |
|:---|:---|
| 文学性维度（1-5）| |
| 专业深度维度（1-5）| |
| 禁止使用的表达？ | |
| 参考风格？ | |

### §3.6 质量标准（adapt）

| 问题 | 答案 |
|:---|:---|
| 最低分阈值是多少？ | |
| 哪个维度一票否决？ | |
| 评分权重如何分配？ | |
| 是否需要特殊评分维度？ | |

### §3.7 交付渠道

| 问题 | 答案 |
|:---|:---|
| 需要哪些 channel？ | markdown（必选）|
| 是否有特殊格式要求？ | |

### §3.8 异常与灰区

| 场景 | 处理策略 |
|:---|:---|
| | |
| | |

---

## 四、模块实现规范

### 4.1 命名约定

所有新增模块必须遵循以下命名约定：

```
platform/1_ingest/radar/radar_<type>.py
platform/2_structure/article/article_<type>.py
platform/3_render/engines/text/render_<type>.py
platform/4_adapt/scorecard/scorecard_<type>.py
```

**类名约定：**

| 阶段 | 类名 | 结果类名 |
|:---|:---|:---|
| ingest | `Radar<Type>` | — |
| ingest request | `Radar<Type>Request` | — |
| structure | `Article<Type>` | `Article<Type>Result` |
| render | `Render<Type>` | `Render<Type>Result` |
| adapt | `Scorecard<Type>` | `Scorecard<Type>Result` |

**Request 类必须包含 `max_signals` 参数（pipeline_router.py 依赖）：**

```python
@dataclass
class RadarDeepIndustryRequest:
    topic: str
    max_signals: int = 5   # ← 必须有此参数
    industry: str = ""
    # ... 其他参数
```

### 4.2 通用模块结构

每个模块必须包含：

```python
# -*- coding: utf-8 -*-
"""
<module>.py — <content_type> IF-P-<N>：<功能一句话描述>
================================================================
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ── 路径配置（使用 importlib.util.spec_from_file_location 避免命名冲突）─
REPO_ROOT = Path(__file__).resolve().parents[N]  # N 根据深度调整
LLM_GATEWAY_PATH = REPO_ROOT / "platform" / "shared" / "llm_gateway.py"

def _load_llm_gateway():
    import importlib.util, sys
    cache_key = "_spdt_llm_gateway"
    if cache_key in sys.modules:
        return sys.modules[cache_key]
    spec = importlib.util.spec_from_file_location(cache_key, str(LLM_GATEWAY_PATH))
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module

# ── 数据类定义 ────────────────────────────────────────────────

@dataclass
class Scorecard<Type>Result:
    scorecard: dict
    passed: bool
    action: str   # "deliver" / "revise" / "reject"
    gray_zones: list[str] = field(default_factory=list)

class Scorecard<Type>:
    WEIGHTS = {...}          # 评分权重（与 registry 一致）
    FACTUAL_THRESHOLD = 70.0  # 一票否决阈值

    def run(self, article: dict) -> Scorecard<Type>Result:
        if self._is_mock_mode():
            return self._run_mock(article)
        return self._run_real(article)

    def _is_mock_mode(self) -> bool:
        import os
        return not bool(os.environ.get("DEEPSEEK_API_KEY"))
```

### 4.3 pipeline_router.py 注册

在 `CONTENT_TYPE_MODULES` 字典中添加：

```python
"<content_type>": {
    "ingest":    ("platform.1_ingest.radar.radar_<type>",   "Radar<Type>"),
    "structure": ("platform.2_structure.article.article_<type>", "Article<Type>"),
    "render":    ("platform.3_render.engines.text.render_<type>", "Render<Type>"),
    "adapt":     ("platform.4_adapt.scorecard.scorecard_<type>", "Scorecard<Type>"),
},
```

同时在 `_default_topic_for_type()` 中添加默认值。

### 4.4 Scorecard 输出结构规范

所有 Scorecard 必须返回以下嵌套结构：

```python
result.scorecard = {
    "header": {
        "artifact_id": "...",
        "artifact_type": "quality_scorecard",
        "content_type": "<type>",
        "scored_at": "<iso_timestamp>",
        "producer": "<module_path>",
        "mock_mode": True/False,
    },
    "scorecard": {                          # ← 关键：两层 scorecard
        "total_score": 89.2,
        "dimensions": {
            "<dim>": {"score": N, "weight": W},
            ...
        },
        "weights": {...},
        "threshold": 70.0,
    },
    "passed": True,
    "action": "deliver",
    "gray_zones": [],
    "revision_suggestions": [],
}
```

**⚠️ 重要：`result.scorecard["scorecard"]["total_score"]` 是真实总分，不是 `result.scorecard["total_score"]`。**

---

## 五、Checkpoint 策略

### 5.1 决策规则（M1-M6）

| Checkpoint | action=skip | action=confirm | action=fast_confirm |
|:---|:---|:---|:---|
| M1（选题）| 结构已模板化 | 选题灵活性高 | 大部分已模板化 |
| M2（结构）| 大纲已固定 | 结构灵活性高 | 大部分已模板化 |
| M3（渲染）| 语气已模板化 | 新语气首次用 | 大部分已模板化 |
| M4（质量）| `threshold_<N>` | — | — |
| M5（交付）| 自动交付 | 新渠道首次 | 大部分已模板化 |
| M6（发布）| 自动发布 | 值班编辑确认 | 主编审批 |

### 5.2 各内容类型 Checkpoint 配置

| 内容类型 | M1 | M2 | M3 | M4 | M5 | M6 | 状态 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| breakdown_news | skip | skip | skip | threshold_70 | skip | skip | ✅ 无 gap |
| science_research | skip | skip | skip | threshold_70 | skip | skip | ✅ 无 gap |
| deep_industry_report | skip | skip | skip | threshold_85 | skip | skip | ✅ 无 gap |

### 5.3 添加新 checkpoint 策略

```
在 content_type_registry.yaml 的 humanas_checkpoints 中添加：
  M1: "skip"      # 自动通过
  M4: "threshold_70"  # 70 分阈值
```

---

## 六、灰区规则

### 6.1 灰区决策矩阵

| 触发关键词 | 行为 | 审计事件 |
|:---|:---|:---|
| 涉及政治/领导人/领土 | `hold_publish` | `gray_zone_triggered` |
| 伤亡人数/损失规模 | `double_verify` | `gray_zone_triggered` |
| 食品安全/医疗健康 | `hold_publish` | `gray_zone_triggered` |
| 涉及竞争对手负面 | `legal_review` | `gray_zone_triggered` |
| 仅 arXiv 预印本（科学类）| `flag_source_grade` | `gray_zone_triggered` |
| A股上市公司财报 | `flag_source_grade` | `gray_zone_triggered` |
| source_grade 全为 C 级 | `double_verify` | `gray_zone_triggered` |
| 涉及政策预测 | `expert_signoff` | `gray_zone_triggered` |

### 6.2 添加新灰区规则

```
在 content_type_registry.yaml 的 gray_zone_rules 中添加：
  - trigger: "<关键词>"
    action: "<行为>"
```

**行为类型：**

| action | 含义 |
|:---|:---|
| `hold_publish` | 暂停发布，等待人工审核 |
| `double_verify` | 双重核实后再决定 |
| `flag_source_grade` | 标注来源等级降级 |
| `legal_review` | 法务审核 |
| `expert_signoff` | 专家签字 |
| `auto_archive` | 自动归档 |

---

## 七、评分权重配置

### 7.1 各类型权重总表

| 内容类型 | factual | source | depth | readability | timeliness | 阈值 | 一票否决 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| breakdown_news | 35% | 20% | — | 20% | 25% | 70 | factual < 60 |
| science_research | 35% | 20% | 20% | 25% | — | 70 | factual < 70 |
| deep_industry_report | 30% | 25% | 20% | 15% | 10% | 85 | factual < 70 |

### 7.2 调整评分权重

```
在 content_type_registry.yaml 的 scorecard_weights 中调整。
⚠️ 必须同时更新对应 scorecard_*.py 中的 WEIGHTS 字典。
```

---

## 八、审计与 Gap 分析

### 8.1 policy_audit.jsonl 事件类型

| event_type | gap | 含义 | 立即行动 |
|:---|:---:|:---|:---|
| `route_resolved` | ❌ | 正常路由命中 | 无需处理 |
| `route_fallback` | ✅ | 类型未注册 | 注册到 registry |
| `checkpoint_pass_auto` | ❌ | checkpoint 自动通过 | 无需处理 |
| `checkpoint_hold` | ✅ | 等待人工确认 | 评估是否改 skip |
| `checkpoint_pass` | ❌ | 人工确认通过 | 无需处理 |
| `quality_gate_passed` | ❌ | 质量门通过 | 无需处理 |
| `quality_gate_failed` | ✅ | 质量未达标 | 调 prompt 或阈值 |
| `stage_failed` | ✅ | 阶段执行失败 | 修复代码 + 补规则 |
| `gray_zone_triggered` | ✅ | 灰区触发 | 人工介入或升级规则 |
| `decision_unmatched` | ✅ | 未知决策分支 | 补 Policy 规则 |

### 8.2 audit_analyzer.py 使用

```bash
# 查看 Markdown 报告
python tools/audit_analyzer.py

# 输出到文件
python tools/audit_analyzer.py --output tools/audit_report.md

# JSON 格式（程序调用）
python tools/audit_analyzer.py --json

# 分析指定日志文件
python tools/audit_analyzer.py --log platform/5_deliver/checkpoint/policy_audit.jsonl
```

### 8.3 Policy 覆盖率评分

```
覆盖度 = (total_events - gap_events) / total_events × 100%
```

| 覆盖度 | 状态 | 行动 |
|:---:|:---:|:---|
| ≥ 90% | 🟢 优秀 | 可开始无人值守 |
| 70-89% | 🟡 良好 | 优先修复高频 gap 类型 |
| 50-69% | 🟠 一般 | 补齐高优先级规则 |
| < 50% | 🔴 不足 | 全面补规则后再自治 |

### 8.4 Gap 修复流程

```
每次运行后执行：
  python tools/audit_analyzer.py --json
       ↓
  发现 gap_events > 0？
       ↓ 是
  gap_groups[].event_type 判断：
       ├─ route_fallback    → 注册到 registry
       ├─ checkpoint_hold   → 改为 skip 或 fast_confirm
       ├─ quality_gate_failed → 调 LLM prompt 或降低阈值
       ├─ stage_failed     → 查看 pipeline_router.py error 字段
       ├─ gray_zone_triggered → 人工介入或升级 gray_zone_rules
       └─ decision_unmatched  → 在 Policy 决策表补充规则
       ↓
  更新 registry / checkpoint 配置
       ↓
  重新运行 pipeline
       ↓ 直到 gap_events = 0
```

---

## 九、Markdown 输出规范

### 9.1 标准格式

```markdown
---
title: "<标题>"
content_type: <类型>
publish_time: <ISO时间>
keywords: [<关键词列表>]
---

# <标题>

## 摘要
<核心观点>

## <章节1>
...

## <章节N>

## 参考来源
【A级/机构研报】Bloomberg Industry Intelligence
【B级/行业媒体】36氪

---

**质量评分** | 总分: 89.2 | 可读性: 88 | 事实性: 100 | 来源: 85 | 深度: 100
```

### 9.2 各类型的 Markdown 结构

| 内容类型 | 必须章节 |
|:---|:---|
| breakdown_news | 标题 + 导语 + 正文 + 来源 |
| science_research | 标题 + 摘要 + 背景/原理/证据/局限/意义 + 来源 |
| deep_industry_report | 标题 + 摘要 + 背景/核心发现/深度分析/趋势预判/结论建议 + 来源 |

---

## 十、实战清单（每新增一个内容类型）

> 复制此清单，每完成一项打 ✅

```
□ §三：设计模板填写完成（7 个子节全部）
□ radar_<type>.py 实现完成（Mock + Real 模式）
□ article_<type>.py 实现完成（大纲模板 + LLM 生成）
□ render_<type>.py 实现完成（语气规则 + 来源标注）
□ scorecard_<type>.py 实现完成（权重 + 阈值 + 一票否决）
□ content_type_registry.yaml 更新（humanas checkpoints + gray_zone_rules + scorecard_weights）
□ pipeline_router.py CONTENT_TYPE_MODULES 注册
□ _default_topic_for_type() 添加默认值
□ pipeline 运行测试 → 5 阶段全部 PASS
□ audit_analyzer.py 运行 → gap_events = 0
□ 总分 ≥ 阈值
□ Markdown 输出可读（含 frontmatter + 章节结构 + 来源）
□ GitHub 提交并推送
```

---

## 十一、版本记录

| 日期 | 版本 | 变更内容 | 验证状态 |
|:---|:---|:---|:---|
| 2026-07-31 | v1.0 | 初始版本，整合 P0 science_research + P1 deep_industry_report 实战经验 | ✅ P0 验证通过，P1 验证通过 |
| | | | |

---

*本文档基于 SPDT-005 平台 v2.0 管线架构，通过 science_research 和 deep_industry_report 两个内容类型的实战验证。*
*每新增一个内容类型后，更新 §十清单和 §十一版本记录。*
