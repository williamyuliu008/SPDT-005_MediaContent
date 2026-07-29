"""
deployer.py — 部署器
====================
将格式化后的内容部署到目标渠道。

支持的部署方式:
- website: 文件写入 + 搜索索引重建
- wechat_mp: 占位（微信公众号草稿箱）
- feishu: 占位（飞书消息发送）
- email: 占位（邮件发送）

新增渠道只需创建 channels/xxx/channel.yaml 和对应的 build/deploy 脚本，
引擎代码无需修改。
"""

from __future__ import annotations
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── 搜索索引构建器 ──────────────────────────────────────────

def _build_search_index(content_bundle: dict[str, Any], date_str: str) -> dict[str, Any]:
    """从 Content Bundle 中提取信号，构建搜索索引。"""
    signals = content_bundle.get("signals", [])
    items: list[dict[str, Any]] = []
    companies_seen: set[str] = set()
    tags_seen: set[str] = set()

    for sig in signals:
        title = sig.get("title", "")
        summary = sig.get("summary", "")

        item = {
            "date": date_str,
            "title": title,
            "summary": summary[:200] if summary else "",
            "content": summary or "",
            "path": "/#",
            "importance_score": sig.get("importance_score", 0.0),
            "sentiment": sig.get("sentiment", "neutral"),
            "companies": sig.get("companies", []),
            "tags": sig.get("tags", []),
            "section": sig.get("section", ""),
        }
        items.append(item)
        for c in item.get("companies", []):
            companies_seen.add(c)
        for t in item.get("tags", []):
            tags_seen.add(t)

    return {
        "build_time": datetime.now().isoformat(),
        "latest_date": date_str,
        "total_signals": len(items),
        "companies_covered": len(companies_seen),
        "items": items,
    }


# ── 部署器 ──────────────────────────────────────────────────

class Deployer:
    """通用多渠道部署器。"""

    def __init__(self, root_dir: Path | None = None):
        if root_dir is None:
            root_dir = Path(__file__).parent.parent
        self.root_dir = Path(root_dir)
        self.channels_dir = self.root_dir / "channels"

    def deploy(
        self,
        channel: str,
        formatted_content: dict[str, Any],
        content_bundle: dict[str, Any],
        date_str: str,
        draft: bool = False,
    ) -> dict[str, Any]:
        """
        将内容部署到指定渠道。

        Args:
            channel: 渠道 ID（如 "website", "wechat_mp"）
            formatted_content: formatter 输出
            content_bundle: 原始 Content Bundle（用于索引构建等）
            date_str: 日期字符串 YYYY-MM-DD
            draft: 是否草稿模式（不实际发布）

        Returns:
            {"success": True, "channel": "website", "deploy_path": "...", ...}
        """
        if channel == "website":
            return self._deploy_website(formatted_content, content_bundle, date_str, draft)
        elif channel == "wechat_mp":
            return self._deploy_wechat_mp(formatted_content, date_str, draft)
        elif channel == "feishu":
            return self._deploy_feishu(formatted_content, date_str, draft)
        else:
            # 通用：查找渠道目录，尝试执行 build 命令
            return self._deploy_generic(channel, formatted_content, date_str, draft)

    # ── website 部署 ────────────────────────────────────────

    def _deploy_website(
        self,
        formatted_content: dict[str, Any],
        content_bundle: dict[str, Any],
        date_str: str,
        draft: bool = False,
    ) -> dict[str, Any]:
        """部署到自用网站。"""
        channel_dir = self.channels_dir / "website"
        channel_config = self._load_channel_config(channel_dir)

        # 确定部署目标路径
        deploy_to = channel_config.get("publishing", {}).get("deploy_to", "")
        if deploy_to:
            deploy_dir = Path(deploy_to)
        else:
            deploy_dir = Path("canvas/ai-lookout/")

        if draft:
            logger.info(f"[website] 草稿模式，跳过实际写入")
            return {
                "success": True,
                "channel": "website",
                "mode": "draft",
                "deploy_path": str(deploy_dir),
                "date": date_str,
            }

        deploy_dir.mkdir(parents=True, exist_ok=True)

        # 1. 构建完整 HTML 页面
        html_content = self._wrap_html_page(formatted_content["content"], date_str)
        index_path = deploy_dir / "index.html"
        index_path.write_text(html_content, encoding="utf-8")
        logger.info(f"[website] HTML 写入: {index_path}")

        # 2. 构建搜索索引
        import json
        idx = _build_search_index(content_bundle, date_str)
        idx_dir = deploy_dir / "search"
        idx_dir.mkdir(parents=True, exist_ok=True)
        idx_path = idx_dir / "index.json"
        idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[website] 索引写入: {idx_path} ({idx['total_signals']} 条信号)")

        # 3. 尝试执行渠道自定义 build 脚本
        build_script = channel_dir / "build.py"
        if build_script.exists():
            logger.info(f"[website] 执行构建脚本: {build_script}")
            try:
                result = subprocess.run(
                    [sys.executable, str(build_script), "--date", date_str],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=str(channel_dir),
                )
                if result.returncode == 0:
                    logger.info(f"[website] build.py 成功:\n{result.stdout}")
                else:
                    logger.warning(f"[website] build.py 失败:\n{result.stderr}")
            except Exception as e:
                logger.warning(f"[website] build.py 执行异常: {e}")

        return {
            "success": True,
            "channel": "website",
            "mode": "live",
            "deploy_path": str(deploy_dir),
            "index_path": str(idx_path),
            "date": date_str,
            "total_signals": idx["total_signals"],
        }

    # ── 占位渠道 ────────────────────────────────────────────

    def _deploy_wechat_mp(self, formatted_content: dict[str, Any], date_str: str, draft: bool = False) -> dict[str, Any]:
        """微信公众号部署（占位）。"""
        mode = "draft" if draft else "publish"
        logger.info(f"[wechat_mp] 占位部署: mode={mode}, date={date_str}")
        # TODO: 接入微信公众号 API
        return {
            "success": True,
            "channel": "wechat_mp",
            "mode": mode,
            "status": "placeholder",
            "date": date_str,
        }

    def _deploy_feishu(self, formatted_content: dict[str, Any], date_str: str, draft: bool = False) -> dict[str, Any]:
        """飞书消息部署（占位）。"""
        logger.info(f"[feishu] 占位部署: date={date_str}")
        # TODO: 接入飞书消息 API
        return {
            "success": True,
            "channel": "feishu",
            "mode": "live",
            "status": "placeholder",
            "date": date_str,
        }

    def _deploy_generic(self, channel: str, formatted_content: dict[str, Any], date_str: str, draft: bool = False) -> dict[str, Any]:
        """通用渠道部署（占位）。"""
        logger.info(f"[{channel}] 通用占位部署: date={date_str}")
        return {
            "success": True,
            "channel": channel,
            "mode": "live" if not draft else "draft",
            "status": "placeholder",
            "date": date_str,
        }

    # ── 辅助方法 ────────────────────────────────────────────

    def _load_channel_config(self, channel_dir: Path) -> dict[str, Any]:
        """加载渠道配置。"""
        import yaml
        config_path = channel_dir / "channel.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _wrap_html_page(self, body_html: str, date_str: str) -> str:
        """将 body HTML 包装为完整页面。"""
        yesterday = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

        nav_dates = f"""
    <div class="date-nav">
        <a href="/?date={yesterday}">← 前一天</a>
        <span class="date-nav-current">{date_str}</span>
        <a href="/?date={tomorrow}">后一天 →</a>
    </div>"""

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 瞭望台 · {date_str}</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <script src="https://cdn.jsdelivr.net/npm/flexsearch@0.7.31/dist/flexsearch.bundle.js"></script>
</head>
<body>
<header>
    <div class="header-inner">
        <a href="/" class="logo"><span class="icon">🔭</span>AI 瞭望台<span class="subtitle">· AI 产业情报自动化</span></a>
        <nav>
            <a href="/" class="active">今日</a>
            <a href="/archive/">📂 归档</a>
            <a href="/search/">🔍 搜索</a>
            <a href="/knowledge/">🧠 知识</a>
        </nav>
    </div>
</header>
<main>
    {nav_dates}
    <article class="daily-report">
        {body_html}
    </article>
    {nav_dates}
</main>
<footer>
    <p>AI 瞭望台 · SmartTextPlatform 自动化运营</p>
    <p>追踪 10 家 AI 核心公司 · 每日 10:30 自动更新</p>
</footer>
</body>
</html>"""

    # ── CLI 入口 ────────────────────────────────────────────

    @staticmethod
    def cli():
        """命令行入口：autopublish deploy ..."""
        import argparse

        parser = argparse.ArgumentParser(description="AutoPublish — 多渠道内容分发")
        sub = parser.add_subparsers(dest="cmd")

        # deploy
        dep = sub.add_parser("deploy", help="部署到指定渠道")
        dep.add_argument("--channel", required=True, help="渠道 ID")
        dep.add_argument("--date", required=True, help="日期 YYYY-MM-DD")
        dep.add_argument("--draft", action="store_true", help="草稿模式")

        # status
        st = sub.add_parser("status", help="查看发布状态")
        st.add_argument("--channel", required=True, help="渠道 ID")

        # stats
        stats = sub.add_parser("stats", help="查看运营数据")
        stats.add_argument("--channel", required=True, help="渠道 ID")
        stats.add_argument("--days", type=int, default=7, help="统计天数")

        args = parser.parse_args()

        deployer = Deployer()

        if args.cmd == "deploy":
            # 从 Content Bundle 文件加载
            bundle_path = Path(f"channels/{args.date}.md")
            if bundle_path.exists():
                content_bundle = {
                    "date": args.date,
                    "formats": {"daily_report": {"markdown": bundle_path.read_text(encoding="utf-8")}},
                    "signals": [],
                }
            else:
                logger.warning(f"未找到 {bundle_path}，使用空 Content Bundle")
                content_bundle = {"date": args.date, "formats": {}, "signals": []}

            # 加载渠道配置
            from autopublish.engine.formatter import ContentFormatter
            formatter = ContentFormatter()
            channel_config = deployer._load_channel_config(deployer.channels_dir / args.channel)
            formatted = formatter.format(content_bundle, channel_config)

            result = deployer.deploy(args.channel, formatted, content_bundle, args.date, draft=args.draft)
            import json
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.cmd == "status":
            print(f"渠道 {args.channel} 状态: 占位（待实现）")

        elif args.cmd == "stats":
            from autopublish.engine.analytics import Analytics
            a = Analytics()
            stats = a.get_stats(args.channel, args.days)
            import json
            print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    Deployer.cli()
