# MKT内阁 — 配合事项与疑问答复

**发件方：** MKT内阁  
**收件方：** 交付内阁  
**关联文档：** 交付内阁评估回执（2026-06-17）  
**日期：** 2026-06-17  
**类型：** 配合交付 + 疑问澄清

---

## 一、阻塞项 1：CI Engine 简报数据格式

### 1.1 数据源路径

```
C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events\2026-06\{MMDD}_extracted.json
```

### 1.2 10 家公司清单（按 CI Engine profiles 目录确认）

| 序号 | 公司 | profile 文件 | 领域标签 |
|:----:|------|-------------|----------|
| 1 | OpenAI | openai.json | 大模型/基础研究 |
| 2 | Google DeepMind | google.json | 大模型/搜索/云 |
| 3 | Microsoft | microsoft.json | 云/AI平台/办公 |
| 4 | Anthropic | anthropic.json | 大模型/安全 |
| 5 | NVIDIA | nvidia.json | AI芯片/硬件 |
| 6 | 字节跳动 | bytedance.json | 大模型/应用/推荐 |
| 7 | 百度 | baidu.json | 大模型/自动驾驶 |
| 8 | 阿里巴巴 | alibaba.json | 云/大模型/开源 |
| 9 | 腾讯 | tencent.json | 大模型/社交/游戏 |
| 10 | Perplexity | perplexity.json | AI搜索/Agent |

### 1.3 JSON Schema（从 2026-06-17 实际产出的第一条提取）

```json
{
  "event_id": "evt_YYYYMMDD_NNN",          // string，唯一事件ID
  "event_type": "product_launch",          // enum: product_launch | funding | price_change | partnership | strategy | regulation | talent_move
  "company": "anthropic",                  // string，公司短名（小写）
  "title": "Anthropic发布Claude Fable 5",  // string，事件标题
  "date": "2026-06-09",                    // string，ISO date
  "summary": "详细描述文本...",             // string，200-500字摘要
  "metrics": {                             // object，可选，指标键值对
    "context_window": 1000000,
    "max_output_tokens": 128000
  },
  "source_url": "https://...",             // string，来源URL
  "source_level": "primary",               // enum: primary | secondary
  "confidence": 0.95,                      // float，置信度 0-1
  "importance_score": 0.92,               // float，重要性评分 0-1
  "delta": {                               // object，变化描述
    "description": "首次向公众开放Mythos级模型",
    "direction": "positive"                // enum: positive | negative | neutral
  },
  "affected_dimensions": ["tech", "business", "finance"],  // array
  "tags": ["mythos", "model_release", "frontier"]           // array
}
```

### 1.4 数据量参考

| 日期 | 事件数 | 文件大小 |
|------|:------:|----------|
| 6/17 | 18 条 | 19.5 KB |
| 6/15 | 15 条 | 16.9 KB |
| 6/11 | 13 条 | 15.8 KB |
| 6/10 | 11 条 | 12.8 KB |

每日约 **12-18 条事件**，覆盖全部 10 家公司。

### 1.5 建议用法

SR-CH-001 的 `build.py` 读取最新 `_extracted.json` → 按 `importance_score` 降序取 Top 5 → 按 `company` 分组 → 交给 STP B/F 赛道生成日报。`importance_score ≥ 0.80` 的事件进入"今日重大信号"，其余进入"其他值得关注"。

---

## 二、阻塞项 2：ModLib 每日扫描格式

### 2.1 数据源路径

```
D:\9_infra\module_lib\docs\daily_reports\external_scan_YYYY-MM-DD.md
```

### 2.2 报告结构（Markdown）

```markdown
# 外部扫描日报
> 日期 / 生成时间 / 综合评级（A/B/C + 得分/100）

## 本期摘要
| 维度 | 状态 | 趋势 |
综合健康度 / GitHub管道 / 缓存候选 / Skill资产 / 社区源发现

## 一、GitHub OSS 扫描
| 指标 | 值 |
扫描器状态 / Token配置 / 实时扫描 / 缓存候选数 / 扫描Profile列表

Profile 列表: AI Agent, 量化交易, 学习教育, 知识库与RAG, ...

## 二、Skill 资产扫描
| 指标 | 值 |
技能总数 / 领域数 / S级数 / A级数 / 新模块来源

领域分布表

## 三、微信/社区源扫描
| 指标 | 值 |
扫描器状态 / 发现文章数 / 新入库数

## 四、本期行动建议
一条或多条建议

## 五、内阁推荐
按内阁领域分组的外源项目推荐表
```

### 2.3 建议用法

SR-CH-003 的 `build.py` 读取最新 `external_scan_*.md` → 提取 GitHub 扫描结果 + Skill 资产变化 + 内阁推荐 → 交给 STP A/D 赛道生成日报。"新发现的 repo"进入"昨日新发现"，"内阁推荐"进入"重点项目深读"。

---

## 三、其余配合事项

### 3. AI 智囊团扫描格式

**路径：** `D:\7_MKT\_05_ops\daily_signals\` — 当前目录尚未产出文件（智囊团扫描直接输出到 CI Engine briefs）。  
**建议：** SR-CH-001 和 SR-CH-005 直接使用 CI Engine 简报（`ci-engine/reports/briefs/*.md`）和提取后的 JSON 作为信号输入。智囊团的扫描结果已融入 CI Engine 每日简报的"战略判断"章节。

### 4. Survey design_precedent 模板

**路径：** `D:\9_infra\survey\templates\design_precedent.yaml` — 已存在。  
**说明：** 该模板定义了设计调研的参数（目标产品、分析维度、输出格式），SR-CH-004 直接调用即可。Survey 的 `template_engine.py` 负责模板渲染。

### 5. 网站样式偏好

- **主题：** 深色科技风（同意交付内阁建议）
- **品牌色：** 无特定品牌色要求，使用科技行业常见的深蓝/青色系即可
- **Logo：** 暂不需要，使用文字标识「AI 瞭望台」
- **响应式：** 桌面优先，移动端仅需内容可读

### 6. 网站托管确认

**路径：** `D:\92_products\SmartTextPlatform\canvas\ai-lookout\`  
**权限：** MKT 内阁已有该目录读写权限。交付内阁直接使用。

---

## 四、七项疑问答复

| # | 疑问 | 答复 |
|:--:|------|------|
| **Q1** | 10 家公司清单 | ✅ 已确认（见本文第一节）。建议使用 profile 目录中的 10 家：OpenAI / Google / Microsoft / Anthropic / NVIDIA / 字节跳动 / 百度 / 阿里巴巴 / 腾讯 / Perplexity。后续如需增删由 MKT 内阁维护 `ci-engine/profiles/` 目录 |
| **Q2** | Stage 差异度计算方式 | 使用 Python `difflib.SequenceMatcher.ratio()` 计算相邻 Stage 输出文本相似度（0=完全不同，1=完全相同）。测试脚本 `tests/continuous/regression_test.py` 已实现，交付内阁可直接复用 |
| **Q3** | App Store 降级方案 | 接受降级。如果公开榜单抓取失效（连续 3 天无数据），自动降级为 Survey web_search 模式（搜索关键词 "best AI apps 2026" + "AI app design trends"），在报告中标注 [降级模式]。PoC 验证建议用 Product Hunt 的 AI 分类页作为首选数据源（DOM 相对稳定） |
| **Q4** | 月报影响力评分 | 由 AI 自动评分，人工不复核。评分规则：`importance_score ≥ 0.90` → 影响力 8-10，`0.80-0.89` → 5-7，`< 0.80` → 1-4。直接复用 CI Engine JSON 中的 `importance_score` 字段 |
| **Q5** | 知识底座查询接口形态 | Phase 1 用 Python 函数调用（`kb.query("OpenAI 过去三个月的变化")` → 返回 Markdown）。Phase 3 在 AI 瞭望台网站上增加知识搜索页面。不做 CLI，不做独立 API |
| **Q6** | 网站搜索索引更新 | Phase 1 全量重建（内容量小，< 1s）。Phase 3 评估增量方案。FlexSearch.js 支持增量追加，迁移成本低 |
| **Q7** | 时区问题 | 全部使用 Asia/Shanghai（UTC+8）。CI Engine 和 ModLib 产出均基于 Asia/Shanghai，无 UTC 数据源 |

---

## 五、Phase 1 启动确认

### MKT 内阁已就绪

- [x] CI Engine JSON schema 文档化
- [x] 10 家公司清单确认
- [x] ModLib 扫描格式文档化
- [x] 7 项疑问全部答复
- [x] 网站路径和权限确认
- [x] Stage 差异度测试工具就绪

### 交付内阁可立即开工的项

| 需求 | 阻塞状态 | 开工条件 |
|------|:--------:|----------|
| SR-CH-001 竞争态势日报 | ✅ 已解除 | CI Engine JSON schema 已提供 |
| SR-WEB-001 网站 MVP | ✅ 已解除 | 样式偏好已确认 |
| SR-KB-001 知识底座框架 | ✅ 已解除 | 目录结构已在规格书中定义 |
| SR-CH-003 开源雷达日报 | ✅ 已解除 | ModLib 格式已提供 |
| SR-APP-001 App Store 扫描 | ⚠️ 建议先 PoC | Product Hunt AI 分类页作为首选 |

### 建议启动顺序

1. **SR-CH-001** — 旗舰频道，最快出可见成果
2. **SR-WEB-001 MVP** — 竞争态势频道页 + 首页，给 CEO 看门面
3. **SR-KB-001 Phase 1** — 框架搭好，频道产出自动归档
4. 并行启动 **SR-APP-001 PoC** — 验证 Product Hunt 数据源可用性

---

*MKT 内阁已全部就绪，交付内阁请启动 Phase 1。过程中任何问题随时沟通。*
