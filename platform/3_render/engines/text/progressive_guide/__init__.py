"""progressive_guide — 渐进式引导模块：全书设计 + 风格尝味 + 框架预览 + 统一合成器"""
from .taste_sampler import TastingSampler, TastingResult, TasteSample, STYLE_DEFINITIONS
from .framework_preview import FrameworkPreview, FrameworkPreviewResult, ChapterOutline, MaterialSummary
from .unified_preview_composer import (
    UnifiedPreviewComposer,
    UnifiedPreviewResult,
    StyleChoicePhase,
    PhaseState,
)
from .book_design import (
    BookDesignGenerator,
    BookDesign,
    BookScheme,
    ChapterDesign,
)

__all__ = [
    # ── 全书设计（BookDesignGenerator）─────────────────
    "BookDesignGenerator",
    "BookDesign",
    "BookScheme",
    "ChapterDesign",
    # ── 风格尝味（TastingSampler）────────────────────────
    "TastingSampler",
    "TastingResult",
    "TasteSample",
    "STYLE_DEFINITIONS",
    # ── 框架预览（FrameworkPreview）─────────────────────
    "FrameworkPreview",
    "FrameworkPreviewResult",
    "ChapterOutline",
    "MaterialSummary",
    # ── 统一合成器（UnifiedPreviewComposer）──────────────
    "UnifiedPreviewComposer",
    "UnifiedPreviewResult",
    "StyleChoicePhase",
    "PhaseState",
]
