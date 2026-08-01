# SPDT-005 科学杂志生成器设计说明书

**版本**: v1.1
**日期**: 2026-08-01
**状态**: 已实现
**负责人**: SPDT-005_MediaContent

---

## 一、产品愿景

将 3 条独立的 AI 内容管线（science_research / deep_industry_report / oped_argument）整合为一个**领域科普杂志自动生成系统**。

用户输入一个领域主题（如"人工智能与科学研究的交叉突破"），系统在数分钟内生成一册包含 5-7 篇结构化文章的完整杂志，支持 DOCX / PDF / HTML 多格式输出。

**差异化价值**：
- 现有管线只生产单篇文章；杂志系统增加**选题规划、产品组装、质量总审**三层
- 5 篇文章围绕同一领域主题展开，形成叙事合力（非简单 Topic 打包）
- 保留每篇文章的独立可追溯性（各自有 scorecard、policy_audit）

---

## 二、杂志产品结构

### 标准结构（7篇文章）

| # | 角色 (article_role) | 内容类型 | 字数要求 | 管线 | 说明 |
|---|---|---|---|---|---|
| 1 | **cover_story** | science_research (deep) | 3000-4000字 | science_research | 封面专题：领域最重大突破，有冲击力 |
| 2 | **explain** | science_research (medium) | 2000-2500字 | science_research | 科学解释：核心概念入门，面向普通读者 |
| 3 | **industry** | deep_industry_report | 3000-5000字 | deep_industry_report | 产业分析：市场格局、技术路线、竞争态势 |
| 4 | **news_brief** | science_research (short) ×N | 每条≤300字 | science_research (快版) | 科技新闻速递：5-8 条近期进展 |
| 5 | **oped** | oped_argument | 1200-1800字 | oped_argument | 观点评论：有立场、有数据、有反驳 |
| 6 | *(可选)* **interview** | science_research | 1500-2000字 | science_research | 人物/对话：虚拟访谈形式（未来扩展） |
| 7 | *(可选)* **data_viz** | deep_industry_report | 1500字 | deep_industry_report | 数据看台：关键图表的文字描述版 |

### 杂志固定结构

```
[封面]
  杂志名 | 卷号/期号 | 主题句 | 日期

[目录]
  各篇文章标题 + 角色标注

[P1] cover_story
  science_research 完整文章

[P2] explain
  science_research 完整文章

[P3] industry
  deep_industry_report 完整文章

[P4] news_brief
  science_research 快版文章（多段落，每段≤300字）

[P5] oped
  oped_argument 完整文章

[封底]
  版权声明 | 编辑手记 | 下期预告
```

---

## 三、系统架构

```
用户输入
  │
  ▼
┌─────────────────────────────────────┐
│  magazine_blueprint.py              │  ← Step 1：选题策划
│  输入：领域主题 + 产品规格           │
│  输出：MagazineBlueprint (文章规划)  │
└──────────────┬──────────────────────┘
               │ Blueprint (5篇规划)
               ▼
┌─────────────────────────────────────┐
│  magazine_orchestrator.py           │  ← Step 2：管线编排
│  并行执行独立管线                    │
│  收集 scorecard + policy_audit      │
│  输出：list[ArticleResult]          │
└──────────────┬──────────────────────┘
               │ list[ArticleResult]
               ▼
┌─────────────────────────────────────┐
│  magazine_assembler.py               │  ← Step 3：产品组装
│  组装封面 + 目录 + 正文 + 封底       │
│  输出：DOCX / PDF / HTML            │
└──────────────┬──────────────────────┘
               │
               ▼
           杂志交付物
    platform/5_deliver/results/magazine/
```

### 关键设计原则

1. **文章独立可追溯**：每篇文章保留完整的 pipeline 结果（brief / outline / article / scorecard）
2. **无状态编排**：orchestrator 不持有管线状态，只负责并行调度
3. **Blueprint 驱动**：杂志结构完全由 Blueprint 定义，可替换、无硬编码
4. **评分门禁**：每篇文章必须通过各自的 scorecard 阈值，才进入组装

---

## 四、模块规格

### 4.1 `magazine_blueprint.py`

**位置**: `platform/2_structure/magazine/magazine_blueprint.py`

**职责**: 根据领域主题 + 产品规格，生成杂志选题规划。

**核心数据结构**:

```python
@dataclass
class MagazineSpec:
    """杂志规格（用户输入）"""
    title: str                  # 杂志名称（如"科学前沿"）
    domain_topic: str           # 领域主题（如"人工智能与科学研究的交叉突破"）
    issue: str                 # 期号（如"2026-Q3"）
    audience: str              # 目标读者（如"理工科研究生"）
    publication_date: str      # 发布日期（ISO）
    articles: list[ArticleSpec]  # 文章规划列表


@dataclass
class ArticleSpec:
    """单篇文章规划（Blueprint 输出）"""
    article_role: str          # 角色（cover_story / explain / industry / news_brief / oped）
    pipeline_type: str         # 管线类型（science_research / deep_industry_report / oped_argument）
    topic: str                 # 文章主题
    constraints: dict          # 约束（depth_level / max_signals / perspective 等）


@dataclass
class MagazineBlueprint:
    """杂志蓝图（Blueprint 输出）"""
    spec: MagazineSpec
    articles: list[ArticleSpec]
    generated_at: str
```

**蓝本是预置模板 + LLM 增强**:
- 内置领域→文章角色映射模板
- LLM 可根据领域主题推荐文章 topic 和优先级
- 支持用户手动覆盖/调整 Blueprint

**使用方式**:
```python
blueprint = MagazineBlueprintLoader().load(
    domain_topic="人工智能与科学研究的交叉突破",
    title="科学前沿",
    issue="2026-Q3"
)
# 或用 LLM 增强
blueprint = MagazineBlueprintGenerator(llm=LLMGateway()).generate(
    domain_topic="人工智能与科学研究的交叉突破",
    article_count=5
)
```

---

### 4.2 `magazine_orchestrator.py`

**位置**: `platform/2_structure/magazine/magazine_orchestrator.py`

**职责**: 接收 Blueprint，编排 3 条管线并行执行，汇总结果。

**核心逻辑**:

```python
class MagazineOrchestrator:
    def __init__(self):
        self._load_pipelines()

    def run(self, blueprint: MagazineBlueprint) -> MagazineRunResult:
        # Step 1: 并行执行所有管线（按 pipeline_type 分组）
        futures = {}
        for spec in blueprint.articles:
            future = self._submit_pipeline(spec)  # 异步提交
            futures[spec.article_role] = future

        # Step 2: 收集结果
        article_results = {}
        for role, future in futures.items():
            result = future.get()  # 等待完成
            # 质量门禁：score < threshold → 标记 revise，不阻止组装但记录
            article_results[role] = result

        # Step 3: 汇总 policy_audit
        policy_audit_entries = [
            r.policy_audit for r in article_results.values()
        ]

        return MagazineRunResult(
            blueprint=blueprint,
            articles=article_results,
            policy_audit=policy_audit_entries,
            all_passed=all(r.passed for r in article_results.values()),
        )
```

**并发策略**: 使用 `concurrent.futures.ThreadPoolExecutor`，根据 pipeline_type 分配线程池。
**容错策略**: 单篇文章失败不影响其他文章，记录 gray_zone 并继续。

---

### 4.3 `magazine_assembler.py`

**位置**: `platform/5_deliver/magazine/magazine_assembler.py`

**职责**: 将文章结果组装为完整杂志文档。

**核心逻辑**:

```python
class MagazineAssembler:
    def assemble(self, run_result: MagazineRunResult,
                fmt: str = "docx") -> MagazineArtifact:
        # 1. 渲染各部分
        cover_md = self._render_cover(run_result.blueprint)
        toc_md = self._render_toc(run_result.articles)
        articles_md = [self._render_article(a) for a in run_result.articles.values()]
        backcover_md = self._render_backcover(run_result)

        # 2. 合并 Markdown
        full_md = "\n\n".join([cover_md, toc_md] + articles_md + [backcover_md])

        # 3. 转换格式
        if fmt == "docx":
            return self._to_docx(full_md, run_result.blueprint)
        elif fmt == "pdf":
            return self._to_pdf(full_md, run_result.blueprint)
        else:
            return self._to_html(full_md, run_result.blueprint)
```

**文件输出**:
```
platform/5_deliver/results/magazine/
  {magazine_title}_{issue}/
    magazine_{issue}.docx
    magazine_{issue}.pdf
    articles/
      01_cover_story.md
      02_explain.md
      03_industry.md
      04_news_brief.md
      05_oped.md
    audit/
      policy_audit.jsonl
      scorecard_summary.json
```

---

## 五、管线升级（新增字段）

现有 3 条管线的 Request dataclass 新增产品级字段，**向后兼容**（默认值确保现有调用不受影响）：

### RadarScienceFactRequest 新增
```python
@dataclass
class RadarScienceFactRequest:
    topic: str
    channels: list[str] = field(default_factory=list)
    max_signals: int = 5
    min_confidence: float = 0.5
    research_type: Optional[str] = None
    # ── 产品级字段（v1.0新增）──
    magazine_name: str = ""        # 杂志名称
    article_role: str = ""          # 角色（cover_story / explain / news_brief）
    target_audience: str = ""     # 目标读者
    editor_intent: str = ""       # 编辑意图
    depth_level: str = "medium"  # short / medium / deep
```

### RadarDeepIndustryRequest 新增
```python
@dataclass
class RadarDeepIndustryRequest:
    topic: str
    industry: str = ""
    scope_years: int = 3
    priority: str = "normal"
    custom_keywords: list[str] = field(default_factory=list)
    max_signals: int = 5
    # ── 产品级字段（v1.0新增）──
    magazine_name: str = ""
    article_role: str = ""          # "industry"
    target_audience: str = ""
    depth_level: str = "deep"      # deep_industry 默认 deep
```

### RadarOpinionRequest 新增
```python
@dataclass
class RadarOpinionRequest:
    topic: str
    perspective: str = "中立"
    industry_focus: str = ""
    custom_keywords: list[str] = field(default_factory=list)
    max_signals: int = 4
    # ── 产品级字段（v1.0新增）──
    magazine_name: str = ""
    article_role: str = "oped"      # 固定为 oped
    target_audience: str = ""
```

---

## 六、评分门禁设计

| 文章角色 | 管线 | 最低阈值 | 说明 |
|---|---|---|---|
| cover_story | science_research | ≥ 80 | 封面专题，质量最高要求 |
| explain | science_research | ≥ 75 | 科学解释，门槛略低 |
| industry | deep_industry_report | ≥ 80 | 产业分析，数据质量要求高 |
| news_brief | science_research | ≥ 70 | 新闻速递，门槛最低 |
| oped | oped_argument | ≥ 80 | 观点评论，调性要求高 |

**门禁动作**:
- `< threshold`：标记 `action = "revise"`，杂志中该文章显示黄色标注
- `< 60`：标记 `action = "reject"`，杂志中该文章替换为占位符

---

## 七、文件结构

```
platform/
  2_structure/
    magazine/
      __init__.py
      magazine_blueprint.py      # 选题策划器
      magazine_blueprint_spec.py # Blueprint 数据结构
      templates/
        default_blueprint.yaml  # 默认领域→文章映射模板

  3_render/
    engines/
      magazine/
        magazine_assembler.py   # 产品组装器

  5_deliver/
    results/
      magazine/
        {magazine_title}_{issue}/
          magazine_{issue}.docx
          magazine_{issue}.pdf
          articles/
          audit/
```

---

## 八、版本规划

| 版本 | 里程碑 | 状态 |
|---|---|---|
| **v1.0** | 基础框架：Blueprint（预置模板）+ Orchestrator + Assembler，跑通 5 文章 Demo | ✅ 已完成 |
| **v1.1** | LLM 增强 Blueprint（自动推荐文章 topic + 编辑手记 + constraints） | ✅ 已完成 |
| **v1.2** | 质量总审层（杂志整体评分，不只是单篇） | 规划中 |
| **v1.3** | 多格式输出（DOCX/PDF/HTML，保留排版） | 规划中 |
| **v2.0** | 杂志系列化（多期、历史版本追踪） | 规划中 |

### v1.1 新增功能

**LLM 增强 BlueprintGenerator**：
- 调用 LLM 分析领域主题，生成精准文章选题
- 每篇文章附带 `angle`（切入角度）、`keywords`、`key_points`
- 生成 `editor_note`（编辑手记），阐述杂志叙事主线
- LLM 增强结果存入 blueprint `_llm_editor_note` 和 `_llm_articles_plan` 扩展字段
- 支持 `use_llm=True/False` 切换模式
- 失败时自动降级到预置模板

---

## 九、实现优先级

1. **P0**（核心回路）: ✅ Blueprint + Orchestrator + Assembler
2. **P1**（智能增强）: ✅ LLM 增强 Blueprint
3. **P2**（质量总审）: 杂志整体评分层
4. **P3**（格式扩展）: DOCX / PDF 输出

---

*本设计说明书随实现进展持续更新。*
