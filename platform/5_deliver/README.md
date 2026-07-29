# 5_deliver · 触达交付层
## 协调型架构 — 多渠道分发

---

## 定位

协调型流水线的**触达交付阶段**。通过 autopublish 多渠道自动发布引擎完成最终分发。

## 核心职责

| 职责 | 说明 |
|:---|:---||
| **M6 人类检查点** | 最终交付确认（敏感内容/品牌确认/发布前检查） |
| **多渠道分发** | web / feeds / mobile / feishu / wechat_mp 一键发布 |
| **发布日志** | 发布记录存档（success/failure + 原因记录） |

## 支持渠道

| 渠道 | 说明 | 对应组件 |
|:---|:---|:---|
| web | 网站/博客发布 | autopublish web 模块 |
| feeds | RSS/Newsletter 分发 | autopublish feeds 模块 |
| mobile | APP/小程序推送 | autopublish mobile 模块 |
| feishu | 飞书文档/消息发布 | autopublish feishu 模块 |
| wechat_mp | 微信公众号发布 | autopublish wechat_mp 模块 |

## 人类检查点（M6）

```
最终发布前检查：
  □ 内容真实性确认（G-FACTUAL summary）
  □ 敏感内容标记（灰区内容人工确认）
  □ 发布时机确认（时效性稿件定时发布）
  □ 渠道匹配确认（目标受众渠道）
  □ 品牌合规确认（品牌调性一致性）
```

## 协调型说明

> 本层引用 platform/infrastructure/autopublish/ 执行分发。
> SPDT-005 不复制 autopublish 代码，仅声明依赖和配置。

## 五阶段映射

| 阶段 | 对应 SOP | 本层实现 |
|:---|:---|:---|
| 5_deliver | M6 | autopublish（多渠道分发） |

## 与 SPDT-004 5_deliver 的关系

| 维度 | SPDT-004（教育） | SPDT-005（媒体） |
|:---|:---|:---|
| 核心组件 | TextExperienceAPP（HarmonyOS） | autopublish（多渠道） |
| 交付渠道 | PC知识图谱 / 手机APP | web / feeds / mobile / feishu / wechat_mp |
| 发布模式 | 用户主动学习（按需获取） | 主动推送（精准触达） |
| 核心差异 | **学习者主动消费** | **内容主动触达受众** |

## 共享：autopublish 引擎

```
platform/infrastructure/autopublish/
```
autopublish 同时服务 SPDT-004 和 SPDT-005：
- SPDT-004：用 autopublish 将课程内容分发到飞书/微信（课程推广）
- SPDT-005：用 autopublish 将媒体内容分发到 web/feeds/公众号（内容分发）
