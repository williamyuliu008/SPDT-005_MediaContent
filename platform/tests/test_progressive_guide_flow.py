"""
test_progressive_guide_flow.py
==============================
PT-047 渐进式引导模块完整流程测试�?
模拟真实用户意图 �?ChiefEditor解析 �?Orchestration编排 �?MaterialScout取材 �?UnifiedPreviewComposer统一预览 �?用户确认 �?进入pipeline

运行方式:
    cd D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent
    $env:DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
    python test_progressive_guide_flow.py
"""
import sys, os, logging, json, time
from pathlib import Path

# ── 路径设置 ─────────────────────────────────────────────
_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ProgressiveFlow")

# ── LLM client ────────────────────────────────────────────
os.environ.setdefault("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")

def get_llm():
    from shared.tools.llm_clients import get_llm_client
    return get_llm_client()

# ── 用户输入（模拟真实用户提交）────────────────────────────
USER_INPUT = {
    "chapter_title": "乾元元年·蒲州的墨与血",
    "description": (
        "以颜真卿在安史之乱中的经历为主线，写一个关于忠义与家国的小故事�?
        "颜真卿是唐代著名书法家，也是忠臣。安史之乱爆发时，他在平原郡担任太守�?
        "他的堂兄颜杲卿在常山郡抵抗叛军，最终壮烈牺牲。颜真卿听闻噩耗后�?
        "写下了被誉为'天下第二行书'的《祭侄文稿》，寄托了深深的悲愤与哀思�?
    ),
    "style": "narrative_casual",
    "characters": ["颜真�?, "颜杲�?, "安禄�?, "玄宗"],
    "themes": ["忠义", "家国", "书法艺术"],
    "target_length": 3000,
    "genre": "历史人物故事",
}


# ════════════════════════════════════════════════════════════
# 阶段 0：意图解析（ChiefEditor�?# ════════════════════════════════════════════════════════════
def run_chief_editor(user_input: dict, llm) -> dict:
    """ChiefEditor 解析用户意图，生�?tension_curve + 初步 funnel�?""
    logger.info("[Stage 0] ChiefEditor 意图解析")
    t0 = time.time()

    try:
        from agents.chief_editor.agent import ChiefEditorAgent
        agent = ChiefEditorAgent()
        result = agent.execute({"content": user_input.get("description", ""), "metadata": user_input})
        elapsed = time.time() - t0
        logger.info(f"[Stage 0] 完成，耗时 {elapsed:.1f}s")
        return result
    except Exception as e:
        logger.error(f"[Stage 0] ChiefEditor failed: {e}")
        # Fallback：手动构�?tension curve
        return {
            "status": "ok",
            "agent": "chief_editor",
            "tension_curve": {
                "initial": 0.1, "development": 0.3, "climax": 0.95, "resolution": 0.5
            },
            "intent_type": "epic",
            "style_preference": "narrative_casual",
        }


# ════════════════════════════════════════════════════════════
# 阶段 0.5：编排（Orchestration�?# ════════════════════════════════════════════════════════════
def run_orchestration(user_input: dict, chief_result: dict, llm) -> dict:
    """Orchestration 基于意图生成 COG 计算图�?""
    logger.info("[Stage 0.5] Orchestration 编排")
    t0 = time.time()

    try:
        from agents.orchestration.orchestration import OrchestrationAgent
        agent = OrchestrationAgent()
        # Orchestration 需�?(user_input, tension_curve)
        combined = {
            "user_input": user_input,
            "tension_curve": chief_result.get("tension_curve", {}),
        }
        result = agent.execute(combined)
        elapsed = time.time() - t0
        logger.info(f"[Stage 0.5] 完成，耗时 {elapsed:.1f}s")
        # result 可能是字符串（CLI formatter 包装）或 dict
        if isinstance(result, str):
            # 尝试解析 JSON
            try:
                import json as _json
                start = result.find("{")
                if start >= 0:
                    parsed = _json.loads(result[start:])
                    return parsed
            except Exception:
                pass
            return {"status": "ok", "agent": "orchestration", "cog": {}}
        return result
    except Exception as e:
        logger.error(f"[Stage 0.5] Orchestration failed: {e}")
        return {
            "status": "ok",
            "agent": "orchestration",
            "cog": {
                "name": "fallback_cog",
                "nodes": ["intent_parse", "topic_expand", "structure_plan"],
                "edges": [],
                "intent": "epic",
                "tension_arc": "rising_climax",
            },
            "intent_type": "epic",
        }


# ════════════════════════════════════════════════════════════
# 阶段 0.6：取材（MaterialScout�?# ════════════════════════════════════════════════════════════
def run_material_scout(user_input: dict, orchestration_result: dict, llm) -> dict:
    """MaterialScout 基于 COG 采集相关历史素材�?""
    import asyncio
    logger.info("[Stage 0.6] MaterialScout 取材")
    t0 = time.time()

    try:
        from agents.material_scout.material_scout import MaterialScoutAgent, MaterialScoutInput
        agent = MaterialScoutAgent()
        # 构建查询字符�?        query = f"{user_input.get('chapter_title', '')} {user_input.get('description', '')}"
        msi = MaterialScoutInput(
            query=query,
            domain="中国历史·唐史"
        )
        # execute �?async，需�?asyncio.run()
        raw_output = asyncio.run(agent.execute(msi))
        elapsed = time.time() - t0
        logger.info(f"[Stage 0.6] 完成，耗时 {elapsed:.1f}s")
        # 转换�?dict 格式
        return {
            "status": "ok",
            "agent": "material_scout",
            "candidate_materials": raw_output.candidate_materials,
            "tension_curve": raw_output.tension_curve,
        }
    except Exception as e:
        logger.error(f"[Stage 0.6] MaterialScout failed: {e}")
        return {
            "status": "ok",
            "agent": "material_scout",
            "candidate_materials": [
                {"name": "安史之乱", "type": "event", "description": "755-763年唐朝大动乱"},
                {"name": "颜真卿守平原�?, "type": "event", "description": "颜真卿在平原郡抵抗安禄山叛军"},
                {"name": "颜杲卿守常山�?, "type": "event", "description": "颜杲卿在常山郡抵抗，城破被俘后骂贼而死"},
                {"name": "《祭侄文稿�?, "type": "event", "description": "颜真卿为悼念侄子颜季明所书的行书法帖"},
                {"name": "颜真�?, "type": "figure", "description": "唐代书法家，官至太子太师，封鲁郡�?},
                {"name": "颜杲�?, "type": "figure", "description": "颜真卿堂兄，常山太守，安史之乱中殉国"},
                {"name": "安禄�?, "type": "figure", "description": "胡人将领，兼任三镇节度使，发动安史之�?},
                {"name": "玄宗", "type": "figure", "description": "唐玄宗，安史之乱中逃往蜀�?},
            ],
        }


# ════════════════════════════════════════════════════════════
# 阶段 P：UnifiedPreviewComposer 统一预览（Phase 1 + Phase 2�?# ════════════════════════════════════════════════════════════
def run_unified_preview(
    user_input: dict,
    style_phase,
    orchestration_result: dict,
    material_result: dict,
    composer,
) -> tuple:
    """UnifiedPreviewComposer：Phase 1(已完�? + Phase 2 �?unified_result"""
    logger.info("[Stage P] UnifiedPreviewComposer Phase 2")
    t0 = time.time()

    unified = composer.build_framework_preview(
        user_input=user_input,
        style_phase=style_phase,
        orchestration_output=orchestration_result,
        material_scout_output=material_result,
    )
    elapsed = time.time() - t0
    logger.info(f"[Stage P] Phase 2 完成，耗时 {elapsed:.1f}s")
    return unified


# ════════════════════════════════════════════════════════════
# CLI 渲染：精美输�?# ════════════════════════════════════════════════════════════
def render_cli_preview(ui: dict):
    """�?unified to_user_facing 结果渲染为精�?CLI 界面�?""
    tension_emoji = {
        "开篇引�?: "🌒", "矛盾积累": "🌓", "高潮时刻": "🌕",
        "回落收束": "🌗", "结局": "🌑", "平稳叙述": "🌙",
        "发展展开": "🌔", "高潮与衰�?: "�?, "上升至高�?: "🔥",
    }

    p = ui["page"]
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print(f"�? 📖 {p['title']}")
    print(f"�?    {p['subtitle']}")
    print("╠══════════════════════════════════════════════════════╣")

    # ── 风格区块 ─────────────────────────────────────────
    ss = ui["style_section"]
    print(f"�? {ss['title']}  {ss['subtitle']}")
    print(f"�? 状态：{ss['status']}")
    print("�? ─────────────────────────────────────────────────")
    for s in ss["samples"]:
        sel = "  �?" if s["is_selected"] else "    "
        label = f"[{s['label']}]"
        # 截取�?20字显�?        snippet = s["content"][:120].replace("\n", " ")
        print(f"�? {sel}{label}  {snippet}�?)

    print("╠══════════════════════════════════════════════════════╣")

    # ── 章节区块 ─────────────────────────────────────────
    fs = ui["framework_section"]
    print(f"�? {fs['title']}  {fs['subtitle']}")
    print(f"�? 状态：{fs['status']}  |  张力�? {fs['tension_arc_label']}")
    print("�? ─────────────────────────────────────────────────")
    for ch in fs["chapters"]:
        emoji = tension_emoji.get(ch["tension"]["label"], "📖")
        print(f"�?   {emoji} 第{ch['number']}章｜{ch['title']}")
        print(f"�?       �?{ch['subtitle']}  [张力:{ch['tension']['level']:.0%} {ch['tension']['label']}]")
        if ch["key_events"]:
            print(f"�?       �?事件：{' / '.join(ch['key_events'][:2])}")
        if ch["key_figures"]:
            print(f"�?       �?人物：{' / '.join(ch['key_figures'][:2])}")

    print("╠══════════════════════════════════════════════════════╣")

    # ── 取材区块 ─────────────────────────────────────────
    ms = ui["materials_section"]
    evts = ms.get("events", [])
    figs = ms.get("figures", [])
    print(f"�? �?关键取材")
    print(f"�? ─────────────────────────────────────────────────")
    print(f"�?   事件({ms.get('total_events', len(evts))}�?：{' / '.join(evts[:4])}")
    print(f"�?   人物({ms.get('total_figures', len(figs))}�?：{' / '.join(figs[:4])}")

    # ── 张力曲线 ─────────────────────────────────────────
    chart = ui["tension_chart"]
    print("╠══════════════════════════════════════════════════════╣")
    print(f"�? �?全局张力曲线")
    max_bar = 35
    for i, v in enumerate(chart["data"]):
        bar_len = int(v * max_bar)
        bar = "�? * bar_len + "�? * (max_bar - bar_len)
        print(f"�?   第{i+1}�?[{bar}] {v:.0%}")

    print("╠══════════════════════════════════════════════════════╣")
    print("�? �?确认选项")
    print("�? ─────────────────────────────────────────────────")
    for opt in ui["approval_options"]:
        en = "�? if opt["enabled"] else "  "
        action = opt["action"].replace("_", " ")
        print(f"�?   {en} [{action:20s}] {opt['description']}")

    print("╠══════════════════════════════════════════════════════╣")
    hint_key = (
        "ready_to_generate"
        if (ui["style_section"]["is_locked"] and ui["framework_section"]["is_ready"])
        else "style_not_selected"
    )
    hint = ui["hints"].get(hint_key, "")
    print(f"�? 💡 {hint}")
    print("╚══════════════════════════════════════════════════════╝")
    print()


# ════════════════════════════════════════════════════════════
# 主流�?# ════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  PT-047 渐进式引导完整流程测�?)
    print("  社科智能体创作平�?· Progressive Guide Trial Run")
    print("=" * 60)
    print()
    print(f"【用户意图】{USER_INPUT['chapter_title']}")
    print(f"  描述：{USER_INPUT['description'][:80]}�?)
    print(f"  人物：{' / '.join(USER_INPUT['characters'])}")
    print(f"  主题：{' / '.join(USER_INPUT['themes'])}")
    print(f"  目标字数：{USER_INPUT['target_length']}")
    print()

    llm = get_llm()

    # ── Stage 0: ChiefEditor ──────────────────────────────
    t_total = time.time()
    chief_result_raw = run_chief_editor(USER_INPUT, llm)
    # 统一转为 dict（可能是 Pydantic 模型�?    if hasattr(chief_result_raw, "model_dump"):
        chief_result = chief_result_raw.model_dump()
    elif hasattr(chief_result_raw, "__dict__"):
        chief_result = dict(chief_result_raw.__dict__)
    else:
        chief_result = dict(chief_result_raw)
    print()
    print(f"  ChiefEditor output: funnel={chief_result.get('funnel_stage', '?')} | tension={chief_result.get('tension_score', '?')}")
    print()

    # ── Stage 0.5: Orchestration ─────────────────────────
    orch_result = run_orchestration(USER_INPUT, chief_result, llm)
    cog = orch_result.get("cog", {})
    print()
    print(f"  Orchestration COG nodes = {cog.get('nodes', [])}")
    print(f"  intent = {cog.get('intent', '?')}, arc = {cog.get('tension_arc', '?')}")
    print()

    # ── Stage 0.6: MaterialScout ────────────────────────
    material_result = run_material_scout(USER_INPUT, orch_result, llm)
    mats = material_result.get("candidate_materials", material_result.get("materials", []))
    print()
    print(f"  MaterialScout 取材数量：{len(mats)}")
    mat_names = [m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in mats]
    print(f"  素材：{' | '.join(mat_names[:6])}")
    print()

    # ════════════════════════════════════════════════════
    # 渐进式引导：UnifiedPreviewComposer
    # ════════════════════════════════════════════════════
    print("�? * 60)
    print("  渐进式引导阶段开�?)
    print("�? * 60)

    from progressive_guide import UnifiedPreviewComposer

    composer = UnifiedPreviewComposer(llm_client=llm)

    # ── Phase 1: 风格尝味 ────────────────────────────────
    print()
    print("─── Phase 1: 风格尝味 ───────────────────────────────")
    print("  生成 3 种风格微样章，让用户感受不同讲法�?)
    t_p1 = time.time()
    style_phase = composer.build_style_preview(USER_INPUT)
    elapsed_p1 = time.time() - t_p1

    sp = style_phase.raw_result
    print(f"  耗时 {elapsed_p1:.1f}s | 缓存命中: {sp.cache_hit}")
    print()
    for i, s in enumerate(sp.samples):
        is_sel = "�?" if i == 0 else "  "
        print(f"  {is_sel}[{i+1}] {s.label} ({s.style})")
        snippet = s.content[:100].replace("\n", " ")
        print(f"      {snippet}�?)
    print()

    # CLI 演示：自动选第一种（真实场景由用户点选）
    print("  用户行为：点击选择�?[1] 通俗故事�?)
    composer.apply_style_choice(style_phase, 0)
    print(f"  �?风格已锁�?�?{style_phase.chosen_style} ({style_phase.selected_sample.label})")
    print()

    # ── Phase 2: 框架预览 ────────────────────────────────
    print()
    print("─── Phase 2: 框架预览 ───────────────────────────────")
    print("  基于 COG + 取材，生成章节结�?+ 取材摘要 + 张力曲线�?)
    t_p2 = time.time()
    unified = run_unified_preview(
        USER_INPUT, style_phase, orch_result, material_result, composer
    )
    elapsed_p2 = time.time() - t_p2

    print(f"  耗时 {elapsed_p2:.1f}s | 章节�? {unified.framework_result.chapter_count}")
    print()

    # ── 统一预览界面渲染 ─────────────────────────────────
    ui = composer.to_unified_user_facing(unified)
    render_cli_preview(ui)

    # ── 模拟用户确认 ─────────────────────────────────────
    print()
    print("─── 模拟用户操作：full_approve ──────────────────────")
    print("  用户点击：[�?全部确认，开始生成]")
    print()
    feedback = {"action": "full_approve"}
    unified = composer.apply_unified_feedback(unified, feedback)

    elapsed_total = time.time() - t_total
    print(f"  最终状态：{unified.overall_state.value}")
    print(f"  增强 context 包含 {len(unified.enhanced_context)} 个键�?)
    for k, v in unified.enhanced_context.items():
        if isinstance(v, list) and len(v) > 3:
            print(f"    �?{k}: [{len(v)} items]")
        elif isinstance(v, dict):
            print(f"    �?{k}: {{{len(v)} keys}}")
        else:
            print(f"    �?{k}: {str(v)[:60]}")
    print()
    print(f"  ── 流程总耗时: {elapsed_total:.1f}s ──────────────────")
    print(f"    Phase 1（风格尝味）: {elapsed_p1:.1f}s")
    print(f"    Phase 2（框架预览）: {elapsed_p2:.1f}s")
    print()
    print("  ── 下一步：unified.enhanced_context 注入 pipeline ──")
    print("  ControlledGeneration 现在拥有关于章节结构、风格指引�?)
    print("  取材范围的完整信息，直接生成章节正文，无需重新推断�?)
    print()
    print("�?渐进式引导流程测试完�?)


if __name__ == "__main__":
    main()
