# PT-047 × OMAS SDC 适配方案

> 版本：V1.0
> 日期：2026-07-14
> 状态：设计阶段
> 范围：指导 PT-047 如何接入 OMAS SDC + CMC 引擎，实现社科类通俗作品创作智能体平台的自动化开发

---

## 一、为什么需要适配

PT-047 的开发模式与 SDC 的标准假设之间存在**结构性差异**。SDC 的核心价值主张是"胶水代码 ≥70%，新业务代码 ≤300 行"，面向的是**已有可复用模块的整合交付**。PT-047 是**全新的多智能体平台**，包含大量定制业务逻辑（规则引擎、COG 脚本生成器、编排算法），两者存在三个核心冲突：

| 维度 | SDC 默认假设 | PT-047 现实 |
|:---|:---|:---|
| **代码结构** | 整合已有模块为主 | 从零构建 10+ 智能体的完整平台 |
| **胶水比例** | ≥70% 胶水代码 | 规则引擎/编排逻辑等新业务代码预计占 40-50% |
| **交付物** | 单模块/单文件 | 多智能体 + 知识库 + 模板库 + 可视化工具 |
| **任务类型** | 软件开发（code_gen/integration） | **多智能体平台开发**（新类别，无现成配方） |

因此，不能简单调用 `run_standard("社科类通俗作品创作平台")`，需要先对 SDC 做**扩展适配**，再用于 PT-07 的构建。

---

## 二、适配架构总览

```
┌─────────────────────────────────────────────────────┐
│              OMAS 根目录 (D:\6_agent_project\omas)     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  SDC 扩展层 (PT-047 适配)                    │   │
│  │                                              │   │
│  │  1. resource_router.py                      │   │
│  │     新增: "多智能体平台开发" 任务分解规则      │   │
│  │                                              │   │
│  │  2. SCOPE_RULES 扩展                         │   │
│  │     新增: "multi_agent_platform" scope        │   │
│  │     允许: 新业务代码 ≤ 2000 LOC               │   │
│  │           胶水比例 ≥ 40% (从70%降级)         │   │
│  │                                              │   │
│  │  3. MATCH_TABLE 扩展                         │   │
│  │     新增: multi_agent_platform 资源匹配项     │   │
│  │     引入: MODLIB/agent.py (Agent框架)        │   │
│  │           CMC content_engine (内容生成)        │   │
│  │                                              │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  CMC 内容引擎 (PT-047 直接复用)              │   │
│  │                                              │   │
│  │  · textfactory → 模板填充引擎               │   │
│  │  · COG 脚本模板 → 可作为内容生成配方引用    │   │
│  │  · style_templates → 文风包管理接口         │   │
│  │                                              │   │
│  │  ⚠️ 当前 CMC 仅支持:                        │   │
│  │     教科书/试卷/报告 (5种)，PT-047 的       │   │
│  │     "历史通俗作品" 属于新类型，              │   │
│  │     需扩展 CMC 支持或作为 PT-047 内置生成    │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  MODLIB 模块库 (PT-047 复用)                │   │
│  │                                              │   │
│  │  · infra_module_lib/agent.py                │   │
│  │    → 作为 AG-047-01 Chief Editor 的基础框架  │   │
│  │                                              │   │
│  │  · infra_module_lib/memory/chromadb         │   │
│  │    → 作为知识库底层 (AG-047-11 KnowledgeBase)│   │
│  │                                              │   │
│  │  · infra_module_lib/retrieval               │   │
│  │    → 作为材料检索底层 (AG-047-03 Scout)     │   │
│  │                                              │   │
│  │  · infra_module_lib/processing_rule_engine   │   │
│  │    → PT-047 规则引擎可基于此扩展             │   │
│  │                                              │   │
│  │  · infra_module_lib/networking (FastAPI)    │   │
│  │    → Web UI 服务层                          │   │
│  │                                              │   │
│  │  · infra_module_lib/hmi (Streamlit/Gradio)  │   │
│  │    → COG Visualizer 可直接复用              │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
└─────────────────────────────────────────────────────┘
                          │
                          ▼ (PT-047 项目目录)
┌─────────────────────────────────────────────────────┐
│  D:\92_products\SPDT-005_MediaContent\             │
│  PT-047_SocSciAgent/                                │
│                                                      │
│  agents/          ← 10个 Agent AGENT.yaml (骨架)   │
│  templates/       ← 模板注册表 (TPL-01 等)         │
│  kb/               ← 知识库节点 (晚明历史)          │
│  style_packs/     ← 文风包                          │
│  reader_personas/ ← 读者画像                        │
│  historio_packs/  ← 史观包                          │
│  tests/           ← 单元测试                        │
│  docs/            ← 设计文档 + SDC适配方案 (本文件) │
│                                                      │
│  [开发阶段逐步填充 agents/ 下的实现文件]             │
└─────────────────────────────────────────────────────┘
```

---

## 三、SDC 核心文件扩展方案

### 3.1 resource_router.py — 新增任务类型

在 `TASK_DECOMPOSERS` 列表末尾新增一条规则：

```python
# 多智能体平台开发 → 需要架构+通信+编排+内容生成
{
    "pattern": r"(多智能体平台|Agent平台|Multi-Agent平台|agent.*platform|multi.*agent.*system|多Agent集群平台)",
    "subtasks": [
        {"name": "多Agent平台架构设计",  "category": "multi_agent_platform", "priority_base": 7},
        {"name": "Agent间通信与协调",   "category": "agent_networking",   "priority_base": 18},
        {"name": "编排引擎实现",         "category": "orchestration_engine","priority_base": 8},
        {"name": "内容生成配方设计",    "category": "content_recipe",      "priority_base": 13},
        {"name": "规则引擎配置",         "category": "rule_engine",         "priority_base": 11},
    ],
},
```

**优先级说明**：`priority_base=7`（很高）是因为多智能体平台是复杂任务，需优先完成架构设计。

### 3.2 MATCH_TABLE — 新增资源匹配

在 `MATCH_TABLE` 字典中新增：

```python
"multi_agent_platform": {
    "primary": [
        {"name": "module_lib.agent",                        "weight": 0.90, "reason": "Agent框架(82KB)"},
        {"name": "module_lib.pipeline_orchestrator",        "weight": 0.85, "reason": "编排器"},
        {"name": "module_lib.processing_rule_engine",      "weight": 0.80, "reason": "规则引擎"},
    ],
    "secondary": [
        {"name": "module_lib.processing_computation_graph", "weight": 0.75, "reason": "计算图/COG"},
        {"name": "module_lib.hmi",                          "weight": 0.70, "reason": "可视化调试"},
        {"name": "DESIGN.arch_analysis",                   "weight": 0.65, "reason": "架构路由"},
    ],
},
"orchestration_engine": {
    "primary": [
        {"name": "module_lib.pipeforge",                    "weight": 0.90, "reason": "管道编排引擎"},
        {"name": "module_lib.processing_computation_graph", "weight": 0.85, "reason": "COG脚本生成"},
    ],
    "secondary": [
        {"name": "module_lib.processing_rule_engine",      "weight": 0.70, "reason": "规则引擎"},
        {"name": "DESIGN.arch_analysis",                   "weight": 0.65, "reason": "架构分析"},
    ],
},
"content_recipe": {
    "primary": [
        {"name": "CMC.content_engine",                       "weight": 0.85, "reason": "内容引擎"},
        {"name": "module_lib.processing_conditional_router", "weight": 0.70, "reason": "条件路由"},
    ],
    "secondary": [
        {"name": "shared/tools/llm_clients.py",              "weight": 0.60, "reason": "LLM调用"},
    ],
},
"agent_networking": {
    "primary": [
        {"name": "module_lib.networking",                    "weight": 0.85, "reason": "网络/FastAPI"},
    ],
    "secondary": [
        {"name": "module_lib.protocol",                      "weight": 0.70, "reason": "协议设计"},
    ],
},
"rule_engine": {
    "primary": [
        {"name": "module_lib.processing_rule_engine",       "weight": 0.90, "reason": "规则引擎核心"},
    ],
    "secondary": [
        {"name": "module_lib.storage",                       "weight": 0.60, "reason": "规则持久化"},
    ],
},
```

### 3.3 DEPENDENCIES — 新增依赖关系

```python
DEPENDENCIES = {
    # ... 原有依赖 ...
    "agent_networking":    ["multi_agent_platform"],
    "orchestration_engine":["multi_agent_platform"],
    "rule_engine":         ["multi_agent_platform"],
    "content_recipe":      ["multi_agent_platform"],
}
```

### 3.5 UIUX_design SOP 引用规范

PT-047 的最终 UI 层（诊断报告可视化、Web 控制台）需遵循 UIUX_design SOP v2.0：

```
D:\9_infra\UIUX_design\_SOP\v2.0/
    ├── README.md                    # DAGO 四层编译器总览
    ├── src/
    │   ├── dago_compiler_v20.py     # 8 Stage 流水线
    │   ├── visualizer_v20.py        # Stage 8: 统一可视化
    │   └── visual_parameter_compiler.py  # Stage 7B: 视觉参数编译
    └── rules/
        ├── G/visual_parameter_space.yaml  # 5维视觉参数
        ├── A/primitive_activation.yaml     # 推导链
        └── D/                          # 领域覆写

PT-047 GUI 层（未来）调用流程:
  dims (COG JSON) → dago_compiler_v20 → ux_definition → visualizer_v20 → HTML/Streamlit
```

**关键引用**：
- `dims.json` → PT-047 的 COG 配置直接映射为 UIUX 的 5 维参数（density→信息密度, severity→风险色）
- `visualizer_v20.py` → 最终 Web 可视化的渲染引擎
- `layout_templates.yaml` → L1 沉浸阅读 / L4 简单列表 → PT-047 章节展示布局

---

### 3.6 EXISTING_PRODUCTS — 复用已有产品检查

```python
EXISTING_PRODUCTS = {
    # ... 原有映射 ...
    "多智能体平台|Agent平台|多Agent": {
        "product": "AgentClusterOS",
        "note": "Agent集群OS架构可参考，但需为PT-047定制内容编排逻辑"
    },
}
```

---

## 四、SCOPE RULES — 新增多智能体平台 Scope

在 `run_standard.py` 的 `SCOPE_RULES` 字典中新增：

```python
SCOPE_RULES = {
    # ... 原有 scope ...
    "multi_agent_platform": {
        "max_total_loc": 5000,
        "max_glue_loc": 2000,
        "max_agents": 5,         # SDC 并行 worker 上限
        "max_days": 30,
        "max_new_business_loc": 2000,  # 新增: 业务代码上限（PT-047 核心诉求）
        "min_glue_ratio": 0.40,        # 新增: 胶水比例下限（从70%降级）
        "require": "需人工审核架构设计 + COG 脚本正确性",
        "note": "PT-047 多智能体平台：规则引擎/COG生成器等新业务代码不可避免"
    },
    "cli_diagnostic": {
        "max_total_loc": 500,
        "max_glue_loc": 400,
        "max_days": 3,
        "require": "输出可机器解析的 JSON/YAML 结构化日志",
        "note": "CLI 诊断工具: 纯结构化输出，不依赖 UI，agent 和人类均可消费"
    },
}
```

**降级说明**：
- `min_glue_ratio: 0.40`（标准 0.70 → 降至 0.40）：PT-047 的规则引擎（评分函数、COG 脚本生成器、张力曲线算法）是纯新业务逻辑，无法通过胶水实现
- `max_new_business_loc: 2000`：设定硬上限，超出则要求进一步拆分任务
- `max_days: 30`：多智能体平台复杂，给予更宽松的时间

---

## 五、SDC 运行模式选择

### 5.1 PT-047 不适用标准 code_gen/integration

| SDC 标准模式 | 问题 |
|:---|:---|
| `assessment` | 仅评估，PT-047 需要实际构建 |
| `integration` | 要求胶水 ≥70%，PT-047 业务代码约 40-50%，不满足 |
| `code_gen` | 仅 CMM=L1 且组织资源 <4 项时使用，PT-047 需多轮构建 |

### 5.2 新增 PT-047 专属模式：`multi_agent_platform`

```python
# 在 step_decide() 中新增分支
elif mode == "multi_agent_platform":
    # 核心逻辑: 分阶段构建，每阶段产出具体工件
    # Phase 1: 首席编排器 + 编排引擎 + COG可视化工具
    # Phase 2: 材料Scout + 知识库检索
    # Phase 3: 生成器 + 评审 + 反思
    # Phase 4: 输出渲染器 + 文风/史观管理 + 合规扫描
    
    # 每个 Agent 独立交付，累积到 PT-047 agents/ 目录
    # run_summary 记录每个 Agent 的交付状态
```

**PT-047 专属模式逻辑**：

```python
def step_execute_pt047(run_dir, task_name, decision, resources):
    """PT-047 多智能体平台构建执行器"""
    
    # 1. 分析设计文档，确定要构建的 Agent
    design_doc = os.path.join(
        "D:/92_products/SPDT-005_MediaContent/PT-047_SocSciAgent",
        "docs", "平台设计需求.md"
    )
    
    # 2. 读取 Agent 列表（从平台设计文档中提取）
    # 3. 对每个 Agent 执行: AGENT.yaml → 实现骨架填充 → 集成测试
    # 4. 每完成一个 Agent，更新 PT-047/agents/{name}/AGENT.yaml status
    
    # Phase 1 交付物: 
    #   - AG-047-01 ChiefEditor (骨架 + 核心协调逻辑)
    #   - AG-047-04 Orchestration (三层漏斗 + COG输出)
    #   - AG-047-12 COG Visualizer (独立调试工具)
    
    return {
        "mode": "multi_agent_platform",
        "agents_delivered": ["chief_editor", "orchestration", "cog_visualizer"],
        "phase": 1,
        "capability_change": "PT-047 Phase 1 完成",
    }
```

---

## 六、CMC 引擎的定位与局限

### 6.1 CMC 当前能力

```
CMC content_engine 支持的内容类型:
  1. 教科书 (textbook)
  2. 试卷 (exam_paper)
  3. 报告 (report)
  4. 知识问答 (qa)
  5. 摘要生成 (summary)

PT-047 需求:
  → 历史通俗作品 (popular_history) ← 新类型，CMC 暂不支持
```

### 6.2 PT-047 对 CMC 的利用策略

| CMC 组件 | PT-047 如何复用 | 局限性 |
|:---|:---|:---|
| `textfactory` 模板引擎 | 作为 AG-047-07 生成器的槽填充参考实现 | 需为通俗作品扩展 |
| `slot_filling` 机制 | 直接复用 PT-047 的 ControlledGeneration | 需适配 COG 格式 |
| `style_templates` | 文风包管理可参考 CMC 的 style template 接口 | 需自定义 |
| `llm_client` | `shared/tools/llm_clients.py` 直接复用 | 无 |

**结论**：CMC 的 `slot_filling` 机制是 PT-047 ControlledGeneration 的最佳参考，建议在 AG-047-07 中直接引用 `CMC.content_engine` 作为生成引擎的外层封装。

---

## 七、MODLIB 复用清单

| MODLIB 模块 | 复用方式 | PT-047 落地位置 |
|:---|:---|:---|
| `infra_module_lib/agent.py` | Agent 基础框架（82KB，含多轮对话、工具调用、记忆管理） | 所有 10 个 Agent 的基类 |
| `infra_module_lib/memory/chromadb` | 向量知识库底层 | AG-047-11 KnowledgeBaseAgent |
| `infra_module_lib/retrieval` | 语义检索模块 | AG-047-03 MaterialScout |
| `infra_module_lib/processing_rule_engine` | 规则引擎（评分、过滤、约束） | AG-047-04 Orchestration（规则层）|
| `infra_module_lib/processing_computation_graph` | 计算图（COG 生成器可基于此扩展） | AG-047-04 Orchestration（COG 脚本生成）|
| `infra_module_lib/processing_conditional_router` | 条件路由 | AG-047-01 ChiefEditor（路由决策）|
| `infra_module_lib/networking`（FastAPI）| Web 服务/API 接口 | AG-047-12 COG Visualizer |
| `infra_module_lib/hmi`（Streamlit/Gradio）| 可视化 UI | AG-047-12 COG Visualizer |
| `shared/tools/llm_clients.py` | LLM 调用（DeepSeek/Qwen） | AG-047-07 ControlledGeneration |

---

## 八、PT-047 × SDC 集成架构

### 8.1 整体集成关系

```
┌──────────────────────────────────────────────────────────────┐
│  OMAS SDC (开发引擎)                                         │
│                                                              │
│  SDC.run_standard() → 四层决策链                             │
│    ├── 上下文加载（宪章/指令/能力清单）                        │
│    ├── 资源扫描（组织+系统库）                               │
│    ├── 决策（mode=multi_agent_platform）                     │
│    └── 执行（step_execute_pt047）                           │
│                                                              │
│  SDC 产出 → PT-047 项目目录的代码文件                         │
│    D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent   │
└────────────────────────────┬─────────────────────────────────┘
                             │ 交付物写入
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  PT-047 社科类通俗作品创作平台                                │
│                                                              │
│  Phase 1 (当前):                                             │
│    agents/chief_editor/        ← SDC 生成                   │
│      AGENT.yaml (已有)                                         │
│      chief_editor.py (待生成)                                  │
│    agents/orchestration/        ← SDC 生成                   │
│      AGENT.yaml (已有)                                         │
│      orchestration.py (待生成)                                │
│      cog_visualizer.py (待生成, 调试工具)                     │
│    agents/material_scout/      ← SDC 生成                   │
│      AGENT.yaml (已有)                                         │
│      material_scout.py (待生成)                               │
│                                                              │
│  Phase 2-4: generation, review, reflection, output 等          │
│                                                              │
│  PT-047 运行时的调用链:                                      │
│    ChiefEditor → Orchestration → MaterialScout               │
│                → ControlledGeneration → Review              │
│                → Reflection (if fail) → Output              │
└──────────────────────────────────────────────────────────────┘
```

### 8.2 SDC 扩展文件放置位置

```
D:\6_agent_project\omas\src\SDC\
  kernel/
    resource_router.py          ← 修改: 新增 multi_agent_platform 规则
  governance/
    scope_rules_ext.yaml       ← 新增: PT-047 专属 scope 定义
  PT-047/
    run_pt047.py               ← 新增: PT-047 专属执行器
    diagnostics/
      cog_cli.py              ← Phase 0 交付 (CLI 诊断系统)
      cog_gui.py              ← Phase 4 交付 (GUI, 最后)
    agents/
      chief_editor.py
      orchestration.py
      material_scout.py
      ...
```

**注意**：修改 `resource_router.py` 是对 OMAS SDC 源文件的直接改动，属于 PT-047 的适配成本。改动后 SDC 对所有任务生效（多智能体平台开发赛道的通用提升）。

---

## 九、分阶段开发计划（基于 SDC 的 PT-047 构建）

### 9.1 开发优先级原则

> **CLI 优先，GUI 最后。**
> "可视化"不是指 GUI 界面，而是指**结构化诊断输出**（JSON/YAML）。CLI 诊断系统输出机器可读的结构化日志，agent 在运行时直接消费，人类通过终端查看——无需人工操作界面，不降低自动化开发效率。GUI 层是功能稳定后的锦上添花，放在最后。

### 9.2 开发阶段映射

```
┌──────────────────────────────────────────────────────────────────────┐
│  SDC 轮次  │  PT-047 阶段        │  交付物                          │
├────────────┼──────────────────────┼──────────────────────────────────┤
│  Run #1    │  Phase 0             │  COG CLI 诊断系统                 │
│            │  (诊断工具先行)        │  • 三层漏斗推理 → JSON 结构日志    │
│            │                      │  • agent/人类均可消费               │
│            │                      │  • 复用 module_lib.hmi (非 GUI)    │
├────────────┼──────────────────────┼──────────────────────────────────┤
│  Run #2    │  Phase 1.1           │  ChiefEditor Agent               │
│            │  (核心编排器)          │  • 全局上下文管理                  │
│            │                      │  • 任务分发路由                    │
│            │                      │  • 状态机驱动                      │
├────────────┼──────────────────────┼──────────────────────────────────┤
│  Run #3    │  Phase 1.2           │  Orchestration Agent             │
│            │  (编排引擎)            │  • 三层漏斗选择                   │
│            │                      │  • COG 脚本生成                    │
│            │                      │  • 张力曲线编排                    │
├────────────┼──────────────────────┼──────────────────────────────────┤
│  Run #4    │  Phase 1.3           │  MaterialScout Agent             │
│            │  (材料检索)            │  • 意图解析 → 检索                │
│            │                      │  • 节点评分 + 挖掘模式              │
├────────────┼──────────────────────┼──────────────────────────────────┤
│  Run #5-7  │  Phase 2             │  ControlledGeneration            │
│            │  (受控生成)            │  + Review + Reflection            │
├────────────┼──────────────────────┼──────────────────────────────────┤
│  Run #8-10 │  Phase 3             │  Output + Style +                │
│            │  (辅助功能)            │  Historio + Compliance           │
├────────────┼──────────────────────┼──────────────────────────────────┤
│  Run #11   │  Phase 4             │  COG GUI 可视化 (最后，按需)      │
│            │  (UI 层)              │  • 复用 UIUX_design SOP v2.0      │
│            │                      │  • 复用 module_lib.hmi (Streamlit) │
│            │                      │  • 复用 dago_compiler_v20.py       │
└────────────┴──────────────────────┴──────────────────────────────────┘
```

### 9.3 Run #1 prompt 示例（CLI 诊断系统）

```
task_name = "PT-047 Phase 0: 构建 COG CLI 诊断系统"
description = """
多智能体社科作品创作平台 PT-047 的命令行诊断工具。
核心功能: 
1. 接收 COG JSON 配置，输出三层漏斗决策过程的详细结构化日志
2. 输出格式: JSON Lines (.jsonl)，每个决策节点含: layer/score/candidates/reason
3. 不需要任何图形界面，纯文本终端输出
4. agent 可直接读取日志做决策，人类可在终端查看
输入: COG JSON 配置文件路径
输出: 诊断报告 (stdout + 可选 .jsonl 文件)
复用: module_lib.hmi (仅用其日志格式化工具, 不引入 UI)
范围: CLI, scope=cli_diagnostic, ≤500 LOC
"""
```

### 9.4 PT-047 的 CMM 追踪

| 维度 | 初始等级 | 目标 | 达成条件 |
|:---|:---|:---|:---|
| 多智能体平台开发赛道 | L1 | L2 | Phase 1-4 完整交付 ≥1 个 Agent |
| 规则引擎赛道的胶水比率 | L1 | L2 | reuse_score ≥60（复用 MODLIB 模块 ≥3）|

---

## 十、关键适配决策与风险

### 10.1 适配决策清单

| 决策ID | 问题 | 决策 | 理由 |
|:---|:---|:---|:---|
| DEC-PT047-01 | SDC 标准胶水比 70% 是否必须遵守？ | 否，降级至 40% | PT-047 的规则引擎/COG 生成器属于新业务逻辑，无法纯胶水实现 |
| DEC-PT047-02 | CMC 内容引擎是否直接用于 PT-047？ | 部分复用 | CMC slot_filling 机制参考；"通俗作品"类型需新扩展 |
| DEC-PT047-03 | SDC resource_router.py 改动是否回退？ | 否，持续维护 | 多智能体平台是 SDC 的新赛道，PT-047 改动的通用价值 |
| DEC-PT047-04 | 每轮 SDC 交付的粒度？ | 1 个 Agent + 1 个功能 | 多智能体平台复杂，单轮不应超过 1 个 Agent |
| DEC-PT047-05 | COG Visualizer 的形式？ | **CLI 先行**，GUI 最后 | GUI 需要人工操作，降低自动化效率；CLI 输出 JSON 结构化日志，agent 可直接消费 |
| DEC-PT047-06 | GUI 层参考什么标准？ | UIUX_design SOP v2.0 | DAGO 四层编译器 + 5维视觉参数 + dago_compiler_v20.py |

### 10.2 风险与缓解

| 风险 | 等级 | 缓解措施 |
|:---|:---|:---|
| SDC 胶水比例降级导致代码质量不可控 | 高 | 每个 Agent 交付后人工代码审查，聚焦规则引擎和 COG 生成器 |
| CMC 不支持"通俗作品"内容类型 | 中 | PT-047 内置生成器，不依赖 CMC 扩展；CMC slot_filling 机制作为参考 |
| 10 个 Agent 的集成测试复杂度高 | 高 | Phase 0 的 CLI 诊断系统作为统一调试入口；每轮交付包含单元测试；GUI 放在最后作为辅助层 |
| SDC 改动影响其他赛道 | 低 | 仅在 TASK_DECOMPOSERS 中新增，不修改已有规则 |
| 知识库初始化（晚明历史）数据不足 | 中 | Phase 1 构建知识节点填充流程，而非一次性填满 |

---

## 十一、行动清单（下一步）

```
□ 第一步: 修改 SDC resource_router.py
    新增 "多智能体平台开发" 任务分解规则 (TASK_DECOMPOSERS)
    新增 MATCH_TABLE 条目 (5个新 category)
    更新 DEPENDENCIES
    
□ 第二步: 修改 SDC run_standard.py
    新增 SCOPE_RULES["multi_agent_platform"]
    新增 SCOPE_RULES["cli_diagnostic"]
    新增 step_execute_pt047() 执行器
    在 step_decide() 中增加分支判断
    
□ 第三步: 创建 PT-047 专属运行脚本
    D:\6_agent_project\omas\src\SDC\PT-047\run_pt047.py
    封装: 读取平台设计文档 → 解析 Agent 列表 → 批量调用 SDC
    
□ 第四步: 执行 SDC Run #1 — 构建 COG CLI 诊断系统
    输出: PT-047/diagnostics/cog_cli.py
    产出: 三层漏斗推理 JSON 结构化日志 (agent/人类均可消费)
    
□ 第五步: 执行 SDC Run #2 — 构建 ChiefEditor Agent
    复用: module_lib.agent.py, module_lib.processing_conditional_router
    产出: PT-047/agents/chief_editor/chief_editor.py
    
□ （Phase 4 完成后）构建 GUI 层时
    参考: D:\9_infra\UIUX_design\_SOP\v2.0/
    复用: dago_compiler_v20.py, visualizer_v20.py, visual_parameter_space.yaml
    产出: PT-047/diagnostics/cog_gui.py (Streamlit/Gradio)
```

---

## 附录：SDC 与 PT-047 术语对照

| SDC 术语 | PT-047 对应 |
|:---|:---|
| Task / 任务 | 单个 Agent 的实现 |
| Subtask / 子任务 | Agent 的功能模块（如 COG 生成、张力曲线） |
| Integration / 整合交付 | 将 Agent 接入 PT-047 流水线 |
| Resource / 资源 | MODLIB 模块、CMC 组件 |
| MATCH_TABLE | Agent 类型 → 所需 MODLIB 模块的映射 |
| CMM / 能力成熟度 | PT-047 各 Agent 的完成度等级 |
| Glue Code / 胶水代码 | 适配接口、串联调用的代码（规则引擎除外） |
| Business Logic / 业务代码 | 规则引擎、COG 生成器、张力曲线算法 |
| Delivery Catalog | PT-047 Agent 交付记录 |
| Scope Gate | PT-047 每轮交付的质量门槛 |

---

*本文档是 PT-047 与 OMAS SDC 集成的核心参考。*
*SDC 改动（resource_router.py / run_standard.py）完成后，请同步更新 OMAS pdt_registry/PT-047/pdt.yaml 中的 "dev_engine" 字段为 "SDC-extended"。*
