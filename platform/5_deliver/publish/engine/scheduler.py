"""
scheduler.py — 定时调度器
=========================
解析 campaign 或 channel 中的 cron 表达式，触发定时发布。
当前为占位实现，实际调度由外部 cron 系统管理。
"""

from __future__ import annotations
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class Scheduler:
    """定时调度器——解析调度配置，判断当前是否应执行。"""

    def __init__(self, campaigns_dir: Optional[Path] = None):
        if campaigns_dir is None:
            campaigns_dir = Path(__file__).parent.parent / "campaigns" / "active"
        self.campaigns_dir = Path(campaigns_dir)

    def should_run(self, schedule: str, now: Optional[datetime] = None) -> bool:
        """检查 cron 表达式是否匹配当前时间。（占位：始终返回 True）"""
        # TODO: 实现 cron 解析（使用 croniter 库）
        logger.debug(f"Schedule check: {schedule} → always true (placeholder)")
        return True

    def next_run(self, schedule: str, now: Optional[datetime] = None) -> datetime:
        """计算下次执行时间。（占位）"""
        if now is None:
            now = datetime.now()
        logger.debug(f"Next run for {schedule} → {now}")
        return now  # placeholder

    def list_campaigns(self) -> list[Path]:
        """列出所有活跃的发布计划。"""
        if not self.campaigns_dir.exists():
            return []
        return list(self.campaigns_dir.glob("*.yaml"))
