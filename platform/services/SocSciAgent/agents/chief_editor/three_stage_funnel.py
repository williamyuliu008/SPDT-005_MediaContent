"""
chief_editor.three_stage_funnel — 三层漏斗算法 (stub)
"""
from __future__ import annotations

class ThreeStageFunnel:
    """三层漏斗分类器。"""

    def classify(self, text: str) -> str:
        """返回阶段: draft | review | publish。"""
        if not text:
            return "draft"
        length = len(text)
        if length < 200:
            return "draft"
        elif length < 1000:
            return "review"
        return "publish"
