# 5_deliver/results/ 输出目录说明

> v1.2+ 采用的分层目录结构

## 目录结构

```
results/
├── README.md              ← 本文档
├── MANIFEST.json          ← 全部文件的清单（自动生成）
│
├── delivered/             ← ✅ 最终发布成品（action=deliver）
│   ├── oped_argument/     ← 观点评论
│   ├── deep_industry_report/
│   ├── science_research/
│   ├── breakdown_news/
│   └── ...
│
├── revise/                ← ⚠️  待修改稿件（action=revise）
│   ├── oped_argument/
│   └── ...
│
└── archive/               ← 📁 历史文件（测试废弃 / 早期版本）
    ├── breakdown_news/     ← 大量早期测试 JSON
    ├── science_research/
    └── ...
```

## 文件命名规范

### Markdown（成品）
```
{content_type}_{title_slug}_{date}_{score}.md

示例：
oped_argument_AI_jianguan_2026-07-31_83.md
deep_industry_report_半导体国产化_2026-07-30_89.md
```

### Pipeline JSON（管线结果）
```
PL_{content_type}_{shortId}.json

示例：
PL_oped_argument_F6A52857.json
PL_deep_industry_report_16005339.json
```

## 三层生命周期

| 阶段 | 目录 | 说明 |
|:---|:---|:---|
| 新产出 | `results/` | 管线运行后立即写入 |
| 待审核 | `revise/` | score 70-80，需人工修改 |
| 已归档 | `archive/` | 历史测试/废弃文件 |

## MANIFEST.json

自动生成的清单文件，包含所有已分类文件的列表。

```json
{
  "generated_at": "2026-07-31T...",
  "delivered": { "oped_argument": ["file.md"] },
  "revise": {},
  "archive": { "breakdown_news": ["PL_*.json", ...] }
}
```
