"""
chief_editor.tension_curve — 张力曲线模块 (stub)
"""
from __future__ import annotations
from typing import List

class TensionCurve:
    """张力曲线: 计算文本内容的叙事张力分值。"""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha

    def score(self, text: str) -> float:
        """返回 0.0-1.0 的张力分。"""
        if not text:
            return 0.0
        # stub: 简单启发式
        tension_indicators = sum(1 for w in [
            '然而', '但是', '不过', '却', '矛盾', '冲突', '危险', '危机',
            '高潮', '转折', '崩溃', '决裂', '意外', '震惊'
        ] if w in text)
        return min(1.0, tension_indicators * 0.1)
