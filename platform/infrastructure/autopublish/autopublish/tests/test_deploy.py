"""
test_deploy.py — AutoPublish 独立部署测试
==========================================
验证:
1. website 渠道部署
2. 新渠道注册（不改引擎代码）
"""

import json
import sys
import tempfile
from pathlib import Path

# 将 autopublish 加入 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.formatter import ContentFormatter, md_to_html
from engine.deployer import Deployer, _build_search_index
from engine.pipeline import AutoPublishPipeline


# ── Mock 数据 ───────────────────────────────────────────────

MOCK_CONTENT_BUNDLE = {
    "date": "2026-06-17",
    "formats": {
        "daily_report": {
            "markdown": """# 🔭 AI 瞭望台 · 2026年6月17日

## 竞争态势

**OpenAI 发布 GPT-5 推理能力大幅提升**
> 来源 OpenAI Blog | 类型 capability | 影响力 9.5
> OpenAI 今天正式发布了 GPT-5 模型，在推理能力上相比 GPT-4 有了质的飞跃。

**Google DeepMind 推出 Gemini 3 多模态架构**
> 来源 Google Research | 类型 capability | 影响力 8.8
> Gemini 3 引入全新的多模态融合机制，在视觉理解任务上超越人类水平。

## 芯事

**NVIDIA B300 量产启动，台积电 3nm 产能满载**
> 来源 台媒电子时报 | 类型 supply_chain | 影响力 9.0
> NVIDIA 下一代 Blackwell Ultra B300 GPU 已进入量产阶段。

---

*本日报由 AI 瞭望台自动生成*
""",
            "word_count": 350,
            "sections": {
                "compete": {
                    "label": "竞争态势",
                    "items": [
                        {"title": "OpenAI 发布 GPT-5", "summary": "OpenAI 今天正式发布了 GPT-5 模型..."},
                        {"title": "Google DeepMind 推出 Gemini 3", "summary": "Gemini 3 引入全新的多模态融合机制..."},
                    ],
                },
                "chips": {
                    "label": "芯事",
                    "items": [
                        {"title": "NVIDIA B300 量产启动", "summary": "NVIDIA 下一代 Blackwell Ultra B300 GPU 已进入量产阶段。"},
                    ],
                },
            },
        }
    },
    "signals": [
        {
            "title": "OpenAI 发布 GPT-5 推理能力大幅提升",
            "summary": "OpenAI 今天正式发布了 GPT-5 模型，在推理能力上相比 GPT-4 有了质的飞跃。",
            "section": "竞争态势",
            "importance_score": 9.5,
            "sentiment": "positive",
            "companies": ["OpenAI"],
            "tags": ["model_release", "frontier"],
        },
        {
            "title": "Google DeepMind 推出 Gemini 3 多模态架构",
            "summary": "Gemini 3 引入全新的多模态融合机制，在视觉理解任务上超越人类水平。",
            "section": "竞争态势",
            "importance_score": 8.8,
            "sentiment": "positive",
            "companies": ["Google"],
            "tags": ["model_release", "multimodal"],
        },
        {
            "title": "NVIDIA B300 量产启动，台积电 3nm 产能满载",
            "summary": "NVIDIA 下一代 Blackwell Ultra B300 GPU 已进入量产阶段。",
            "section": "芯事",
            "importance_score": 9.0,
            "sentiment": "positive",
            "companies": ["NVIDIA"],
            "tags": ["hardware", "GPU", "supply_chain"],
        },
    ],
}


# ── 测试用例 ───────────────────────────────────────────────

def test_formatter_html():
    """测试格式转换：Markdown → HTML"""
    formatter = ContentFormatter()
    channel_config = {
        "channel": {"id": "website", "name": "测试网站", "type": "internal"},
        "content": {"primary": "daily_report", "output_format": "html"},
    }
    result = formatter.format(MOCK_CONTENT_BUNDLE, channel_config)

    assert result["channel"] == "website"
    assert result["format"] == "html"
    assert "<h1" in result["content"]
    assert "<h2>竞争态势</h2>" in result["content"]
    assert "OpenAI" in result["content"]
    assert result["meta"]["word_count"] == 350
    print("✅ test_formatter_html 通过")


def test_formatter_markdown():
    """测试格式转换：保持 Markdown"""
    formatter = ContentFormatter()
    channel_config = {
        "channel": {"id": "feishu", "name": "飞书", "type": "internal"},
        "content": {"primary": "daily_report", "output_format": "markdown"},
    }
    result = formatter.format(MOCK_CONTENT_BUNDLE, channel_config)

    assert result["format"] == "markdown"
    assert "## 竞争态势" in result["content"]
    print("✅ test_formatter_markdown 通过")


def test_formatter_plain():
    """测试格式转换：纯文本"""
    formatter = ContentFormatter()
    channel_config = {
        "channel": {"id": "email", "name": "邮件", "type": "external"},
        "content": {"primary": "daily_report", "output_format": "plain"},
    }
    result = formatter.format(MOCK_CONTENT_BUNDLE, channel_config)

    assert result["format"] == "plain"
    assert "##" not in result["content"]  # markdown removed
    assert "竞争态势" in result["content"]
    print("✅ test_formatter_plain 通过")


def test_formatter_max_chars():
    """测试内容截断"""
    formatter = ContentFormatter()
    channel_config = {
        "channel": {"id": "wechat_mp", "name": "公众号", "type": "external"},
        "content": {"primary": "daily_report", "output_format": "markdown", "max_chars": 100},
    }
    result = formatter.format(MOCK_CONTENT_BUNDLE, channel_config)
    assert len(result["content"]) <= 150  # 允许截断标记的额外字符
    print("✅ test_formatter_max_chars 通过")


def test_search_index():
    """测试搜索索引构建"""
    idx = _build_search_index(MOCK_CONTENT_BUNDLE, "2026-06-17")

    assert idx["total_signals"] == 3
    assert idx["companies_covered"] == 3
    assert len(idx["items"]) == 3
    assert idx["items"][0]["importance_score"] == 9.5
    assert "NVIDIA" in idx["items"][2]["companies"]
    print("✅ test_search_index 通过")


def test_deploy_website_dry():
    """测试 website 部署（不实际写入文件，用临时目录）"""
    import tempfile
    import yaml

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建临时 channels/website/channel.yaml（deploy_to 指向临时目录）
        tmp_channels = Path(tmpdir) / "channels"
        website_dir = tmp_channels / "website"
        website_dir.mkdir(parents=True)

        deploy_target = Path(tmpdir) / "deploy_output"
        channel_yaml_data = {
            "channel": {"id": "website", "name": "测试", "type": "internal"},
            "publishing": {"deploy_to": str(deploy_target)},
            "content": {"primary": "daily_report", "output_format": "html"},
        }
        with open(website_dir / "channel.yaml", "w", encoding="utf-8") as f:
            yaml.dump(channel_yaml_data, f, allow_unicode=True)

        # 使用自定义 root_dir 的 deployer
        deployer = Deployer(root_dir=Path(tmpdir))
        formatter = ContentFormatter(channels_dir=tmp_channels)
        channel_config = deployer._load_channel_config(website_dir)

        formatted = formatter.format(MOCK_CONTENT_BUNDLE, channel_config)
        result = deployer._deploy_website(formatted, MOCK_CONTENT_BUNDLE, "2026-06-17", draft=False)

        assert result["success"] is True
        assert result["channel"] == "website"
        assert (deploy_target / "index.html").exists()
        assert (deploy_target / "search" / "index.json").exists()

        # 验证 HTML 内容
        html = (deploy_target / "index.html").read_text(encoding="utf-8")
        assert "AI 瞭望台" in html
        assert "OpenAI" in html
        assert "flexsearch" in html

        print("✅ test_deploy_website_dry 通过")


def test_deploy_placeholder_channels():
    """测试占位渠道部署"""
    deployer = Deployer()
    formatter = ContentFormatter()

    for channel in ["wechat_mp", "feishu"]:
        result = deployer.deploy(
            channel,
            {"content": "test", "format": "markdown"},
            MOCK_CONTENT_BUNDLE,
            "2026-06-17",
        )
        assert result["success"] is True
        assert result["channel"] == channel
        assert result["status"] == "placeholder"

    print("✅ test_deploy_placeholder_channels 通过")


def test_pipeline():
    """测试完整管道"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建临时渠道配置
        channel_dir = Path(tmpdir) / "channels" / "website"
        channel_dir.mkdir(parents=True)

        import yaml
        channel_yaml = {
            "channel": {"id": "website", "name": "测试", "type": "internal"},
            "publishing": {"deploy_to": str(Path(tmpdir) / "deploy")},
            "content": {"primary": "daily_report", "output_format": "html"},
        }
        with open(channel_dir / "channel.yaml", "w", encoding="utf-8") as f:
            yaml.dump(channel_yaml, f, allow_unicode=True)

        # 使用自定义 root_dir 创建 pipeline
        pipeline = AutoPublishPipeline(root_dir=Path(tmpdir))

        result = pipeline.run("website", MOCK_CONTENT_BUNDLE, date_str="2026-06-17")

        assert result["success"] is True
        assert result["channel"] == "website"
        assert result["formatted"]["word_count"] == 350

        print("✅ test_pipeline 通过")


def test_new_channel_registration():
    """测试：新增渠道——仅创建 channel.yaml，不改引擎代码即可注册"""
    import tempfile
    import yaml

    with tempfile.TemporaryDirectory() as tmpdir:
        # 在临时目录模拟 channels/ 结构
        channels_dir = Path(tmpdir) / "channels"
        test_channel_dir = channels_dir / "test"
        test_channel_dir.mkdir(parents=True)

        # 创建 test 渠道的 channel.yaml
        channel_config = {
            "channel": {"id": "test", "name": "测试渠道", "type": "internal"},
            "publishing": {"schedule": "0 12 * * *"},
            "content": {"primary": "daily_report", "output_format": "markdown"},
        }
        with open(test_channel_dir / "channel.yaml", "w", encoding="utf-8") as f:
            yaml.dump(channel_config, f, allow_unicode=True)

        # 使用 formatter（不修改引擎代码）
        formatter = ContentFormatter(channels_dir=channels_dir)
        result = formatter.format(MOCK_CONTENT_BUNDLE, channel_config)

        assert result["channel"] == "test"
        assert result["format"] == "markdown"

        # 使用 deployer（不修改引擎代码）
        deployer = Deployer(root_dir=Path(tmpdir))
        deployer.channels_dir = channels_dir
        deploy_result = deployer.deploy("test", result, MOCK_CONTENT_BUNDLE, "2026-06-17")

        assert deploy_result["success"] is True
        assert deploy_result["channel"] == "test"

        print("✅ test_new_channel_registration 通过（仅 channel.yaml，不改引擎代码）")


# ── 主入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AutoPublish 独立部署测试")
    print("=" * 60)

    tests = [
        test_formatter_html,
        test_formatter_markdown,
        test_formatter_plain,
        test_formatter_max_chars,
        test_search_index,
        test_deploy_website_dry,
        test_deploy_placeholder_channels,
        test_pipeline,
        test_new_channel_registration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} 失败: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"结果: {passed} 通过 / {failed} 失败 / {len(tests)} 总计")
    print(f"{'=' * 60}")

    if failed > 0:
        sys.exit(1)
