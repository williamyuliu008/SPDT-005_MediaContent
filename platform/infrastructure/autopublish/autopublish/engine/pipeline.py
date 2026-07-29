"""
pipeline.py — 管道主控
======================
串联 format → deploy → verify 全流程。

用法:
    from autopublish.engine.pipeline import AutoPublishPipeline
    pipeline = AutoPublishPipeline()
    result = pipeline.run("website", content_bundle, date_str="2026-06-22")
"""

from __future__ import annotations
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

from .formatter import ContentFormatter
from .deployer import Deployer
from .analytics import Analytics

logger = logging.getLogger(__name__)


class AutoPublishPipeline:
    """AutoPublish 主控管道：format → deploy → verify。"""

    def __init__(self, root_dir: Path | None = None):
        if root_dir is None:
            root_dir = Path(__file__).parent.parent
        self.root_dir = Path(root_dir)
        self.channels_dir = self.root_dir / "channels"
        self.formatter = ContentFormatter(self.channels_dir)
        self.deployer = Deployer(self.root_dir)
        self.analytics = Analytics()

    def run(
        self,
        channel: str,
        content_bundle: dict[str, Any],
        date_str: str = "",
        draft: bool = False,
    ) -> dict[str, Any]:
        """
        执行完整发布管道。

        Args:
            channel: 渠道 ID
            content_bundle: SmartText 引擎输出的 Content Bundle
            date_str: 日期（默认今天）
            draft: 草稿模式

        Returns:
            管道执行结果
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # 1. 加载渠道配置
        channel_dir = self.channels_dir / channel
        channel_config = self._load_channel_config(channel_dir)

        if not channel_config:
            return {
                "success": False,
                "error": f"渠道配置未找到: {channel_dir / 'channel.yaml'}",
                "channel": channel,
                "date": date_str,
            }

        # 2. Format
        logger.info(f"[Pipeline] 开始格式化: channel={channel}, date={date_str}")
        try:
            formatted = self.formatter.format(content_bundle, channel_config)
        except Exception as e:
            self.analytics.record_deploy(channel, date_str, "format_failed", {"error": str(e)})
            return {"success": False, "error": f"格式化失败: {e}", "channel": channel, "date": date_str}

        # 3. Deploy
        logger.info(f"[Pipeline] 开始部署: channel={channel}, date={date_str}")
        try:
            deploy_result = self.deployer.deploy(channel, formatted, content_bundle, date_str, draft=draft)
        except Exception as e:
            self.analytics.record_deploy(channel, date_str, "deploy_failed", {"error": str(e)})
            return {"success": False, "error": f"部署失败: {e}", "channel": channel, "date": date_str}

        # 4. Verify（占位）
        verified = self._verify(deploy_result, channel_config)

        # 5. 记录
        self.analytics.record_deploy(
            channel, date_str,
            "success" if deploy_result.get("success") else "failed",
            {"deploy": deploy_result, "verified": verified},
        )

        return {
            "success": deploy_result.get("success", False),
            "channel": channel,
            "date": date_str,
            "formatted": {
                "format": formatted.get("format"),
                "word_count": formatted.get("meta", {}).get("word_count", 0),
            },
            "deploy": deploy_result,
            "verified": verified,
        }

    def _load_channel_config(self, channel_dir: Path) -> dict[str, Any]:
        """加载渠道配置。"""
        import yaml
        config_path = channel_dir / "channel.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _verify(self, deploy_result: dict[str, Any], channel_config: dict[str, Any]) -> dict[str, Any]:
        """部署后验证（占位）。"""
        # TODO: 实现实际验证逻辑
        return {
            "status": "placeholder",
            "checks": ["deploy_result_exists"],
            "all_passed": deploy_result.get("success", False),
        }
