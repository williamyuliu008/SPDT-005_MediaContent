# SmartText Router — SPDT-005 媒体内容制造 · 入口路由引擎

> 1 Router + 6 PDTs | 4-Step Pipeline: 结构化 → 分类 → 配置 → 反问

## 架构

```
smarttext_router/
├── router/                     SmartText Router (入口路由引擎)
│   ├── classifier.py           4-Step: NL → 10维结构化 → 6 PDT 路由 + Cross-SPDT
│   ├── test_golden.py          15 golden tests (100%) + 6 acceptance criteria
│   ├── llm_gateway.py          LLM 调用网关
│   └── scripts/                测试脚本 + 批量工具
├── docs/                       设计文档
│   ├── proposal/               PP-20260615-001 原始提案
│   ├── references/             SR-TEXT-001 完整规格
│   └── output_samples/         历史分类输出样本
├── clusters/                   各 PDT 生产集群
│   ├── deepprod/               PT-040 深度长文 (6 Stage)
│   ├── flashnews/              PT-041 实时快讯 (4 Stage)
│   ├── scipop/                 PT-042 知识科普 (4 Stage)
│   ├── oped/                   PT-043 观点评论 (4 Stage)
│   ├── creativex/              PT-044 品牌创意 (4 Stage)
│   └── techdoc/                PT-045 技术文档 (4 Stage)
└── config/
    └── platform.yaml           集团军级配置
```

## 路由流程

```
NL需求 → SmartText Router → 10维结构化 → 6 PDT 路由 + Cross-SPDT
  → FlashNews (PT-041)  → 4 Stage: 监测→核查→撰稿→发布
  → DeepProd  (PT-040)  → 6 Stage: 选题→研究→写作→审阅→可视化→交付
  → SciPop    (PT-042)  → 4 Stage: 研究→转化→写作→审查
  → TechDoc   (PT-045)  → 4 Stage: 规格→研究→撰写→审查
  → OpEd      (PT-043)  → 4 Stage: 研究→结构→写作→辩论
  → CreativeX (PT-044)  → 4 Stage: 简报→构思→创作→润色
  → CROSS_SPDT          → 路由到 SPDT-004 (教育内容制造)
```

## 运行

```bash
# 路由器测试
cd router && python test_golden.py    # 15/15, 100%

# CLI 交互测试
python classifier.py
```
