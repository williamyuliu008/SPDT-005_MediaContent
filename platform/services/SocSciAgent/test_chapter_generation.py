"""
test_chapter_generation.py
==========================
PT-047 章节生成测试：使�?UnifiedPreviewComposer 确认�?enhanced_context�?驱动 ControlledGenerationAgent 生成�?章正文�?
运行方式:
    cd D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent
    $env:DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
    python test_chapter_generation.py
"""
import sys, os, logging
from pathlib import Path

_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("ChapterGen")

os.environ.setdefault("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")

# ─────────────────────────────────────────────────────────
# Step 1: 准备 unified enhanced_context
# ─────────────────────────────────────────────────────────
from progressive_guide import UnifiedPreviewComposer

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
        {"name": "颜真卿守平原�?, "type": "event"},
        {"name": "颜杲卿守常山�?, "type": "event"},
        {"name": "《祭侄文稿�?, "type": "event"},
        {"name": "颜真�?, "type": "figure"},
        {"name": "颜杲�?, "type": "figure"},
        {"name": "颜季�?, "type": "figure"},
        {"name": "安禄�?, "type": "figure"},
        {"name": "玄宗", "type": "figure"},
    ]
}

USER_INPUT = {
    "chapter_title": "乾元元年·蒲州的墨与血",
    "description": (
        "以颜真卿在安史之乱中的经历为主线，写一个关于忠义与家国的小故事�?
        "颜真卿是唐代著名书法家，也是忠臣。他的堂兄颜杲卿在常山郡抵抗叛军，最终壮烈牺牲�?
        "颜真卿听闻噩耗后，写下了被誉�?天下第二行书'的《祭侄文稿》，寄托了深深的悲愤与哀思�?
    ),
    "style": "narrative_casual",
    "characters": ["颜真�?, "颜杲�?, "颜季�?, "安禄�?],
    "themes": ["忠义", "家国", "书法艺术"],
    "target_length": 3000,
    "genre": "历史人物故事",
}

# ─────────────────────────────────────────────────────────
# Step 2: 构建 unified preview（跳�?Phase 1，CLI 默认选第1种风格）
# ─────────────────────────────────────────────────────────
from shared.tools.llm_clients import get_llm_client

llm = get_llm_client()
composer = UnifiedPreviewComposer(llm_client=llm)

print("=" * 60)
print("  PT-047 章节生成测试")
print("  基于 UnifiedPreview 确认的框架生成第1章正�?)
print("=" * 60)

# Phase 1: 风格尝味
style_phase = composer.build_style_preview(USER_INPUT)
composer.apply_style_choice(style_phase, 0)   # 默认选第1种：通俗故事�?
# Phase 2: 框架预览
unified = composer.build_framework_preview(
    user_input=USER_INPUT,
    style_phase=style_phase,
    orchestration_output=mock_orchestration,
    material_scout_output=mock_materials,
)
unified = composer.apply_unified_feedback(unified, {"action": "full_approve"})

ctx = unified.enhanced_context
print(f"\n�?框架确认完毕")
print(f"   风格：{ctx['style_label']} | 章节数：{ctx['chapter_count']}")
print(f"   章节：{[ch['title'] for ch in ctx['chapter_outline']]}")
print()

# ─────────────────────────────────────────────────────────
# Step 3: �?enhanced_context 构建章节生成 Prompt
# ─────────────────────────────────────────────────────────
chapter_to_generate = ctx["chapter_outline"][0]   # �?章：墨痕初染
style_def = {
    "narrative_casual": "通俗故事�?,
    "academic_summary": "学术综述�?,
    "novel_drama": "小说化演�?,
}
style_label = ctx.get("style_label", style_def.get(ctx["style"], "通俗故事�?))

events_str = "�?.join(ctx["materials"].get("events", [])[:6])
figures_str = "�?.join(ctx["materials"].get("figures", [])[:6])

generation_prompt = f"""你是一位历史通俗作品作家。请根据以下创作规范，写�?*第一�?*的完整正文�?
【作品信息�?- 书名：《{ctx["theme"]}�?- 风格：{style_label}
- 章节：第{chapter_to_generate["chapter"]}�?- 章节标题：{chapter_to_generate["title"]}
- 章节副标题：{chapter_to_generate["subtitle"]}
- 本章张力目标：{chapter_to_generate["tension"]:.0%}（{chapter_to_generate.get("tension_label", "开篇引�?)}�?
【可用素材�?- 历史事件：{events_str}
- 主要人物：{figures_str}

【风格指引�?{ctx.get("style_guidance", '用日常对话和场景描写拉近历史距离，像小说一样有画面�?)}

【质量要求�?- 字数：约 {chapter_to_generate.get("estimated_chars", 800)} �?- 人物对话要符合唐代人物身�?- 要有具体的场景和细节，不要空泛叙�?- 张力随章节推进逐渐建立
- 开头要有画面感，能吸引读�?- 直接输出章节正文，不要加标题前缀或说明文�?"""

print(f"📝 生成章节：第{chapter_to_generate['chapter']}章「{chapter_to_generate['title']}�?)
print(f"   风格：{style_label} | 目标字数：约 {chapter_to_generate.get('estimated_chars', 800)} �?)
print()
print("─" * 60)

# ─────────────────────────────────────────────────────────
# Step 4: 调用 ControlledGenerationAgent
# ─────────────────────────────────────────────────────────
import time

t0 = time.time()
try:
    from agents.generation.controlled_generation import ControlledGenerationAgent

    gen_agent = ControlledGenerationAgent()

    # 构�?GenerationRequest
    from agents.generation.controlled_generation import GenerationRequest
    req = GenerationRequest(
        prompt=generation_prompt,
        constraints={
            "style": ctx["style"],
            "max_length": chapter_to_generate.get("estimated_chars", 800) * 2,
        },
        temperature=0.75,
        max_tokens=2048,
    )

    result = gen_agent.process(req)
    elapsed = time.time() - t0

    print()
    print("=" * 60)
    print(f"  第{chapter_to_generate['chapter']}章「{chapter_to_generate['title']}�?)
    print(f"  {chapter_to_generate['subtitle']}")
    print("=" * 60)
    print()
    print(result.generated_text)
    print()
    print("=" * 60)
    print(f"  字数：约 {len(result.generated_text)} �?)
    print(f"  生成耗时：{elapsed:.1f}s")
    print(f"  张力曲线段数：{len(result.tension_curve)}")
    print(f"  审核日志条目：{len(result.audit_log)}")
    print("=" * 60)

    # ── 附加：保存到文件 ─────────────────────────────────
    output_path = _ROOT / "generated_chapter_1.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {chapter_to_generate['title']}\n\n")
        f.write(f"**副标�?*：{chapter_to_generate['subtitle']}\n\n")
        f.write(f"**书名**：《{ctx['theme']}》\n")
        f.write(f"**风格**：{style_label}\n")
        f.write(f"**张力**：{chapter_to_generate['tension']:.0%}（{chapter_to_generate.get('tension_label', '开篇引�?)}）\n\n")
        f.write("---\n\n")
        f.write(result.generated_text)
        f.write(f"\n\n---\n")
        f.write(f"*字数：约 {len(result.generated_text)} �?\n")
        f.write(f"*生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
    print(f"\n�?章节已保存至：{output_path}")

except Exception as e:
    import traceback
    elapsed = time.time() - t0
    print(f"\n�?ControlledGenerationAgent 调用失败（耗时 {elapsed:.1f}s）：")
    traceback.print_exc()
