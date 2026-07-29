# SR-ARCH-001：三段工具链架构重构

**发件方：** MKT内阁  
**收件方：** 交付内阁  
**文档类型：** 架构设计需求规格  
**优先级：** P0（当前紧耦合阻碍后续扩展）  
**日期：** 2026-06-22  
**版本：** v1.0

---

## 一、背景

SmartTextPlatform 当前架构存在严重耦合：`daily.py` 同时负责信号采集（Radar）、文字生成（SmartText）、网站输出（分发），改动一处即牵动全身。后续计划扩展多领域雷达（金融/政策/教育）、多分发渠道（公众号/飞书/邮件），耦合架构将导致维护成本指数增长。

**核心认知：** 文字生产线需要三段独立的工具链——Radar（信息挖掘与过滤）、SmartText（文字创作与深加工）、AutoPublish（发布与运营管理）。每段都是通用平台，通过标准接口串联。Radar 通过填充领域字段形成领域雷达，AutoPublish 通过填充渠道配置形成多渠道分发。

---

## 二、部署策略

| 平台 | 部署位置 | 理由 |
|------|----------|------|
| **Radar Platform** | `D:\9_infra\radar_platform` | 纯通用基础设施，服务所有内阁。领域配置方式接入 |
| **SmartText Platform** | `D:\92_products\SmartTextPlatform`（保持原位） | 已有完整测试体系和产品沉淀。重构为可 import 的引擎 |
| **AutoPublish Platform** | `D:\9_infra\autopublish` | 纯通用基础设施。渠道配置方式接入 |

---

## 三、Radar Platform 需求规格

### 3.1 目录结构

```
D:\9_infra\radar_platform\
├── engine/                          ← 通用引擎（所有领域共用）
│   ├── collector.py                 │   采集器：搜索+抓取+API 调度
│   ├── classifier.py                │   分类器：6种信号类型自动分类
│   ├── scorer.py                    │   评分器：按类型拆维加权评分
│   ├── verifier.py                  │   验证器：L1-L4 可验证性阶梯
│   ├── pipeline.py                  │   管道：collect→classify→score→verify
│   └── __init__.py
│
├── domains/                         ← 领域配置
│   ├── ai_tech/                     │   AI科技情报雷达
│   │   ├── domain.yaml              │   领域定义
│   │   ├── sources.yaml             │   信源注册表
│   │   └── taxonomy.yaml            │   信号分类规则（可选，覆盖默认）
│   ├── _template/                   │   领域模板（供新建领域参考）
│   │   └── domain.yaml
│   └── ...                          │   未来：finance/ policy/ education/
│
├── schemas/
│   ├── signal_bundle.json           ← 标准信号输出 Schema
│   └── domain_config.json           ← 领域配置文件 Schema
│
├── bundles/                         ← 信号存档（按领域×日期）
│   └── ai_tech/
│       └── 2026-06/
│           └── 0622.json
│
└── tests/
    └── test_pipeline.py
```

### 3.2 领域配置模板

```yaml
# domains/ai_tech/domain.yaml
domain:
  id: "ai_tech"
  name: "AI科技情报雷达"
  description: "全球AI产业信号扫描"

sources:
  primary:
    - nvidia_newsroom
    - openai_blog
    - sec_edgar
    # ... 指向 sources.yaml 中的信源ID
  secondary:
    - semianalysis
    - theinformation
    # ...

signal_types:                # 该领域关注的信号类型（复用通用分类器）
  - capability
  - structural
  - supply_chain
  - ecosystem
  - paradigm

scoring:                     # 按信号类型的评分权重（覆盖默认）
  capability:
    performance_leap: 0.40
    competitive_gap: 0.30
    time_to_market: 0.30

output:
  bundle_format: "signal_bundle_v1"
  target_formats: ["smarttext"]     # 输出给 SmartText
```

### 3.3 标准接口

**CLI：** `radar scan --domain ai_tech [--date YYYY-MM-DD]`

**输出：** Signal Bundle JSON

```json
{
  "bundle_id": "ai_tech_20260622",
  "domain": "ai_tech",
  "date": "2026-06-22",
  "meta": {"signals_count": 18, "companies_covered": 10, "avg_confidence": 0.87},
  "signals": [{
    "id": "sig_001",
    "type": "capability",
    "company": "nvidia",
    "title": "...",
    "summary": "...",
    "importance_score": 0.95,
    "confidence": 0.98,
    "verifiability": "L4",
    "source_url": "https://...",
    "tags": ["hardware", "edge_ai"],
    "scoring_dimensions": {
      "performance_leap": {"score": 0.90, "rationale": "..."},
      "competitive_gap": {"score": 0.95, "rationale": "..."}
    }
  }]
}
```

### 3.4 从现有代码迁移

| 现有文件 | 迁移目标 |
|----------|----------|
| `radar/source_registry.yaml` | `domains/ai_tech/sources.yaml` |
| `radar/signal_taxonomy.py` | `engine/classifier.py` |
| `radar/scoring_rubric.py` | `engine/scorer.py` |
| `radar/verifiability.py` | `engine/verifier.py` |
| `radar/pipeline.py` + `dispatch.py` | `engine/pipeline.py` |

---

## 四、SmartText Platform 重构需求

### 4.1 目标

保持 `D:\92_products\SmartTextPlatform` 位置不变，但将引擎重构为可独立运行的模块。核心改动：**将 prompt 从代码中独立到配置文件，将内容形态从 daily.py 中独立到 formats/。**

### 4.2 目录结构

```
D:\92_products\SmartTextPlatform\
├── smartext/                        ← 文字创作引擎（新增）
│   ├── engine.py                    │   引擎主入口（从 shared/cluster_engine_v3.py 重构）
│   ├── llm_gateway.py              │   LLM 网关（从 shared/ 迁入）
│   ├── __init__.py
│   │
│   ├── clusters/                    │   六赛道（已有，路径不变）
│   │   ├── flashnews/
│   │   ├── deepprod/
│   │   ├── creativex/
│   │   ├── techdoc/
│   │   ├── scipop/
│   │   └── oped/
│   │
│   ├── formats/                     │   内容形态模板（新增）
│   │   ├── daily_report.py          │   日报
│   │   ├── weekly_brief.py          │   周报
│   │   ├── monthly_review.py        │   月报
│   │   ├── wechat_article.py        │   公众号文章
│   │   └── feishu_message.py        │   飞书消息
│   │
│   └── prompts/                     │   Prompt 配置（从代码独立）
│       ├── flashnews.yaml
│       ├── deepprod.yaml
│       └── ...
│
├── router/                          ← 路由器（不变）
├── clusters/                        ← 保留兼容路径（不变）
├── shared/                          ← 保留兼容路径（不变）
├── tests/                           ← 测试（不变）
└── ...
```

### 4.3 引擎入口接口

```python
# smartext/engine.py
class SmartTextEngine:
    def generate(self, signal_bundle: dict, format: str, **options) -> dict:
        """
        输入: Signal Bundle JSON + 内容形态名称
        输出: Content Bundle JSON
        
        format: 'daily_report' | 'weekly_brief' | 'wechat_article' | ...
        """
```

### 4.4 内容形态模板

每个 `formats/xxx.py` 定义一种从信号到文字作品的转化逻辑：

```python
# formats/daily_report.py
FORMAT_SPEC = {
    "name": "日报",
    "input_signal_types": ["capability", "structural", "supply_chain", "ecosystem"],
    "sections": [
        {"id": "compete", "label": "竞争态势", "cluster": "deepprod", "signal_type": "capability", "max_items": 3},
        {"id": "chips", "label": "芯事", "cluster": "flashnews", "signal_type": "supply_chain", "max_items": 3},
        # ...
    ],
    "output_format": "markdown"
}
```

### 4.5 独立测试能力

SmartText 应可脱离 Radar 独立测试：
```python
from smartext.engine import SmartTextEngine
engine = SmartTextEngine()
result = engine.generate(mock_signal_bundle, "daily_report")
assert result["formats"]["daily_report"]["word_count"] > 1000
```

---

## 五、AutoPublish Platform 需求规格

### 5.1 目录结构

```
D:\9_infra\autopublish\
├── engine/                          ← 通用引擎
│   ├── scheduler.py                 │   定时调度器
│   ├── formatter.py                 │   格式转换器（Content Bundle → 渠道格式）
│   ├── deployer.py                  │   部署器（文件写入/API推送/邮件发送）
│   ├── analytics.py                 │   运营数据采集
│   ├── pipeline.py                  │   管道：format→deploy→verify
│   └── __init__.py
│
├── channels/                        ← 渠道配置
│   ├── website/                     │   自用网站
│   │   ├── channel.yaml             │   渠道定义
│   │   └── templates/               │   页面模板
│   ├── wechat_mp/                   │   微信公众号
│   │   └── channel.yaml
│   ├── feishu/                      │   飞书消息
│   │   └── channel.yaml
│   ├── email/                       │   邮件 Newsletter
│   │   └── channel.yaml
│   └── _template/                   │   渠道模板
│       └── channel.yaml
│
├── campaigns/                       ← 运营活动
│   └── active/
│       └── ai_lookout_daily.yaml    # 每天的发布计划
│
├── stats/                           ← 运营数据
│   └── website/
│
└── tests/
```

### 5.2 渠道配置模板

```yaml
# channels/website/channel.yaml
channel:
  id: "website"
  name: "AI瞭望台网站"
  type: "internal"              # internal(自用) | external(对外)

publishing:
  schedule: "0 10 * * *"
  build_command: "python build.py --date {date}"
  deploy_to: "canvas/ai-lookout/"

content:
  primary: "daily_report"       # 主内容：日报全文
  archive:                      # 归档内容
    - "weekly_brief"
    - "monthly_review"

error:
  on_fail: "fallback_yesterday"
  max_retries: 1
```

```yaml
# channels/wechat_mp/channel.yaml
channel:
  id: "wechat_mp"
  name: "AI瞭望台公众号"
  type: "external"

publishing:
  schedule: "0 8 * * *"
  workflow: "draft_then_publish"   # 先草稿，人工确认

content:
  primary: "wechat_article"
  max_chars: 3000

format:
  auto_cover: true
  author: "AI瞭望台"
```

### 5.3 CLI

```bash
autopublish deploy --channel website --date 2026-06-22
autopublish deploy --channel wechat_mp --date 2026-06-22 --draft
autopublish status --channel website       # 查看发布状态
autopublish stats --channel website --days 7  # 查看运营数据
```

---

## 六、编排层

`build_all.py` 从"一个脚本做四件事"重构为三段编排：

```python
# build_all.py（重构后）
def main():
    # Layer 1: Radar
    bundle = run_radar("ai_tech", date_str)
    
    # Layer 2: SmartText
    content = run_smartext(bundle, "daily_report")
    
    # Layer 3: AutoPublish
    run_autopublish(content, "website")
    # run_autopublish(content, "feishu")  # 未来
```

---

## 七、实施计划

### Phase 1：Radar Platform 独立（1天）

1. 创建 `D:\9_infra\radar_platform\` 目录结构
2. 迁移 `radar/` 下的 5 个模块到 `engine/`
3. 创建 `domains/ai_tech/` 领域配置
4. 创建 `domains/_template/` 领域模板
5. 验证：`radar scan --domain ai_tech` 产出标准 Signal Bundle

### Phase 2：SmartText 引擎化（1天）

1. 创建 `smartext/` 目录和 `engine.py`
2. 将 prompt 独立到 `prompts/*.yaml`
3. 创建 `formats/daily_report.py` 作为首个内容形态
4. 引擎入口 `SmartTextEngine.generate(signal_bundle, format)`
5. 重构 `daily.py` 调用新引擎
6. 回归测试：Stage 差异度不退化

### Phase 3：AutoPublish 独立（1天）

1. 创建 `D:\9_infra\autopublish\` 目录结构
2. 迁移网站构建逻辑到 `channels/website/`
3. 渠道配置模板
4. 重构 `build_all.py` 为三段编排

### Phase 4：清理（0.5天）

1. 移除旧的 `daily.py` 中冗余代码
2. 更新所有 cron 任务
3. 更新文档

---

## 八、验收标准

| 验收项 | 方法 | 标准 |
|--------|------|------|
| Radar 独立运行 | `radar scan --domain ai_tech` | 产出标准 Signal Bundle JSON |
| 新领域接入 | 创建 `domains/test/domain.yaml` | 改配置即可运行，不改引擎代码 |
| SmartText 独立运行 | `SmartTextEngine.generate(mock_bundle, "daily_report")` | 产出 Content Bundle |
| 新增格式模板 | 创建 `formats/test.py` | 不改引擎代码即可注册新格式 |
| AutoPublish 独立运行 | `autopublish deploy --channel website` | 网站正常构建 |
| 新增分发渠道 | 创建 `channels/test/channel.yaml` | 改配置即可，不改引擎代码 |
| 回归测试 | `tests/continuous/run_all.py` | L1/L2/L3 全部通过 |
| 日报质量 | `build_all.py` 生成今日日报 | 内容与重构前一致 |

---

*需求规格书结束。交付内阁请评估工期和技术细节，MKT 内阁可随时配合澄清。*
