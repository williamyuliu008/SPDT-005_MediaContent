# 2_structure · 结构化加工层
## 协调型架构 — 外部 PDT 生产

---

## 定位

协调型流水线的**结构化加工阶段**。通过 ManuscriptsEngine（SocSciAgent）执行外部 PDT 的生产逻辑。

## 核心职责

| 职责 | 说明 |
|:---|:---|
| **M2 体裁生成** | article_v2 / breaking_news / tech_explainer 体裁模板匹配 |
| **M3 结构化编排** | 多 Agent 协作（Analyst→Architect→Writer→Editor）生成大纲和正文 |
| **质量门禁 L1** | G-SOURCE / G-TIMELINESS 前置检查 |

## 核心组件

### ManuscriptsEngine（SocSciAgent）
```
platform/services/ManuscriptsEngine/
```
- **SOP 阶段**：M2 + M3
- **架构**：多 Agent 协作流水线（clean_agent / fix_chief_editor）
- **输入**：smarttext_router 路由决策 + ContentSpec
- **输出**：article_v2 结构化稿件
- **成员 PDT**：
  - PT-040 DeepProd（深度行业报告）
  - PT-042 SciPop（知识科普）
  - PT-043 OpEd（观点评论）
  - PT-045 TechDoc（技术文档）

### pipeline_runner.py
```
platform/services/ManuscriptsEngine/pipeline_runner.py
```
- ManuscriptsEngine 的主编排脚本
- 管理 agents/ 目录下的子 Agent 协作
- 输出 pipeline_output.json（结构化稿件 + 元数据）

## 协调型说明

> 本层通过 junction 引用外部 PT-047_SocSciAgent 的生产逻辑。
> SPDT-005 不复制 ManuscriptsEngine 代码，仅声明依赖关系。

```
外部 PT-047_SocSciAgent（ManuscriptsEngine 主仓库）
    │
    ├── agents/（clean_agent / fix_chief_editor / 领域 Agent）
    ├── pipeline_runner.py（主编排器）
    └── templates/（体裁模板）
           ↑
      junction 引用（不复制代码）
           │
    2_structure/ManuscriptsEngine/（SPDT-005 逻辑命名空间）
```

## 五阶段映射

| 阶段 | 对应 SOP | 本层实现 |
|:---|:---|:---|
| 2_structure | M2+M3 | ManuscriptsEngine（SocSciAgent） |

## 与 SPDT-004 2_structure 的关系

| 维度 | SPDT-004（教育） | SPDT-005（媒体） |
|:---|:---|:---|
| 结构化内容 | scene_v2（沉浸式剧本） | article_v2（结构化文章） |
| 体裁模板 | 墨骨山河/古史知识链 | deep_industry_report / breaking_news / tech_explainer |
| 核心引擎 | TextExperience（自含生产） | ManuscriptsEngine（外部 PDT 协调） |
| 产出形态 | 剧本杀/知识链 | 深度报告/快讯/科普文/评论 |
