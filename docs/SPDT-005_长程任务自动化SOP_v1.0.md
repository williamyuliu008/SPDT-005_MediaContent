# SPDT-005 内容管线 SOP v1.4
> 自适应 AI 备考智能体内容管线 · 运营标准手册
> 版本：v1.4 | 2026-07-31 | 新增：§十一自动化开发框架 + CI/CD规范

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
Step 10 验收测试 — Mock 门控
  运行 `_run_<type>.py`（无 DEEPSEEK_API_KEY）→ mock 模式
  通过条件：模块不 crash + scorecard 返回 action = deliver/revise/reject（结构正确）

Step 11 验收测试 — 真实 LLM 门控 ⚠️ 【v1.3 新增】
  运行 `_run_<type>.py`（设置 DEEPSEEK_API_KEY）→ 真实 API 调用
  通过条件（必须全部满足）：
    ✓ 全流程 4 阶段 hit，无 crash
    ✓ scorecard score ≥ 阈值
    ✓ markdown 正文长度 ≥ 类型要求（见 §3.3）
    ✓ 所有维度分数 ≥ 各自否决线
    ✓ 记录到 policy_audit.jsonl
  注意：每次新增内容类型或 render 改动后必须执行此门控

> **为什么要单独设立 Step 11？**
> v1.2 的教训：science_research、deep_industry_report、oped_argument 三个内容类型的 Step 10（mock）
> 全部通过，但在 Step 11（真实 LLM）验收时才发现：markdown 字段缺失、JSON 解析失败
> （deep_industry 被截断）、readability 不达标（science_readability=73）。Mock 通过不意味着
> 真实 LLM 通过——两者是独立的验收门控。
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
| 是否要求真实联网采集？ | **判断标准见下表** |
| 真实采集失败时的 fallback 策略？ | |

**真实联网 vs Mock 模式判定规则（v1.3 新增）：**

```
是否需要真实联网采集？
│
├─ 内容类型是否属于"情报产品"（时效性 > 24h）？
│   └─ 是 → 必须真实联网（Fail → fallback 到 LLM 记忆，但需记录 gray_zone）
│   └─ 否（知识解读型）→ 优先真实联网，失败则 LLM 记忆可接受
│
├─ 内容是否涉及具体数字/统计数据？
│   └─ 是 → 真实联网采集（LLM 记忆数字不可信）
│   └─ 否（定性分析型）→ Mock 可接受，但真实 LLM 测试必须做
│
└─ 是否有可用的采集 API/工具？
    └─ 有 → 优先接入；无 → 在 gray_zone_rules 中记录为 KnownLimitation
```

**各内容类型的采集要求：**

| 内容类型 | 采集要求 | fallback |
|:---|:---|:---|
| `breakdown_news` | ✅ 必须真实联网 | ❌ 无 fallback（超过 SLA 即废弃）|
| `deep_industry_report` | ✅ 必须真实联网（数据驱动）| LLM 记忆（标注 gray_zone）|
| `science_research` | ✅ 必须真实联网（同行评审来源）| LLM 记忆（标注 gray_zone）|
| `oped_argument` | ✅ 优先真实联网 | LLM 记忆（允许）|
| `science_fact` | ✅ 优先真实联网 | LLM 记忆（允许）|

> **执行原则（v1.3）**：Mock 模式用于开发调试，真实 LLM 验收（Step 11）是**发布前必须通过的强制门控**。Step 10（mock 通过）不是终点，Step 11（真实 LLM 通过）才是。

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

### 4.0 内容类型速查与选型指南

> 所有已注册内容类型一览，包含已实现（✅）和规划中（📋骨架）。

| 类型 | routing_hint | 状态 | 核心场景 | SLA | 阈值 | 说明 |
|:---|:---|:---|:---|:---:|:---:|:---|
| `breakdown_news` | `breaking` | ✅ | 突发事件/危机/重大政策 | — | 70 | 突发快讯，最快速通道 |
| `science_research` | `news_report` | ✅ | 有新论文/新发现触发的科研报道 | 2h | 70 | 五段式叙事，快而准 |
| `deep_industry_report` | `industry_deep` | ✅ | 3000-8000字行业深度分析 | 4h | 85 | 专业受众，数据驱动 |
| `science_fact` | `deep_knowledge` | 📋骨架 | 长效知识点深度科普（非触发式）| 4h | 75 | 知识图谱结构，面向大众 |
| `oped_argument` | `opinion` | 📋骨架 | 有明确立场的评论文章 | — | — | 需逻辑性和事实支撑 |
| `product_review` | `review` | 📋骨架 | 产品测评/对比分析 | — | — | 需利益披露检查 |
| `creative` | `creative` | 📋骨架 | 创意写作/故事类内容 | — | — | 真实人物需授权 |

**选型决策树：**
```
内容触发方式？
  ├─ 突发事件/危机  → breakdown_news
  ├─ 新论文/新发现 → science_research  （科研快讯，2h）
  └─ 无触发，常态化科普
       ├─ 知识点图谱深度  → science_fact  （规划中，知识图谱）
       └─ 行业深度分析    → deep_industry_report

内容类型定位？
  ├─ 需要数据驱动、行业专业受众 → deep_industry_report
  ├─ 需要客观报道，有据可查     → science_research
  └─ 需要逻辑论战，明确立场     → oped_argument  （规划中）
```

**关于 science_research vs science_fact：**
两者不是重复设计，而是针对不同创作任务的合理分工：

| 维度 | science_research（✅已实现）| science_fact（📋规划中）|
|:---|:---|:---|
| 触发方式 | 事件驱动（新论文/发现）| 常态化选题 |
| 速度要求 | SLA=2h，快 | SLA=4h，深 |
| 核心能力 | 五段式叙事，快速准确 | 知识图谱，深度可读 |
| accuracy 维度 | 4（高）| 5（极高，医疗级）|

---

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

### 4.5 Runner 脚本规范（v1.3 新增）

每个内容类型必须配套一个 `_run_<type>.py` 脚本，用于 Step 10（Mock）和 Step 11（真实 LLM）验收测试。

**必须包含的要素：**

```python
# -*- coding: utf-8 -*-
"""
_run_<type>.py — <content_type> Step 10/11 验收脚本
=====================================================
用途：Mock 验收（Step 10）+ 真实 LLM 验收（Step 11）
依赖：DEEPSEEK_API_KEY 环境变量（未设置 = mock 模式）
"""
import sys, os, json, time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
_RUN_TS = str(int(time.time() * 1000))  # ← 必须时间戳前缀，避免模块缓存


def load_module(file_path, cache_key):
    import importlib.util
    key = f"{_RUN_TS}_{cache_key}"      # ← 必须带时间戳
    spec = importlib.util.spec_from_file_location(key, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def get_dict(obj):
    """安全提取 dict"""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict as _asdict
        return _asdict(obj)
    return dict(obj) if obj else {}


# 4 个模块必须分别用不同 cache_key 加载（避免阶段间污染）
RADAR   = load_module(REPO_ROOT / "platform/1_ingest/radar/radar_<type>.py",       "_m_<t>1")
ARTICLE = load_module(REPO_ROOT / "platform/2_structure/article/article_<type>.py", "_m_<t>2")
RENDER  = load_module(REPO_ROOT / "platform/3_render/engines/text/render_<type>.py", "_m_<t>3")
SCARD   = load_module(REPO_ROOT / "platform/4_adapt/scorecard/scorecard_<type>.py", "_m_<t>4")

# Step 1-4 流程...
# 提取 score...
# 验证 markdown 字段存在且长度 > 类型要求

# 验收断言
assert score >= THRESHOLD, f"Score {score} < {THRESHOLD}"
assert len(markdown) >= MIN_MARKDOWN_CHARS, f"Markdown {len(markdown)} < {MIN_MARKDOWN_CHARS}"
print(f"✅ Step {'10/11' if os.environ.get('DEEPSEEK_API_KEY') else '10'} PASSED")
```

**markdown 字段输出最低要求（v1.3 新增）：**

| 内容类型 | 最低正文长度 |
|:---|---:|
| `breakdown_news` | 300 字 |
| `science_research` | 800 字 |
| `deep_industry_report` | 2000 字 |
| `oped_argument` | 600 字 |

> **常见 bug（v1.3 教训）：**
> 1. render 模块返回 `article` 时缺少 `markdown` 字段 → 脚本取到空字符串
> 2. `_load_llm_gateway()` 使用固定 cache key → 代码更新后不重新加载
> 3. LLM 返回 JSON 被截断 → 改用 `structured()` 模式 + 括号平衡提取

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
| `hold_publish` | 暂停发布，等待人工审核（医疗/法律/真实人物/未成年人）|
| `double_verify` | 双重核实后再决定（数据来源/政策预测）|
| `flag_source_grade` | 标注来源等级降级（affiliate链接/单一来源）|
| `legal_review` | 法务审核（竞争对手负面/合规争议）|
| `expert_signoff` | 专家签字（政策预测/学术争议）|
| `auto_archive` | 自动归档（超期/低优先级）|
| `source_upgrade` | 要求升级来源（C级来源升级为A/B级）|

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
| oped_argument | 标题 + 钩子/核心论点/支撑论据/对立论点/反驳/结论/行动号召 + 来源 |

---

## 十一、自动化开发框架（v1.4 新增）

> **设计理念**：SOP 不仅是"内容运营手册"，也是"内容类型开发方法论"。
> 核心原则——**真实 LLM 是开发过程的一部分，不是开发完成后的额外测试**。
>
> 真实 LLM 在开发中有三个角色：
> - **D-1 骨架辅助**：输入 §三设计模板，LLM 辅助生成 4 模块骨架代码
> - **D-4 强制门控**：render 模块任何改动后，必须跑 Step 11 真实 LLM，PASS 才并入主线
> - **D-5 对抗验证**：用 adversarial_audit.py 对新类型做对抗性测试

### 11.1 SOP 驱动开发流程

当需要新增一个内容类型时，遵循以下加速工作流（D = Develop 阶段）：

```
┌──────────────────────────────────────────────────────────────────────┐
│  SOP 驱动开发工作流（内容类型开发加速器）                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  D-0  选定内容类型                                                     │
│          填写 §三 设计模板（7 个子节必须全部完成）                        │
│          填写 §七 评分权重                                             │
│          定义 §六 灰区规则                                             │
│                                                                       │
│  D-1  骨架生成（LLM 辅助）                                            │
│          输入：§三 + §四类模板                                         │
│          输出：radar_<type>.py 骨架                                   │
│          验证：模块能 import + dataclass 结构正确                       │
│          工具：参考 tools/sop_develop.py 规范（§11.2）                  │
│                                                                       │
│  D-2  四模块实现（参考已有点）                                          │
│          参考 science_research / deep_industry / oped_argument 的实现   │
│          遵循 §四 §七 规范                                             │
│          命名约定：radar_<type>.py / article_<type>.py /               │
│                   render_<type>.py / scorecard_<type>.py             │
│                                                                       │
│  D-3  Mock 门控（Step 10）                                            │
│          _run_<type>.py（无 DEEPSEEK_API_KEY）→ mock 模式             │
│          验证：4 阶段全部 PASS                                         │
│                scorecard 返回结构正确（passed / action 字段存在）        │
│                                                                       │
│  D-4  真实 LLM 门控（Step 11）⚠️ 【强制门控，开发的一部分】              │
│          _run_<type>.py（设置 DEEPSEEK_API_KEY）→ 真实 API 调用        │
│          必须全部满足：                                                 │
│            ✓ 4 阶段全部 PASS，无 crash                                 │
│            ✓ scorecard score ≥ 阈值（§七）                            │
│            ✓ markdown 正文长度 ≥ 类型最低要求（§4.5）                   │
│            ✓ 所有维度分数 ≥ 各自否决线（§七）                          │
│            ✓ policy_audit.jsonl 有记录                                │
│          失败处理：gray_zone 记录 → 修复 prompt → 重跑 D-4             │
│                                                                       │
│  D-5  对抗性审核                                                       │
│          python tools/adversarial_audit.py                            │
│          验证：critical findings ≤ 3                                  │
│                                                                       │
│  D-6  SOP 更新                                                        │
│          §三 末尾加入新类型设计模板（"已完成"状态）                      │
│          §四 §四.0 表格加入新行                                        │
│          §十 清单加入新类型                                            │
│          版本升级 v1.N → v1.N+1                                       │
│                                                                       │
│  D-7  CI/CD 接入（可选但推荐）                                         │
│          .github/workflows/llm-acceptance.yml（§11.3）                  │
│          push 后自动触发所有类型的 Step 11                             │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 11.2 sop_develop.py 开发加速器规范（规划中）

> **v1.4 状态**：规范定义，工具待实现。
> 预计 v1.5 完成。

`sop_develop.py` 是 SOP 驱动的骨架生成工具。输入 §三设计模板的 YAML/JSON，输出完整 4 模块骨架。

**输入 schema**：

```yaml
meta:
  name: "deep_industry_report"   # snake_case
  label: "深度行业报告"
  version: "1.0"
content_spec:
  target: "3000-8000字行业深度分析"
  audience: "专业投资者/从业者"
  sla: "4h"
quality:
  threshold: 85
  veto_line: "factual < 70"
weights:
  factual: 0.30
  source: 0.25
  depth: 0.20
  readability: 0.15
  timeliness: 0.10
gray_zone_rules:
  - trigger: "涉及A股上市公司"
    action: "double_verify"
```

**输出**：
- `platform/1_ingest/radar/radar_<name>.py`（骨架 + Mock 模板）
- `platform/2_structure/article/article_<name>.py`（骨架）
- `platform/3_render/engines/text/render_<name>.py`（骨架）
- `platform/4_adapt/scorecard/scorecard_<name>.py`（骨架）
- `_run_<name>.py`（验收脚本）
- `content_type_registry.yaml`（增量 patch）

### 11.3 CI/CD 接入规范（v1.4 新增）

**触发条件**：
- push 到 main 分支
- push 到 `feat/*` / `fix/*` / `content/*` 分支
- 手动触发（workflow_dispatch）

**执行内容**：

```yaml
# .github/workflows/llm-acceptance.yml
jobs:
  acceptance:
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: "3.11" }

      - name: Read DeepSeek API Key
        run: echo "DEEPSEEK_API_KEY=${{ secrets.DEEPSEEK_API_KEY }}" >> $GITHUB_ENV

      - name: Run all LLM acceptance tests
        run: python _run_all_llm.py
        # _run_all_llm.py 必须满足：
        #   1. exit code = 0（所有类型 PASS）
        #   2. 每个内容类型的 score ≥ 阈值
        #   3. 每个 markdown 正文长度 ≥ §4.5 最低要求
        #   4. policy_audit.jsonl 记录存在

      - name: Upload results artifact
        uses: actions/upload-artifact@v4
        with:
          name: llm-acceptance-results
          path: |
            platform/5_deliver/results/delivered/**/*.md
            platform/5_deliver/checkpoint/policy_audit.jsonl
            tools/audit_report.md
```

**断言规范**（_run_all_llm.py 必须包含）：

```python
# §11.3 CI/CD 断言 — 每个类型必须验证
assert score >= THRESHOLD, f"Score {score} < {THRESHOLD}"
assert len(markdown) >= MIN_CHARS[type_], f"Markdown {len(markdown)} < {MIN_CHARS}"
assert all_dimensions_above_veto_lines(scorecard), "Dimension below veto line"
assert policy_audit_logged(content_type), "No audit log for {content_type}"
```

### 11.4 Phase B 真实联网采集规范（v1.4 新增）

> **v1.4 状态**：规划定义，接入待实施。目标 v1.5 完成 SPDT-011 接入。

Phase A（当前）：所有数据源 `source_verified = False`（LLM 模式），scorecard 记录 -15/-20 惩罚并写入 gray_zone。

Phase B 目标：将真实联网 API 接入后，`source_verified = True`，移除惩罚。

**接入优先级**：

| 优先级 | 内容类型 | 数据源 | 工具 |
|:---:|:---|:---|:---|
| P0 | `science_research` | arXiv API + Semantic Scholar API | SPDT-011 SemiInfoHub |
| P0 | `deep_industry_report` | Bloomberg / 36Kr / 行业报告 | SPDT-011 SemiInfoHub |
| P1 | `breakdown_news` | 新闻聚合 API（财经/科技垂类）| 待选型 |
| P2 | `science_fact` | Wikipedia / 百度百科（结构化）| 待选型 |

**Phase B 验收标准**：

```
source_verified = True 当且仅当：
  1. API 调用成功返回（非超时 / 非 4xx / 非 5xx）
  2. 返回内容包含非空文本 / 数据数组
  3. 时间戳新鲜度 ≤ SLA（science_research 2h / deep_industry 4h）

失败处理：
  - API 调用失败 → source_verified = False + gray_zone 记录
  - 数据过期 → source_verified = False + gray_zone 记录
  - 不得静默忽略 → 必须写入 policy_audit.jsonl
```

**SPD-SPDT-011 集成约定**：

```
SemiInfoHub → SPDT-005 注入点：
  integration/spdt09_interface/feed_bridge.py（已有）
  ↑ 待新增：
  integration/spdt05_interface/content_feed.py
    输入：情报数据包（MASTER.json schema）
    输出：Radar<type>Request.signals[] 格式
    触发：每日 09:00 CST（mavis cron daily）
```

### 11.5 SOP 版本管理约定

SOP 版本号语义：

| 版本 | 变更类型 | 示例 |
|:---:|:---|:---|
| v1.N.patch | 错别字/格式修正 | 标点修正 |
| v1.N.minor | 新增章节/附录，不破坏已有流程 | §十一新增 |
| v1.N.major | 破坏性变更（模块命名/接口/阈值）| LLM API 切换 |

**SOP 更新触发条件**：
- 新增内容类型完成 → SOP 版本 +1.minor
- render 模块 prompt 改动且影响评分 → SOP 版本 +1.minor
- 阈值/否决线变更 → SOP 版本 +1.minor
- 架构重构（影响已有管线）→ SOP 版本 +1.major

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

## 十二、版本记录

| 日期 | 版本 | 变更内容 | 验证状态 |
|:---|:---|:---|:---|
| 2026-07-31 | v1.0 | 初始版本，整合 P0 science_research + P1 deep_industry_report 实战经验 | ✅ P0 验证通过，P1 验证通过 |
| 2026-07-31 | v1.1 | 对抗性审核修复 + science_research/science_fact 定位决策（保持分离方案A）| ✅ adversarial audit 36→5 findings |
| 2026-07-31 | v1.2 | P3 oped_argument 全 SOP 验证：4 模块实现 + 验收测试 4/4 PASS + Router E2E 通过 | ✅ P3 验收测试通过 |
| 2026-07-31 | v1.4 | **§十一自动化开发框架**：SOP即开发引擎理念；D-0→D-7 SOP驱动开发工作流（新增D-4强制门控说明）；§11.2 sop_develop.py规范定义（规划v1.5实现）；§11.3 CI/CD接入规范（GitHub Actions workflow）；§11.4 Phase B真实联网采集规范（SPD-SPDT-011集成约定）；§11.5 SOP版本管理约定；render_science_fact.py可读性专项prompt（目标≥80，每段≤3句，禁止连续2+技术名词，字数提升至1200-2000）| ✅ SOP已升级，CI/CD待配置 |

---

*本文档基于 SPDT-005 平台 v2.0 管线架构，通过 science_research / deep_industry_report / oped_argument 三个内容类型的实战验证。*
*每新增一个内容类型后，更新 §十清单和 §十一版本记录。*
