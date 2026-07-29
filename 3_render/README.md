# 3_render · 渲染生产层
## 协调型架构 — 多形态渲染

---

## 定位

协调型流水线的**多形态渲染阶段**。将结构化稿件渲染为多种交付形态（图文 / 音频 / 视频 / 卡片）。

## 核心职责

| 职责 | 说明 |
|:---|:---|
| **M4 质量门禁** | G-AUDIT / G-COGNITION / G-INTERFACE 阳光/灰区/失败路径 |
| **多形态渲染** | 同一稿件渲染为：图文版 / 音频版 / 视频版 / 卡片版 |
| **渲染引擎** | 复用 SPDT-004 的 video_factory / audio_factory |

## 渲染类型

| 形态 | 说明 | 复用 SPDT-004 组件 |
|:---|:---|:---|
| 图文版 | 原始 article_v2 稿件（网页/公众号格式） | — |
| 音频版 | 文字→语音（audio_scene_*.mp3） | SPDT-004 video_factory |
| 视频版 | 场景帧 + 音频合成 | SPDT-004 video_factory |
| 卡片版 | 关键信息提取 → 知识卡片 | SPDT-004 video_factory |

## 质量门禁（3_render 核心）

```
G-SOURCE     → 来源可信度 ≥ D
G-TIMELINESS → 快讯内容时效性验证
G-FACTUAL    → 事实准确性审计（关键数据点交叉验证）
G-STYLE      → 风格一致性（目标受众匹配）
G-STRUCTURE  → 结构完整性（引言/正文/结论）
G-FORMAT     → 格式合规性（标题/字数/标签）
```

| 路径 | 条件 | 处理 |
|:---|:---|:---|
| **阳光路径** | 全部门禁 PASS | 自动输出到 4_adapt |
| **灰区路径** | G-SOURCE/G-TIMELINESS 警告 | 人工签批后输出 |
| **失败路径** | 任意 critical 失败 | 回写修正（退回到 2_structure） |

## 协调型说明

> 渲染执行依赖 SPDT-004 的 video_factory（跨 PDT 复用）。
> 本层声明依赖关系，不复制渲染代码。

## 五阶段映射

| 阶段 | 对应 SOP | 本层实现 |
|:---|:---|:---|
| 3_render | M4 | quality_gate + video_factory 引用 |

## 与 SPDT-004 3_render 的关系

| 维度 | SPDT-004（教育） | SPDT-005（媒体） |
|:---|:---|:---|
| 渲染引擎 | video_factory（自含） | 引用 SPDT-004 video_factory |
| 渲染形态 | 音频/视频/卡片 | 图文/音频/视频/卡片（更宽泛） |
| 质量门禁 | G-COGNITION / G-AUDIT | G-SOURCE / G-TIMELINESS / G-FACTUAL（更偏媒体） |
| 核心差异 | **自含生产** | **复用协调** |
