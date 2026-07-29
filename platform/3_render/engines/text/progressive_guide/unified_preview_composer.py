"""
progressive_guide.unified_preview_composer
==========================================
统一预览合成器：将「风格尝味」+「框架预览」合二为一，
让用户在「同一界面」看到：
  1. 三种风格样章（局部品鉴）
  2. 全局章节结构（整体骨架）
  3. 关键取材摘要（内容原料）

用户一次确认「风格 + 框架 + 取材」，对齐真正意图后再进入全量生成。

使用方式（两阶段）：
    composer = UnifiedPreviewComposer()

    # Phase 1: 风格尝味（快速，1次 LLM 调用 × 3风格）
    style_phase = composer.build_style_preview(user_input)

    # ... 用户在前端点选风格 → composer.apply_style_choice(style_phase, chosen_style)

    # Phase 2: 框架预览（需要 orchestration + material_scout 数据）
    unified = composer.build_framework_preview(
        user_input=user_input,
        style_phase=style_phase,          # 来自 Phase 1
        orchestration_output=cog_data,     # 来自 ChiefEditor + Orchestration
        material_scout_output=materials,   # 来自 MaterialScout
    )

    # Phase 3: 用户确认
    # unified.to_unified_user_facing() → 前端渲染
    # unified.apply_unified_feedback(feedback) → 进入 pipeline 或重新迭代
"""
from __future__ import annotations
import logging, os, sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# ── 路径设置 ─────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

logger = logging.getLogger("UnifiedPreviewComposer")

# ── 子模块引用 ─────────────────────────────────────────────
from .taste_sampler import TastingSampler, TastingResult, TasteSample, STYLE_DEFINITIONS
from .framework_preview import (
    FrameworkPreview,
    FrameworkPreviewResult,
    ChapterOutline,
    MaterialSummary,
)


# ── 枚举：统一预览的阶段状态 ──────────────────────────────
class PhaseState(Enum):
    PENDING   = "pending"    # 尚未开始
    READY     = "ready"     # 已生成，等待用户确认
    APPROVED  = "approved"  # 用户已确认
    REJECTED  = "rejected"  # 用户已拒绝
    MODIFIED  = "modified"  # 用户已修改


# ── Phase 1：风格尝味结果 ─────────────────────────────────
@dataclass
class StyleChoicePhase:
    """
    Phase 1 的完整状态。
    包含 TastingResult + 用户当前是否已选择风格 + 风格选中后的增强 Brief。
    """
    raw_result: TastingResult              # 来自 TastingSampler 的原始 TastingResult
    chosen_style: Optional[str] = None     # 用户选择的风格（None = 尚未选择）
    phase_state: PhaseState = PhaseState.PENDING
    selected_sample: Optional[TasteSample] = None  # 用户选中的样章
    taste_brief: Optional[Dict[str, Any]] = None  # 选中后的增强 Brief（传给 framework）

    @property
    def is_style_locked(self) -> bool:
        return self.chosen_style is not None


# ── Phase 2：框架预览结果 ─────────────────────────────────
# （复用 FrameworkPreviewResult，不另起炉灶）


# ── 统一预览完整结果 ─────────────────────────────────────
@dataclass
class UnifiedPreviewResult:
    """
    统一预览的完整状态（Phase 1 + Phase 2 合并）。
    这是传给 pipeline 或用户确认的核心数据结构。
    """
    # ── 来源信息 ──────────────────────────────────────────
    user_input: Dict[str, Any]  # 用户原始输入（theme, characters, themes...）

    # ── Phase 1：风格尝味 ─────────────────────────────────
    style_phase: StyleChoicePhase

    # ── Phase 2：框架预览 ─────────────────────────────────
    framework_result: Optional[FrameworkPreviewResult] = None

    # ── 最终状态 ──────────────────────────────────────────
    overall_state: PhaseState = PhaseState.PENDING
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # ── 合并后的增强 context（传给 pipeline）─────────────
    # 包含 style + chapter_outline + materials，pipeline 可直接使用
    enhanced_context: Dict[str, Any] = field(default_factory=dict)

    # ── 便捷属性 ──────────────────────────────────────────
    @property
    def is_style_ready(self) -> bool:
        return self.style_phase.is_style_locked

    @property
    def is_framework_ready(self) -> bool:
        return self.framework_result is not None

    @property
    def is_fully_approved(self) -> bool:
        return (
            self.overall_state == PhaseState.APPROVED
            and self.is_style_ready
            and self.is_framework_ready
        )

    def summary_text(self) -> str:
        """生成一行事先摘要，供 CLI/日志使用。"""
        style = self.style_phase.chosen_style or "未选择"
        chapters = (
            self.framework_result.chapter_count
            if self.framework_result
            else "?"
        )
        status = self.overall_state.value
        return (
            f"[UnifiedPreview] style={style} | chapters={chapters} | "
            f"status={status} | generated={self.generated_at[:19]}"
        )


# ── 统一预览合成器 ────────────────────────────────────────
class UnifiedPreviewComposer:
    """
    统一预览合成器。

    将 TastingSampler（风格尝味）和 FrameworkPreview（框架预览）
    合二为一，确保用户在同一界面确认「风格 + 框架 + 取材」后再进入全量生成。

    设计原则：
    1. 两阶段独立可调用（Phase 1 快速，Phase 2 较重）
    2. 风格选择会影响框架预览的措辞（框架描述风格与样章风格对齐）
    3. 一次 unified feedback 处理所有修改
    4. CLI 和 GUI 共用同一数据结构，通过 to_unified_user_facing() 渲染

    与 pipeline 的集成：
        # pipeline_runner.py 中：
        if args.progressive:
            composer = UnifiedPreviewComposer()
            # Phase 1: 风格尝味
            style_phase = composer.build_style_preview(user_input)
            # 等待用户点选风格（CLI: print + input; GUI: API 返回）
            chosen = ask_user_style_selection(style_phase)
            composer.apply_style_choice(style_phase, chosen)
            # Phase 2: 框架预览
            unified = composer.build_framework_preview(
                user_input=user_input,
                style_phase=style_phase,
                orchestration_output=orchestration_result,
                material_scout_output=material_result,
            )
            # 等待用户确认框架
            feedback = ask_user_framework_confirmation(unified)
            composer.apply_unified_feedback(unified, feedback)
            # 注入增强 context
            user_input.update(unified.enhanced_context)
            # 进入 pipeline Stage 1...
    """

    def __init__(self, llm_client=None):
        self._tasting = TastingSampler(llm_client=llm_client)
        self._framework = FrameworkPreview(llm_client=llm_client)

    # ── Phase 1: 风格尝味 ─────────────────────────────────

    def build_style_preview(
        self,
        user_input: Dict[str, Any],
        style_list: List[str] = None,
    ) -> StyleChoicePhase:
        """
        快速生成 3 种风格的微样章（Phase 1）。

        参数：
            user_input: {"theme": "...", "characters": [...], "themes": [...], ...}
            style_list: 可选，指定风格列表，默认 3 种

        返回：
            StyleChoicePhase：包含 TastingResult，用户可在 UI 中点选风格
        """
        logger.info(f"[Phase1] Building style preview for: {user_input.get('theme', '?')}")

        style_list = style_list or list(STYLE_DEFINITIONS.keys())

        tasting_result = self._tasting.taste(
            theme=user_input.get("chapter_title", user_input.get("theme", "待定")),
            characters=user_input.get("characters", []),
            themes=user_input.get("themes", []),
            style_list=style_list,
        )

        return StyleChoicePhase(
            raw_result=tasting_result,
            chosen_style=None,
            phase_state=PhaseState.READY,
            selected_sample=None,
        )

    def apply_style_choice(
        self,
        style_phase: StyleChoicePhase,
        chosen_style_or_index: Any,
    ) -> StyleChoicePhase:
        """
        将用户选择的风格写入 Phase 状态。

        参数：
            chosen_style_or_index: str（风格ID，如 "narrative_casual"）
                                  或 int（样章序号 0/1/2）
                                  或 TasteSample 对象
        """
        if isinstance(chosen_style_or_index, int):
            # 按序号选取
            samples = style_phase.raw_result.samples
            idx = max(0, min(chosen_style_or_index, len(samples) - 1))
            chosen_sample = samples[idx]
        elif isinstance(chosen_style_or_index, TasteSample):
            chosen_sample = chosen_style_or_index
        elif isinstance(chosen_style_or_index, str):
            # 按风格ID选取
            chosen_sample = next(
                (s for s in style_phase.raw_result.samples
                 if s.style == chosen_style_or_index),
                style_phase.raw_result.samples[0],
            )
        else:
            chosen_sample = style_phase.raw_result.samples[0]

        # 生成增强 taste_brief（传入 framework preview）
        taste_brief = self._tasting.build_taste_brief(
            selected_sample=chosen_sample,
            all_samples=style_phase.raw_result.samples,
            theme=style_phase.raw_result.theme,
            characters=style_phase.raw_result.characters,
            themes=style_phase.raw_result.themes,
        )

        style_phase.chosen_style = chosen_sample.style
        style_phase.selected_sample = chosen_sample
        style_phase.taste_brief = taste_brief
        style_phase.phase_state = PhaseState.APPROVED
        logger.info(f"[Phase1] Style locked: {chosen_sample.style} ({chosen_sample.label})")
        return style_phase

    # ── Phase 2: 框架预览 ────────────────────────────────

    def build_framework_preview(
        self,
        user_input: Dict[str, Any],
        style_phase: StyleChoicePhase,
        orchestration_output: Dict[str, Any],
        material_scout_output: Dict[str, Any],
    ) -> UnifiedPreviewResult:
        """
        生成全局章节框架预览（Phase 2）。
        必须先完成 Phase 1（风格已选）再调用。

        参数：
            user_input: 用户原始输入
            style_phase: Phase 1 的结果（风格已确认）
            orchestration_output: ChiefEditor + Orchestration 的输出（包含 COG）
            material_scout_output: MaterialScout 的输出（包含 candidate_materials）

        返回：
            UnifiedPreviewResult：包含完整预览 + 待用户确认
        """
        if not style_phase.is_style_locked:
            logger.warning("[Phase2] Style not yet selected. Framework preview still built but not final.")
            # 允许继续（用于演示），但日志警告

        # 注入已选风格到 user_input（影响框架的文风描述）
        enriched_input = dict(user_input)
        if style_phase.is_style_locked:
            enriched_input["style"] = style_phase.chosen_style
            # 同时传入 taste_brief 的风格指引
            brief = style_phase.raw_result.taste_brief
            enriched_input["style_guidance"] = brief.get("style_guidance", "")
            enriched_input["style_focus"] = brief.get("focus", [])

        logger.info(
            f"[Phase2] Building framework preview: "
            f"style={style_phase.chosen_style or 'unlocked'} | "
            f"theme={user_input.get('chapter_title', user_input.get('theme', '?'))}"
        )

        framework_result = self._framework.build(
            orchestration_output=orchestration_output,
            material_scout_output=material_scout_output,
            user_input=enriched_input,
        )

        # 构建统一增强 context（pipeline 直接使用）
        enhanced_context = self._build_unified_context(
            user_input=enriched_input,
            style_phase=style_phase,
            framework_result=framework_result,
        )

        unified = UnifiedPreviewResult(
            user_input=user_input,
            style_phase=style_phase,
            framework_result=framework_result,
            overall_state=PhaseState.READY,
            enhanced_context=enhanced_context,
        )

        logger.info(f"[Phase2] Framework ready: {framework_result.chapter_count} chapters")
        return unified

    def _build_unified_context(
        self,
        user_input: Dict[str, Any],
        style_phase: StyleChoicePhase,
        framework_result: FrameworkPreviewResult,
    ) -> Dict[str, Any]:
        """
        将风格 + 框架 + 取材合并为一个增强 context，
        传给 pipeline 的 ControlledGeneration。
        """
        brief = style_phase.taste_brief or {}

        return {
            # ── 风格 ──────────────────────────────────────
            "style": style_phase.chosen_style,
            "style_label": framework_result.style_label,
            "style_guidance": brief.get("style_guidance", ""),
            "style_focus": brief.get("focus", []),
            "avoid_focus": brief.get("avoid_focus", []),
            "tasted_sample_content": brief.get("tasted_sample_content", ""),

            # ── 框架 ──────────────────────────────────────
            "chapter_outline": framework_result.enhanced_context.get("chapter_outline", []),
            "global_tension_arc": framework_result.global_tension_arc,
            "tension_arc_description": framework_result.materials.tension_arc,

            # ── 取材 ──────────────────────────────────────
            "materials": {
                "events": framework_result.materials.events,
                "figures": framework_result.materials.figures,
                "institutions": framework_result.materials.institutions,
                "ideas": framework_result.materials.ideas,
                "total_events": framework_result.materials.total_events,
                "total_figures": framework_result.materials.total_figures,
            },

            # ── 元信息 ───────────────────────────────────
            "theme": framework_result.theme,
            "overall_theme": framework_result.overall_theme,
            "chapter_count": framework_result.chapter_count,
            "pipeline_stage_hint": "controlled_generation",
            "approval_timestamp": datetime.now().isoformat(),
        }

    # ── 统一用户界面渲染 ─────────────────────────────────

    def to_unified_user_facing(
        self,
        unified: UnifiedPreviewResult,
    ) -> Dict[str, Any]:
        """
        将 UnifiedPreviewResult 渲染为前端可直接使用的统一结构。
        包含：风格样章 + 章节大纲 + 取材摘要 + 张力曲线 + 操作选项

        这是一个完整的「全局预览界面」，用户在此做最终确认。
        """
        fr = unified.framework_result
        sp = unified.style_phase.raw_result

        # 风格样章
        style_samples = []
        for i, s in enumerate(sp.samples):
            is_selected = (unified.style_phase.chosen_style == s.style)
            style_samples.append({
                "id": i,
                "style": s.style,
                "label": s.label,
                "description": s.description,
                "content": s.content,
                "is_selected": is_selected,
                "select_hint": "✓ 已选" if is_selected else "点击选择",
            })

        # 章节大纲
        chapters_data = []
        tension_emoji = {
            "开篇引入": "🌒", "矛盾积累": "🌓", "高潮时刻": "🌕",
            "回落收束": "🌗", "结局": "🌑", "平稳叙述": "🌙",
            "发展展开": "🌔", "高潮与衰落": "⚡", "上升至高潮": "🔥",
        }
        if fr:
            for ch in fr.chapters:
                chapters_data.append({
                    "number": ch.chapter,
                    "title": ch.title,
                    "subtitle": ch.subtitle,
                    "tension": {
                        "level": ch.tension_level,
                        "label": ch.tension_label,
                        "emoji": tension_emoji.get(ch.tension_label, "📖"),
                    },
                    "key_events": ch.key_events,
                    "key_figures": ch.key_figures,
                    "estimated_chars": ch.estimated_chars,
                })

        # 取材摘要
        materials_data = {}
        if fr:
            materials_data = {
                "total_events": fr.materials.total_events,
                "total_figures": fr.materials.total_figures,
                "events": fr.materials.events,
                "figures": fr.materials.figures,
                "institutions": fr.materials.institutions,
                "ideas": fr.materials.ideas,
            }

        # 张力曲线
        tension_arc_chart = fr.global_tension_arc if fr else []

        # 确认状态
        style_status = (
            f"已选：{unified.style_phase.selected_sample.label}"
            if unified.style_phase.selected_sample
            else "等待选择风格"
        )
        framework_status = (
            f"{fr.chapter_count}章框架就绪"
            if fr
            else "框架预览生成中..."
        )

        # 完整统一界面
        return {
            # ── 页面标题 ────────────────────────────────────
            "page": {
                "title": f"《{unified.user_input.get('chapter_title', unified.user_input.get('theme', '待定'))}》创作预览",
                "subtitle": (
                    fr.overall_theme if fr
                    else "全局预览：风格 + 框架 + 取材"
                ),
                "style": unified.user_input.get("style", "narrative_casual"),
                "style_label": fr.style_label if fr else "待定",
                "generated_at": unified.generated_at,
            },

            # ── 区块 1：风格样章（Phase 1）──────────────────
            "style_section": {
                "title": "✦ 风格预览",
                "subtitle": "先看看你的作品可能的样子——选一个你喜欢的讲法",
                "status": style_status,
                "is_locked": unified.style_phase.is_style_locked,
                "samples": style_samples,
                "style_definition": {
                    k: {
                        "label": v["label"],
                        "description": v["description"],
                    }
                    for k, v in STYLE_DEFINITIONS.items()
                },
            },

            # ── 区块 2：章节框架（Phase 2）──────────────────
            "framework_section": {
                "title": "✦ 章节设计",
                "subtitle": "整体骨架——章节结构与张力曲线",
                "status": framework_status,
                "is_ready": unified.is_framework_ready,
                "chapter_count": fr.chapter_count if fr else 0,
                "chapters": chapters_data,
                "tension_arc_chart": tension_arc_chart,
                "tension_arc_label": (
                    fr.materials.tension_arc if fr else "待生成"
                ),
            },

            # ── 区块 3：关键取材（Phase 2）──────────────────
            "materials_section": {
                "title": "✦ 关键取材",
                "subtitle": "这些历史事件和人物将被编织进故事",
                "is_ready": unified.is_framework_ready,
                **materials_data,
            },

            # ── 区块 4：张力曲线 ────────────────────────────
            "tension_chart": {
                "title": "✦ 全局张力曲线",
                "data": tension_arc_chart,
                "chapter_count": fr.chapter_count if fr else 0,
            },

            # ── 统一操作选项 ───────────────────────────────
            "approval_options": [
                {
                    "action": "full_approve",
                    "label": "✅ 全部确认，开始生成",
                    "description": (
                        "风格 + 框架 + 取材均符合预期，"
                        f"生成 {fr.chapter_count if fr else "?"} 章正文"
                    ),
                    "enabled": unified.style_phase.is_style_locked and unified.is_framework_ready,
                },
                {
                    "action": "modify_style_only",
                    "label": "↩ 重选风格",
                    "description": "对当前章节框架满意，但想换一种讲法",
                    "enabled": True,
                },
                {
                    "action": "modify_framework",
                    "label": "✏️ 调整章节框架",
                    "description": "修改章节标题、张力分布或关键取材",
                    "enabled": unified.is_framework_ready,
                },
                {
                    "action": "regenerate_all",
                    "label": "🔄 重新生成预览",
                    "description": "对风格和框架都不满意，重新开始",
                    "enabled": True,
                },
                {
                    "action": "stop",
                    "label": "⛔ 暂停，另改意图",
                    "description": "整体不符合预期，重新输入创作意图",
                    "enabled": True,
                },
            ],

            # ── 提示语 ─────────────────────────────────────
            "hints": {
                "style_not_selected": "请先在上方选择一种风格（点击样章）",
                "framework_not_ready": "框架预览生成中，请稍候……",
                "ready_to_generate": "一切就绪！确认后进入全量生成",
            },

            # ── 传给 pipeline 的增强 context（只读快照）─────
            "_enhanced_context": unified.enhanced_context,
        }

    # ── 统一反馈处理 ─────────────────────────────────────

    def apply_unified_feedback(
        self,
        unified: UnifiedPreviewResult,
        feedback: Dict[str, Any],
    ) -> UnifiedPreviewResult:
        """
        处理用户对统一预览的反馈。

        feedback 格式：
        {
            "action": "full_approve" | "modify_style_only" | "modify_framework"
                    | "regenerate_all" | "stop",
            "style_choice": "narrative_casual",          # 仅 modify_style_only
            "chapter_changes": {                          # 仅 modify_framework
                1: {"title": "新标题", "tension_level": 0.5},
                2: {"key_events": ["新事件"]}
            }
        }
        """
        action = feedback.get("action", "full_approve")

        if action == "stop":
            unified.overall_state = PhaseState.REJECTED
            logger.info("[UnifiedFeedback] User stopped.")
            return unified

        if action == "modify_style_only":
            new_style = feedback.get("style_choice")
            if new_style:
                self.apply_style_choice(unified.style_phase, new_style)
            unified.overall_state = PhaseState.MODIFIED
            logger.info(f"[UnifiedFeedback] Style changed to: {new_style}")
            return unified

        if action == "modify_framework":
            changes = feedback.get("chapter_changes", {})
            if unified.framework_result and changes:
                unified.framework_result = self._framework.apply_user_feedback(
                    unified.framework_result,
                    {"action": "modify_chapter", "changes": changes},
                )
                # 重建 enhanced context
                unified.enhanced_context = self._build_unified_context(
                    unified.user_input, unified.style_phase, unified.framework_result
                )
            unified.overall_state = PhaseState.MODIFIED
            logger.info(f"[UnifiedFeedback] Framework modified: {list(changes.keys())}")
            return unified

        if action == "regenerate_all":
            # 重置状态，用户需重新走 Phase 1
            unified.style_phase = StyleChoicePhase(
                raw_result=unified.style_phase.raw_result,  # 保留 theme 等元信息
                phase_state=PhaseState.PENDING,
            )
            unified.framework_result = None
            unified.overall_state = PhaseState.PENDING
            unified.enhanced_context = {}
            logger.info("[UnifiedFeedback] Reset to Phase 1.")
            return unified

        if action == "full_approve":
            if not unified.style_phase.is_style_locked:
                logger.warning("[UnifiedFeedback] Style not selected, auto-selecting first.")
                self.apply_style_choice(unified.style_phase, 0)

            unified.overall_state = PhaseState.APPROVED

            # 确保 enhanced_context 包含最新的 framework 状态
            if unified.framework_result:
                unified.enhanced_context = self._build_unified_context(
                    unified.user_input, unified.style_phase, unified.framework_result
                )

            logger.info(
                f"[UnifiedFeedback] APPROVED: style={unified.style_phase.chosen_style} | "
                f"chapters={unified.framework_result.chapter_count if unified.framework_result else '?'}"
            )
            return unified

        # 默认：不做修改
        return unified

    # ── 快捷方法 ─────────────────────────────────────────

    def build_full_preview(
        self,
        user_input: Dict[str, Any],
        orchestration_output: Dict[str, Any],
        material_scout_output: Dict[str, Any],
        default_style: str = "narrative_casual",
    ) -> UnifiedPreviewResult:
        """
        一次性完成 Phase 1 + Phase 2（跳过用户交互，用于 CLI 测试或 batch 模式）。

        参数：
            default_style: 风格尝味时默认选中的风格（CLI 测试用）
        """
        # Phase 1
        style_phase = self.build_style_preview(user_input)
        self.apply_style_choice(style_phase, default_style)

        # Phase 2
        unified = self.build_framework_preview(
            user_input=user_input,
            style_phase=style_phase,
            orchestration_output=orchestration_output,
            material_scout_output=material_scout_output,
        )
        return unified


# ── CLI 快速测试 ─────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Mock 输入
    mock_orchestration = {
        "cog": {
            "name": "cog_from_input",
            "nodes": ["input_parse", "intent_classify", "candidates"],
            "edges": [],
            "intent": "epic",
            "tension_arc": "rising_climax",
        }
    }
    mock_materials = {
        "candidate_materials": [
            {"name": "安史之乱", "type": "event"},
            {"name": "颜真卿守平原郡", "type": "event"},
            {"name": "颜杲卿守常山郡", "type": "event"},
            {"name": "颜真卿", "type": "figure"},
            {"name": "安禄山", "type": "figure"},
            {"name": "玄宗", "type": "figure"},
        ]
    }
    mock_user_input = {
        "chapter_title": "乾元元年·蒲州的墨与血",
        "style": "narrative_casual",
        "characters": ["颜真卿", "安禄山"],
        "themes": ["忠义", "家国", "书法"],
        "target_length": 2000,
    }

    composer = UnifiedPreviewComposer()

    # ── Phase 1: 风格尝味 ────────────────────────────────
    print("\n" + "=" * 60)
    print("  Phase 1: 风格尝味")
    print("=" * 60)
    style_phase = composer.build_style_preview(mock_user_input)
    sp = style_phase.raw_result
    for i, s in enumerate(sp.samples):
        is_sel = "[选择]" if i == 0 else "      "
        print(f"\n{is_sel}[{i+1}] {s.label} ({s.style})")
        print(f"       {s.description}")
        print(f"       {s.content[:100]}……")

    # CLI 测试：默认选第一种风格
    composer.apply_style_choice(style_phase, 0)
    print(f"\n✅ 风格已锁定：{style_phase.chosen_style}")

    # ── Phase 2: 框架预览 ────────────────────────────────
    print("\n" + "=" * 60)
    print("  Phase 2: 框架预览")
    print("=" * 60)
    unified = composer.build_framework_preview(
        user_input=mock_user_input,
        style_phase=style_phase,
        orchestration_output=mock_orchestration,
        material_scout_output=mock_materials,
    )

    # ── 统一界面渲染 ─────────────────────────────────────
    ui = composer.to_unified_user_facing(unified)

    print(f"\n📖 {ui['page']['title']}")
    print(f"   {ui['page']['subtitle']}")
    print(f"\n{'─' * 50}")
    print(f"【风格】{ui['style_section']['status']}")
    print(f"{'─' * 50}")
    for s in ui["style_section"]["samples"]:
        sel = "✓" if s["is_selected"] else " "
        print(f"  {sel} {s['label']}: {s['content'][:80]}…")

    print(f"\n{'─' * 50}")
    print(f"【章节】{ui['framework_section']['status']} | 张力弧: {ui['framework_section']['tension_arc_label']}")
    print(f"{'─' * 50}")
    for ch in ui["framework_section"]["chapters"]:
        emoji = ch["tension"]["emoji"]
        print(f"  {emoji} 第{ch['number']}章｜{ch['title']}")
        print(f"      └ {ch['subtitle']} [张力:{ch['tension']['level']:.0%} {ch['tension']['label']}]")
        if ch["key_events"]:
            print(f"      └ 事件：{' / '.join(ch['key_events'])}")
        if ch["key_figures"]:
            print(f"      └ 人物：{' / '.join(ch['key_figures'])}")

    print(f"\n{'─' * 50}")
    print(f"【取材】")
    print(f"{'─' * 50}")
    ms = ui["materials_section"]
    print(f"  事件 {ms.get('total_events', 0)} 个：{' / '.join(ms.get('events', [])[:5])}")
    print(f"  人物 {ms.get('total_figures', 0)} 个：{' / '.join(ms.get('figures', [])[:4])}")

    print(f"\n{'─' * 50}")
    print(f"【张力曲线】{ui['tension_chart']['data']}")
    print(f"{'─' * 50}")
    chart = ui["tension_chart"]["data"]
    max_bar = 30
    for i, v in enumerate(chart):
        bar_len = int(v * max_bar)
        bar = "█" * bar_len + "░" * (max_bar - bar_len)
        print(f"  第{i+1}章 [{bar}] {v:.0%}")

    print(f"\n{'─' * 50}")
    print(f"【操作选项】")
    print(f"{'─' * 50}")
    for opt in ui["approval_options"]:
        en = "✅" if opt["enabled"] else "🔒"
        print(f"  {en} {opt['label']}: {opt['description']}")

    print(f"\n{'=' * 60}")
    print(f"  状态：{unified.overall_state.value} | {unified.summary_text()}")
    print(f"{'=' * 60}")

    # ── 模拟用户确认 ──────────────────────────────────────
    print("\n>>> 模拟用户执行: full_approve")
    feedback = {"action": "full_approve"}
    unified = composer.apply_unified_feedback(unified, feedback)
    print(f"最终状态: {unified.overall_state.value}")
    print(f"增强 context keys: {list(unified.enhanced_context.keys())}")
