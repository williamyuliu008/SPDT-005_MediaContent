"""
AutoPublish Engine — 通用多渠道内容分发引擎
============================================
将 Content Bundle（SmartText 引擎输出）转换为渠道特定格式并部署。

用法:
    from autopublish.engine.pipeline import AutoPublishPipeline
    pipeline = AutoPublishPipeline()
    result = pipeline.run("website", content_bundle, date_str="2026-06-22")
"""

__version__ = "1.0.0"
