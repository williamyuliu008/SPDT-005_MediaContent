# 3_render — 渲染生产

> **SOP 阶段**：M4（质量门禁 + 多形态渲染）
> **SOP 规范**：`内容制造管线执行规范 v1.0` §2.3

---

## 目录结构

```
3_render/
├── quality/              ← 质量门禁（本次实现）
│   ├── __init__.py
│   ├── media_gates.py    ← G-SOURCE / G-TIMELINESS / G-FACTUAL / G-STYLE
│   ├── _run_test.py      ← 20项集成测试（全过）
│   └── README.md          ← 本文件
│
└── README.md              ← 本文件（父级）
```

---

## 质量门禁（media_gates.py）

### 门禁一览

| 门禁 ID | 名称 | 检查内容 | 路径 |
|:---|:---|:---|:--:|
| **G-SOURCE** | 信源可靠性 | 信任等级 ≥ D（0.6），支持 article_v2 和 scene_v2 格式 | sunshine / gray_zone / failure |
| **G-TIMELINESS** | 时效性 | 按 content_type 动态阈值（breaking_news ≤ 4h / 深度 ≤ 72h） | sunshine / gray_zone / failure |
| **G-FACTUAL** | 事实核查 | 数字声明溯源 + factuality metadata 标注 | sunshine / gray_zone / failure |
| **G-STYLE** | 风格合规 | 体裁结构 + 禁用表达 + content_type 特检 | sunshine / gray_zone / failure |

### 使用方式

```python
from quality.media_gates import MediaGateRunner, GSourceGate

# 批量执行
runner = MediaGateRunner()
result = runner.run_all(article_v2_data)

if result["overall_pass"]:
    print("所有门禁通过")
else:
    print(f"失败: {result['failure_gates']}")
    print(f"需审核: {result['gray_zone_gates']}")

# 单独执行
source_gate = GSourceGate()
r = source_gate.check({"sources": [{"name": "CNBC", "trust_level": "C"}]})
print(r.path.value)  # sunshine
```

### 门禁结果（GateResult）

```python
GateResult(
    gate_id="G-SOURCE",
    gate_name="信源可靠性",
    path=GatePath.SUNSHINE,  # sunshine | gray_zone | failure
    passed=True,
    verdict="PASS",           # PASS | FAIL | REVIEW_REQUIRED
    score=0.75,
    detail="信源通过，D+级以上...",
    violations=[],            # 违规项
    recommendations=[]        # 改进建议
)
```

---

## 门禁路径语义

| 路径 | 语义 | 动作 |
|:---|:---|:---|
| **sunshine** | 自动通过 | 直接进入下一阶段 |
| **gray_zone** | 需人工审核 | 生成 GrayZoneTicket，触发 M4 人类检查点 |
| **failure** | 硬违规 | 生成 FailureReport，回链 2_structure 修正 |

---

## 与 SPDT-004 通用门禁的关系

| 门禁 | SPDT-004 | SPDT-005 |
|:---|:---|:---|
| G-STRUCTURE | ✅ universal_gates.py | ✅ 复用 SPDT-004 |
| G-FORMAT | ✅ universal_gates.py | ✅ 复用 SPDT-004 |
| G-REUSE | ✅ universal_gates.py | ✅ 复用 SPDT-004 |
| G-REGISTRY | ✅ universal_gates.py | ✅ 复用 SPDT-004 |
| G-SOURCE | N/A | ✅ 本模块实现 |
| G-TIMELINESS | N/A | ✅ 本模块实现 |
| G-FACTUAL | N/A | ✅ 本模块实现 |
| G-STYLE | N/A | ✅ 本模块实现 |

> **设计原则**：通用门禁（G-STRUCTURE/G-FORMAT/G-REUSE/G-REGISTRY）在 SPDT-004 中维护一次，SPDT-005 通过 junction 引用。媒体专用门禁在 SPDT-005 中独立实现，通过 MODLIB 共享（未来）。

---

## 调用时机

```
2_structure (ManuscriptsEngine)
        ↓  article_v2 / breaking_news / tech_explainer
        ↓
3_render/quality/media_gates.py  ← G-SOURCE / G-TIMELINESS / G-FACTUAL / G-STYLE
        ↓  GatePath.SUNSHINE
多形态渲染（图文/音频/视频/卡片）
        ↓
4_adapt (质量记分卡)
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|:---|:---|:---|
| v1.0 | 2026-07-30 | 初版：G-SOURCE / G-TIMELINESS / G-FACTUAL / G-STYLE 实现，20项测试全过 |
