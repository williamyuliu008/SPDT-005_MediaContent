"""
test_generate_all_chapters.py
=============================
PT-047 三章连续生成测试�?基于 UnifiedPreviewComposer 确认�?enhanced_context�?连续生成�?�?�?章正文，保存为完整书稿�?
运行方式:
    cd D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent
    $env:DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
    python test_generate_all_chapters.py
"""
import sys, os, logging, time
from pathlib import Path

_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("AllChapters")
os.environ.setdefault("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")

from shared.tools.llm_clients import get_llm_client
from progressive_guide import UnifiedPreviewComposer

# ── 固定取材数据（确保历史领域）────────────────────────────
MOCK_MATERIALS = {
    "candidate_materials": [
        {"name": "安史之乱", "type": "event"},
        {"name": "颜真卿守平原�?, "type": "event"},
        {"name": "颜杲卿守常山�?, "type": "event"},
        {"name": "颜季明殉�?, "type": "event"},
        {"name": "马嵬驿兵�?, "type": "event"},
        {"name": "玄宗西逃入蜀", "type": "event"},
        {"name": "《祭侄文稿》写�?, "type": "event"},
        {"name": "颜真�?, "type": "figure"},
        {"name": "颜杲�?, "type": "figure"},
        {"name": "颜季�?, "type": "figure"},
        {"name": "安禄�?, "type": "figure"},
        {"name": "玄宗", "type": "figure"},
        {"name": "杨贵�?, "type": "figure"},
        {"name": "史思明", "type": "figure"},
    ]
}

MOCK_ORCHESTRATION = {
    "cog": {
        "name": "cog_yanzhenqing",
        "nodes": ["intent_parse", "topic_expand", "structure_plan"],
        "edges": [],
        "intent": "epic",
        "tension_arc": "rising_climax",
    }
}

USER_INPUT = {
    "chapter_title": "乾元元年·蒲州的墨与血",
    "description": (
        "以颜真卿在安史之乱中的经历为主线，写一个关于忠义与家国的故事�?
        "颜真卿是唐代书法家、忠臣，在平原郡担任太守时恰逢安史之乱爆发，"
        "其堂兄颜杲卿在常山郡誓死抵抗，城破后颜杲卿父子遭叛军肢解，一门三十余口尽殁�?
        "颜真卿闻讯悲愤，挥泪写下被誉�?天下第二行书'的《祭侄文稿》�?
    ),
    "style": "narrative_casual",
    "characters": ["颜真�?, "颜杲�?, "颜季�?, "安禄�?, "玄宗"],
    "themes": ["忠义", "家国", "书法艺术"],
    "target_length": 3000,
    "genre": "历史人物故事",
}

STYLE_DEFS = {
    "narrative_casual": ("通俗故事�?, "用日常对话和场景描写拉近历史距离，像小说一样有画面�?),
    "academic_summary": ("学术综述�?, "客观陈述，史实为主，兼具深度分析"),
    "novel_drama": ("小说化演�?, "戏剧张力强，人物内心刻画深刻，适合沉浸式阅读体�?),
}


def build_chapter_prompt(
    chapter_info: dict,
    ctx: dict,
    prev_chapter_content: str = "",
) -> str:
    """为指定章节构建完整生�?Prompt�?""
    ch_num = chapter_info["chapter"]
    style_key = ctx["style"]
    style_label, style_desc = STYLE_DEFS.get(style_key, STYLE_DEFS["narrative_casual"])

    events_str = "�?.join(ctx["materials"].get("events", [])[:8])
    figures_str = "�?.join(ctx["materials"].get("figures", [])[:8])

    # ── 前情提要（续写章节需要） ────────────────────────
    recap = ""
    if prev_chapter_content and ch_num > 1:
        recap = f"\n【前情提要（第{ch_num-1}章概要）】\n{prev_chapter_content[:300]}……\n"

    # ── 章节特定指引 ────────────────────────────────────
    if ch_num == 1:
        tension_directive = (
            "本章为开篇，节奏宜缓，通过日常场景和人物对话建立时代氛围，"
            "在末尾引入冲突预兆（如范阳来信），为后续章节蓄力�?
        )
    elif ch_num == 2:
        tension_directive = (
            "本章为冲突升级章。张力目�?80%�?
            "颜杲卿守常山、城破被俘是核心事件，需要正面描写战争场景和人物的抉择时刻�?
            "要有具体的战斗描写和人物对话，不能回避悲剧，但保持叙述的克制与尊严�?
        )
    else:  # ch_num == 3
        tension_directive = (
            "本章为高潮与收束章。张力目�?100%�?
            "核心是颜真卿挥泪写《祭侄文稿》的场景——悲愤化为笔墨�?
            "情感要有爆发力，同时要有历史纵深感�?
            "结尾要有余韵，留给读者对忠义、家国、书法三重主题的回味空间�?
        )

    prompt = f"""你是一位历史通俗作品作家。请根据以下创作规范，写�?*第{ch_num}�?*的完整正文�?
【书名】《{ctx["theme"]}�?【风格】{style_label} �?{style_desc}
【全章张力弧】{ctx.get("tension_arc_description", "导入→冲突升级→高潮收束")}
{recap}
【本章信息�?- 章节序号：第{ch_num}�?- 章节标题：{chapter_info["title"]}
- 章节副标题：{chapter_info["subtitle"]}
- 本章张力目标：{chapter_info["tension"]:.0%}（{chapter_info.get("tension_label", "发展�?)}�?- 本章预估字数：{chapter_info.get("estimated_chars", 800)} �?
【可用素材�?- 历史事件：{events_str}
- 主要人物：{figures_str}

【章节特定指引�?{tension_directive}

【质量要求�?- 字数：约 {chapter_info.get("estimated_chars", 800)} 字（允许上下浮动 20%�?- 人物对话要符合唐代人物身份，不要用现代白�?- 要有具体的场景和细节，拒绝空泛叙�?- 忠实于历史事实，不要虚构关键事件
- 直接输出章节正文，不要加标题前缀或说明文�?""

    return prompt


def generate_chapter(
    chapter_info: dict,
    ctx: dict,
    prev_content: str,
    gen_agent,
    llm,
    chapter_num: int,
) -> str:
    """生成单个章节并返回正文�?""
    style_label = ctx.get("style_label", "通俗故事�?)
    target_chars = chapter_info.get("estimated_chars", 800)

    print(f"\n  生成中�?", end="", flush=True)
    t0 = time.time()

    prompt = build_chapter_prompt(chapter_info, ctx, prev_content)

    # 使用 LLM 直接生成（比 agent wrapper 更可靠）
    resp = llm.chat(prompt, temperature=0.75, max_tokens=2048)
    content = resp.content.strip() if hasattr(resp, "content") else str(resp)

    elapsed = time.time() - t0
    print(f"�?{len(content)}�?/ {elapsed:.1f}s")

    return content


# ════════════════════════════════════════════════════════════
# 主流�?# ════════════════════════════════════════════════════════════
def main():
    t_total = time.time()
    llm = get_llm_client()

    print("=" * 60)
    print("  PT-047 三章连续生成")
    print("  《乾元元年·蒲州的墨与血》完整书�?)
    print("=" * 60)
    print(f"\n风格：narrative_casual | 总目标字数：�?2400 �?)

    # ── Step 1: UnifiedPreviewComposer 确认框架 ─────────
    print("\n─── 框架确认（UnifiedPreviewComposer）───")
    composer = UnifiedPreviewComposer(llm_client=llm)

    style_phase = composer.build_style_preview(USER_INPUT)
    composer.apply_style_choice(style_phase, 0)

    unified = composer.build_framework_preview(
        user_input=USER_INPUT,
        style_phase=style_phase,
        orchestration_output=MOCK_ORCHESTRATION,
        material_scout_output=MOCK_MATERIALS,
    )
    unified = composer.apply_unified_feedback(unified, {"action": "full_approve"})
    ctx = unified.enhanced_context

    chapters = ctx["chapter_outline"]
    style_label = ctx["style_label"]
    print(f"  �?框架确认完毕 | {len(chapters)}�?| 风格：{style_label}")
    for ch in chapters:
        print(f"     第{ch['chapter']}章「{ch['title']}」{ch['tension']:.0%} {ch.get('tension_label', '')}")

    # ── Step 2: 逐章生成 ────────────────────────────────
    print("\n─── 章节生成 ────────────────────────────────")

    from agents.generation.controlled_generation import ControlledGenerationAgent
    gen_agent = ControlledGenerationAgent()

    chapter_contents: list[dict] = []
    all_text = ""
    prev_content = ""

    for i, ch in enumerate(chapters):
        ch_num = ch["chapter"]

        print(f"\n  ══ 第{ch_num}章「{ch['title']}」═�?)
        print(f"     副标题：{ch['subtitle']}")
        print(f"     张力目标：{ch['tension']:.0%}（{ch.get('tension_label', '')}�?)
        print(f"     预估字数：约 {ch.get('estimated_chars', 800)} �?)

        content = generate_chapter(
            chapter_info=ch,
            ctx=ctx,
            prev_content=prev_content,
            gen_agent=gen_agent,
            llm=llm,
            chapter_num=ch_num,
        )

        chapter_contents.append({
            "chapter": ch_num,
            "title": ch["title"],
            "subtitle": ch["subtitle"],
            "tension": ch["tension"],
            "tension_label": ch.get("tension_label", ""),
            "content": content,
            "char_count": len(content),
        })

        prev_content += f"\n\n{content}\n\n"

    elapsed_total = time.time() - t_total

    # ── Step 3: 渲染完整书稿 ────────────────────────────
    print()
    print("=" * 60)
    print("  《乾元元年·蒲州的墨与血》完整书�?)
    print("=" * 60)
    print()
    print(f"# {ctx['theme']}")
    print(f"\n**风格**：{style_label}  |  **章节�?*：{len(chapters)}�? |  **取材**：{events_str if (events_str := '�?.join(ctx['materials'].get('events', [])[:6])) else '见各�?}\n")
    print(f"---\n")

    for ch_data in chapter_contents:
        print()
        print(f"## 第{ch_data['chapter']}章「{ch_data['title']}�?)
        print(f"\n*{ch_data['subtitle']}*")
        print()
        print(ch_data["content"])
        print()
        print(f"*字数：约 {ch_data['char_count']} �?| 张力：{ch_data['tension']:.0%}（{ch_data['tension_label']}�?")
        print()
        print("---")
        print()

    print()
    print("=" * 60)
    total_chars = sum(c["char_count"] for c in chapter_contents)
    print(f"  书稿统计")
    print(f"  总字数：�?{total_chars} �?)
    print(f"  总耗时：{elapsed_total:.1f}s")
    for ch_data in chapter_contents:
        print(f"    第{ch_data['chapter']}章「{ch_data['title']}」：{ch_data['char_count']}�?)
    print("=" * 60)

    # ── Step 4: 保存完整书稿 ────────────────────────────
    output_path = _ROOT / "generated_full_book.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {ctx['theme']}\n\n")
        f.write(f"**风格**：{style_label}\n")
        f.write(f"**章节�?*：{len(chapters)}章\n")
        f.write(f"**取材**：{events_str}\n\n")
        f.write(f"---\n\n")

        for ch_data in chapter_contents:
            f.write(f"## 第{ch_data['chapter']}章「{ch_data['title']}」\n\n")
            f.write(f"*{ch_data['subtitle']}*\n\n")
            f.write(ch_data["content"])
            f.write(f"\n\n*字数：约 {ch_data['char_count']} �?| 张力：{ch_data['tension']:.0%}（{ch_data['tension_label']}�?\n\n")
            f.write("---\n\n")

        f.write(f"\n*全稿字数：约 {total_chars} �?\n")
        f.write(f"*生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
        f.write(f"*�?PT-047 社科智能体创作平台生�?\n")

    print(f"\n�?完整书稿已保存至：{output_path}")
    print("�?三章连续生成完毕")


if __name__ == "__main__":
    main()
