# 对抗性审核报告
> 自动生成 | 2026-07-30 14:42 UTC | 模型: deepseek-chat | 消耗: 0 tokens

## 摘要

| 严重性 | 数量 |
|:---|---:|
| MEDIUM | 1 |
| LOW | 3 |
| INFO | 1 |

## 🟡 MEDIUM — 1 项

### 存在多个 science 相关内容类型: ['science_research', 'science_fact'] 🔒 [需人工处理]
- **分类**: `logic`
- **位置**: `content_type_registry.yaml`
- **描述**: science_fact 和 science_research 的定位可能重叠。science_fact（科普知识）指向 smartext/knowledge_graph，science_research 指向 radar_science_fact。两者是否真的需要分离？
- **建议**: 评估是否应合并为单一 science 类型，或明确区分受众和 SLA。

## 🟢 LOW — 3 项

### _default_topic_for_type 缺少类型: breakdown_news ✅ [自动可修复]
- **分类**: `gap`
- **位置**: `pipeline_router.py _default_topic_for_type()`
- **描述**: `breakdown_news` 在 CONTENT_TYPE_MODULES 中注册了，但 _default_topic_for_type() 中没有默认值。
- **建议**: 在 _default_topic_for_type() 的 defaults 字典中添加 'breakdown_news': '内容创作'。

### _default_topic_for_type 缺少类型: science_research ✅ [自动可修复]
- **分类**: `gap`
- **位置**: `pipeline_router.py _default_topic_for_type()`
- **描述**: `science_research` 在 CONTENT_TYPE_MODULES 中注册了，但 _default_topic_for_type() 中没有默认值。
- **建议**: 在 _default_topic_for_type() 的 defaults 字典中添加 'science_research': '内容创作'。

### _default_topic_for_type 缺少类型: deep_industry_report ✅ [自动可修复]
- **分类**: `gap`
- **位置**: `pipeline_router.py _default_topic_for_type()`
- **描述**: `deep_industry_report` 在 CONTENT_TYPE_MODULES 中注册了，但 _default_topic_for_type() 中没有默认值。
- **建议**: 在 _default_topic_for_type() 的 defaults 字典中添加 'deep_industry_report': '内容创作'。

## ℹ️ INFO — 1 项

### render_deep_industry 正确使用 parents[4] ✅ [自动可修复]
- **分类**: `logic`
- **位置**: `render_deep_industry.py`
- **描述**: REPO_ROOT = Path(__file__).resolve().parents[4] 是正确的（text→render→engines→3_render→platform→REPO_ROOT）。
- **建议**: 无需修复，这是正确的。
