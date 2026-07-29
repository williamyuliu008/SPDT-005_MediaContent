# AutoPublish Platform

**通用多渠道内容分发基础设施** — 将 SmartText 引擎输出的 Content Bundle 自动发布到网站、公众号、飞书等渠道。

```
D:\9_infra\autopublish\
```

## 架构

```
                  Content Bundle (SmartText 引擎输出)
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  AutoPublish Pipeline                │
│                                                      │
│   format ───────► deploy ───────► verify             │
│   (格式转换)       (渠道部署)       (发布验证)          │
│                                                      │
│   ContentFormatter   Deployer       Analytics         │
└─────────────────────────────────────────────────────┘
         │                  │
         ▼                  ▼
   渠道特定格式          website / wechat_mp / feishu / ...
   (HTML/MD/Plain)      (文件写入 / API推送 / 占位)
```

## 目录结构

```
autopublish/
├── engine/                      # 通用引擎
│   ├── pipeline.py              # 管道主控：format → deploy → verify
│   ├── formatter.py             # 格式转换（Content Bundle → 渠道格式）
│   ├── deployer.py              # 部署器（文件写入/API推送）
│   ├── scheduler.py             # 定时调度器
│   ├── analytics.py             # 运营数据采集（占位）
│   └── __init__.py
│
├── channels/                    # 渠道配置（新增渠道只需加 channel.yaml）
│   ├── website/                 # AI瞭望台网站
│   │   ├── channel.yaml
│   │   ├── build.py             # 网站构建脚本
│   │   └── templates/
│   ├── wechat_mp/               # 微信公众号（占位）
│   │   └── channel.yaml
│   ├── feishu/                  # 飞书消息（占位）
│   │   └── channel.yaml
│   └── _template/               # 渠道模板
│       └── channel.yaml
│
├── campaigns/                   # 运营活动
│   └── active/
│       └── ai_lookout_daily.yaml
│
└── tests/
    └── test_deploy.py           # 9 项测试，全部通过
```

## 快速开始

### 部署到网站

```bash
# 通过 pipeline（推荐）
cd D:\9_infra\autopublish
python -c "
from engine.pipeline import AutoPublishPipeline
from pathlib import Path

pipeline = AutoPublishPipeline()
md = Path('D:/92_products/SmartTextPlatform/channels/2026-06-17.md').read_text(encoding='utf-8')
bundle = {'date': '2026-06-17', 'formats': {'daily_report': {'markdown': md}}, 'signals': []}
result = pipeline.run('website', bundle, date_str='2026-06-17')
print(result['success'])
"

# 或使用独立构建脚本
cd D:\9_infra\autopublish\channels\website
python build.py --date 2026-06-17
```

### 新增渠道（不改引擎代码）

```bash
# 1. 创建渠道目录和配置
mkdir D:\9_infra\autopublish\channels\my_channel
cp D:\9_infra\autopublish\channels\_template\channel.yaml D:\9_infra\autopublish\channels\my_channel\

# 2. 编辑 channel.yaml（修改 id、name、content.primary、output_format 等）

# 3. 直接使用
python -c "
from engine.pipeline import AutoPublishPipeline
pipeline = AutoPublishPipeline()
result = pipeline.run('my_channel', bundle, date_str='2026-06-17')
"
```

### 运行测试

```bash
cd D:\9_infra\autopublish
python tests\test_deploy.py
```

## Content Bundle 格式

AutoPublish 接收 SmartText 引擎输出的标准 Content Bundle：

```json
{
  "date": "2026-06-17",
  "formats": {
    "daily_report": {
      "markdown": "# AI 瞭望台...",
      "sections": { ... },
      "word_count": 2500
    }
  },
  "signals": [
    {
      "title": "OpenAI 发布 GPT-5",
      "summary": "...",
      "section": "竞争态势",
      "importance_score": 9.5,
      "companies": ["OpenAI"],
      "tags": ["model_release", "frontier"]
    }
  ]
}
```

## 渠道配置格式

```yaml
channel:
  id: "website"
  name: "AI瞭望台网站"
  type: "internal"

publishing:
  schedule: "0 10 * * *"
  deploy_to: "D:/92_products/SmartTextPlatform/canvas/ai-lookout/"

content:
  primary: "daily_report"       # Content Bundle 中的 format key
  output_format: "html"         # html | markdown | plain

error:
  on_fail: "fallback_yesterday"
  max_retries: 1
```

## 验收状态

| 验收项 | 状态 |
|--------|------|
| Formatter: Markdown → HTML/MD/Plain | ✅ |
| Deployer: website 文件写入 + 搜索索引 | ✅ |
| Pipeline: format → deploy → verify | ✅ |
| 新增渠道（仅 channel.yaml） | ✅ |
| 独立测试（9/9 通过） | ✅ |
| 构建脚本迁移（build_site.py → build.py） | ✅ |
| 占位渠道（wechat_mp、feishu） | ✅ |
