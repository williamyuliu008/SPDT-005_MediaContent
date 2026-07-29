# TextClassifier 重定位方案

> 2026-07-12 | 决策：纳入 SPDT-005 shared/smarttext_router/router/

## 背景

TextClassifier 创建于 2026-06-15（PP-20260615-001），定位为"文字产品生产线的统一入口路由器"。当时 SPDT 体系尚未建立（SPDT-005 成立于 2026-07-10），6 集群定义未与 PDT 对齐。

## 问题诊断

### 三方命名不一致

| 维度 | classifier.py | smarttext_router README | SPDT-005 PDT | 对齐状态 |
|---|---|---|---|---|
| A | 快讯/短消息 | 实时快反 | PT-041 FlashNews | ✅ |
| B | 深度分析/报告 | 深度生产 | PT-040 DeepProd | ✅ |
| C | 科普/**教育** | 知识科普(E) | PT-042 SciPop | ❌ |
| D | 技术文档 | 技术文档 | PT-045 TechDoc | ✅ |
| E | 创意/评论 | 观点论证(F) | PT-043 OpEd | ❌ |
| F | 营销/商业文案 | 创意转化(C) | PT-044 CreativeX | ❌ |

### 覆盖范围过大

- C 集群包含"教育"：SPDT-004 才是教育内容的归属
- E/F 边界模糊：PT-043(OpEd) 和 PT-044(CreativeX) 的分界线更清晰
- 缺少跨 SPDT 路由：无法甄别教育类需求并转发 SPDT-004

## 决策

**纳入 SPDT-005，作为 smarttext_router 的 router 子系统。不新建 SPDT。**

### 集群重新映射

| 集群 | 新名称 | 对应 PDT | 说明 |
|---|---|---|---|
| A | FlashNews | PT-041 | 实时快讯/短消息，≤500字 |
| B | DeepProd | PT-040 | 深度分析/报告/白皮书 |
| C | SciPop | PT-042 | 知识科普（**不含教育**）|
| D | TechDoc | PT-045 | 技术文档/API文档/用户手册 |
| E | OpEd | PT-043 | 观点评论/社论/深度思考 |
| F | CreativeX | PT-044 | 品牌创意/营销文案/品牌故事 |

### 新增：跨 SPDT 路由

```
输入检测到"教育/学生/备考/课件/培训"标签
  → 不进入 C 集群
  → 输出 cross_spdt_route: SPDT-004
  → SPDT-004 PT-031(通识教育) 接单
```

## 迁移步骤

1. 复制 `D:\92_products\TextClassifier\src\` → `D:\92_products\SPDT-005_MediaContent\shared\smarttext_router\router\`
2. 修改 `classifier.py`：集群标签对齐 SPDT-005 PDT 名称
3. 修改 `classifier.py`：Cluster C 移除"教育"，新增 `cross_spdt_route` 逻辑
4. 更新 golden tests：15 个测试用例重新标注
5. 更新 `smarttext_router/README.md`：集群名称一致化
6. 归档 `D:\92_products\TextClassifier`（SR-TEXT-001 迁移到 smarttext_router/docs/）
7. 废弃 group_army_test.py（由 golden tests 替代）

## 保留资产

- 4-step pipeline（结构化→分类→配置→反问）
- 10 维 StructuredSpec
- 7-rule 决策树
- 2s 目标延迟（纯规则引擎）
- 15 golden tests + 5 edge cases
- L2 配置模板体系

## 责任人

- SPDT-005 owner: agent-e926h
- 迁移执行: kg
