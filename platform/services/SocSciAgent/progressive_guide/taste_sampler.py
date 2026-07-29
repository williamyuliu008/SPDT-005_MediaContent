"""
progressive_guide.taste_sampler — 尝味采样器
在用户进入正式 pipeline 前，用极低成本生成 3 种风格的微样章，
让用户"先尝一口"，锁定风格偏好后再继续。
"""
from __future__ import annotations
import hashlib, json, logging, os, sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── 确保 shared.tools 可导入 ─────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

logger = logging.getLogger("TastingSampler")

# ── 风格定义 ────────────────────────────────────────────
STYLE_DEFINITIONS = {
    "narrative_casual": {
        "label": "通俗故事化",
        "description": "用日常对话和场景描写拉近历史距离，像小说一样有画面感",
        "examples": ["天宝年间，长安东市胡商云集……", "城门刚开，一骑快马冲入……"],
    },
    "academic_summary": {
        "label": "学术综述风",
        "description": "客观陈述，史实为主，兼具深度分析，适合想了解历史脉络的读者",
        "examples": ["唐代天宝年间(742-756)，安禄山以三镇节度使身份……", "天宝十四载十一月丙寅，安禄山反于范阳……"],
    },
    "novel_drama": {
        "label": "小说化演义",
        "description": "戏剧张力强，人物内心刻画深刻，适合沉浸式阅读体验",
        "examples": ["暮色刚染红兴庆宫檐角，一骑快马踏破长街寂静……", "颜真卿放下手中狼毫，望向北方——那是他再也回不去的故土。"],
    },
}

# ── 样章缓存（内存缓存，相同 theme+style 不重复调用 LLM）────
# 注意：缓存 key 仅含 theme+style，主题变化时旧缓存可能返回错误内容。
# 为防止此问题，_topic_version 会在每次主题变更时递增，使旧 key 全部失效。
_sample_cache: Dict[str, Dict[str, str]] = {}
_topic_version: int = 0          # 全局主题版本号，递增使旧缓存失效
_topic_fingerprint: str = "" # 上次缓存的主题指纹，用于检测变化


@dataclass
class TasteSample:
    """单个风格样章。"""
    style: str
    label: str
    description: str
    content: str          # 样章正文，150-300字
    token_estimate: int   # 估算token数
    cache_key: str        # 缓存key
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TastingResult:
    """完整尝味结果，包含3种风格。"""
    theme: str
    characters: List[str]
    themes: List[str]
    samples: List[TasteSample]
    taste_brief: Dict[str, Any]  # 可直接传给 pipeline 的增强 Brief
    cache_hit: bool = False


# ── LLM 调用 ────────────────────────────────────────────
def _get_llm_client():
    """获取 LLM 客户端，优先 DeepSeek。"""
    try:
        from shared.tools.llm_clients import get_llm_client
        return get_llm_client()
    except Exception as e:
        logger.warning(f"LLM client load failed: {e}, using stub")
        return None


def _estimate_tokens(text: str) -> int:
    """中英文混合 token 估算（粗略：中文≈1.5字/token，英文≈0.25词/token）。"""
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    english = len([w for w in text.split() if w.isascii()])
    return int(chinese / 1.5 + english * 0.25)


# ── 单风格样章生成 ───────────────────────────────────────
def _generate_single_sample(
    style: str,
    theme: str,
    characters: List[str],
    themes: List[str],
    llm_client,
) -> TasteSample:
    """生成单个风格的微样章。"""
    style_def = STYLE_DEFINITIONS.get(style, {})
    label = style_def.get("label", style)
    description = style_def.get("description", "")
    example = style_def.get("examples", [""])[0]

    char_str = "、".join(characters) if characters else "待定人物"
    theme_str = "、".join(themes) if themes else theme

    prompt = f"""你是一位历史通俗作品作家。请根据以下创作意图，生成一段**{label}**风格的微样章（150-300字）。

【创作意图】
- 主题/书名：{theme}
- 主要人物：{char_str}
- 核心主题：{theme_str}

【风格要求】
{description}

【开头示例】（仅供参考开头气质，不要照抄）：
"{example}"

请直接输出样章正文，不要加引言、不要加解释、不要加标题前缀。"""


    content = ""
    if llm_client:
        try:
            resp = llm_client.chat(prompt, temperature=0.8, max_tokens=500)
            content = resp.content.strip() if hasattr(resp, "content") else str(resp)
        except Exception as e:
            logger.warning(f"LLM generate failed for {style}: {e}")
            content = _generate_fallback_sample(style, theme, char_str)

    if not content:
        content = _generate_fallback_sample(style, theme, char_str)

    # 缓存key
    cache_key = _make_cache_key(theme, style)

    return TasteSample(
        style=style,
        label=label,
        description=description,
        content=content,
        token_estimate=_estimate_tokens(content),
        cache_key=cache_key,
    )


def _generate_fallback_sample(style: str, theme: str, characters: str) -> str:
    """LLM不可用时的占位样章（仍具可读性）。"""
    fallbacks = {
        "narrative_casual": (
            f"天宝年间，天下承平日久。\n\n"
            f"长安东市，胡商穿梭，粟特商队的驼铃声在黄昏里格外清晰。\n\n"
            f"与此同时，范阳节度使安禄山正在帐中踌躇——"
            f"他等这一刻已经等了太久。\n\n"
            f"《{theme}》的故事，就从这一刻的寂静开始。"
        ),
        "academic_summary": (
            "唐代天宝年间(742-756)，中央与地方的权力格局发生深刻变化。\n\n"
            "安禄山兼任平卢、范阳、河东三镇节度使，拥兵约十九万，占全国边防军六成以上。\n\n"
            f"天宝十四载(755)十一月初四，安禄山以'清君侧'为名，于范阳起兵。\n\n"
            f"《{theme}》所记，即为这一重大历史转折的来龙去脉。"
        ),
        "novel_drama": (
            f"暮色如潮水漫过兴庆宫的飞檐。\n\n"
            f"玄宗立于殿前，遥望北方——\n"
            f"那里有他亲手扶持、如今却举旗反叛的胡人将领；\n"
            f"那里有他再也唤不回的大唐盛世。\n\n"
            f"杨贵妃立于身后，她不知道的是：\n"
            f"此刻正在蒲州提笔的那个人，将以一腔孤忠，"
            f"在史册上刻下比帝王更不朽的名字。\n\n"
            f"《{theme}》。"
        ),
    }
    return fallbacks.get(style, f"《{theme}》正在书写……")


def _make_cache_key(theme: str, style: str) -> str:
    """生成缓存key：theme + style + _topic_version 的哈希。

    _topic_version 在主题变化时递增，使旧 key 全部失效。
    """
    raw = f"{theme}:{style}:v{_topic_version}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:12]


# ── 主类 ───────────────────────────────────────────────
class TastingSampler:
    """
    尝味采样器。

    在用户进入正式 pipeline 前，快速生成 3 种风格的微样章，
    让用户基于真实感受而非抽象参数选择风格。

    使用方式：
        sampler = TastingSampler()
        result = sampler.taste(
            theme="乾元元年·蒲州的墨与血",
            characters=["颜真卿", "安禄山"],
            themes=["忠义", "家国", "书法"]
        )
        # result.samples[0] 是用户点击后选中的那个
        brief = sampler.build_brief_from_choice(
            result.samples[0], result.samples[1:]
        )
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client or _get_llm_client()

    def taste(
        self,
        theme: str,
        characters: List[str] = None,
        themes: List[str] = None,
        style_list: List[str] = None,
    ) -> TastingResult:
        """
        生成 3 种风格的微样章。

        参数：
            theme: 主题/书名
            characters: 主要人物列表
            themes: 核心主题列表
            style_list: 可选，指定要生成的风格，默认 3 种

        返回：
            TastingResult：包含 3 个 TasteSample + 可直接用的 taste_brief
        """
        global _sample_cache, _topic_version, _topic_fingerprint

        characters = characters or []
        themes = themes or []
        style_list = style_list or list(STYLE_DEFINITIONS.keys())

        # ── 主题指纹检测：任何字段变化都递增版本并清空旧缓存 ──
        current_fingerprint = "|".join(sorted([
            theme,
            "|".join(sorted(characters)),
            "|".join(sorted(themes)),
        ]))
        if _topic_fingerprint and current_fingerprint != _topic_fingerprint:
            logger.warning(f"[TastingSampler] Topic fingerprint changed! "
                           f"old={repr(_topic_fingerprint[:30])} "
                           f"new={repr(current_fingerprint[:30])} "
                           f"→ incrementing _topic_version {_topic_version} → {_topic_version + 1}")
            _topic_version += 1
            _sample_cache.clear()
        _topic_fingerprint = current_fingerprint

        samples: List[TasteSample] = []
        cache_hit = False

        for style in style_list:
            cache_key = _make_cache_key(theme, style)

            # 命中缓存
            if cache_key in _sample_cache:
                cached_content = _sample_cache[cache_key]
                logger.info(f"TastingSampler cache hit: {cache_key}")
                cache_hit = True
                sample = TasteSample(
                    style=style,
                    label=STYLE_DEFINITIONS[style]["label"],
                    description=STYLE_DEFINITIONS[style]["description"],
                    content=cached_content,
                    token_estimate=_estimate_tokens(cached_content),
                    cache_key=cache_key,
                )
            else:
                sample = _generate_single_sample(
                    style=style,
                    theme=theme,
                    characters=characters,
                    themes=themes,
                    llm_client=self.llm,
                )
                # 写入缓存
                _sample_cache[cache_key] = sample.content

            samples.append(sample)

        # 构建 taste_brief（可追加到用户原始输入）
        # 默认选择第一种风格（CLI测试用；真实场景由用户点选）
        taste_brief = self.build_taste_brief(
            selected_sample=samples[0],
            all_samples=samples,
            theme=theme,
            characters=characters,
            themes=themes,
        )

        return TastingResult(
            theme=theme,
            characters=characters,
            themes=themes,
            samples=samples,
            taste_brief=taste_brief,
            cache_hit=cache_hit,
        )

    def build_taste_brief(
        self,
        selected_sample: TasteSample,
        all_samples: List[TasteSample],
        theme: str,
        characters: List[str],
        themes: List[str],
    ) -> Dict[str, Any]:
        """
        根据用户选中的样章，构建增强 Brief 传给 pipeline。

        核心思路：用户选的不是"哪个风格好"，而是"这段文字的长相/气质符合我的想象"，
        所以要把这个感知锚点转译为可量化的 pipeline 参数。
        """
        style = selected_sample.style
        style_def = STYLE_DEFINITIONS.get(style, {})

        # 从选中样章推断 focus 侧重
        focus_map = {
            "narrative_casual": ["daily_life", "character_reaction", "scene_building"],
            "academic_summary": ["historical_facts", "institutional_change", "cause_effect"],
            "novel_drama": ["psychological_depth", "emotional_arc", "climax_structure"],
        }
        inferred_focus = focus_map.get(style, [])

        # 从未选中样章推断用户不倾向的维度
        rejected_styles = [s.style for s in all_samples if s.style != style]
        rejected_focus_map = {
            "narrative_casual": ["strict_chronology", "statistical_analysis"],
            "academic_summary": ["pure_narrative", "literary_ornament"],
            "novel_drama": ["dry_factual", "balanced_neutral"],
        }
        avoid_focus = []
        for rs in rejected_styles:
            avoid_focus.extend(rejected_focus_map.get(rs, []))

        brief = {
            "theme": theme,
            "style": style,
            "style_label": style_def.get("label", style),
            "tasted_sample": True,
            "tasted_sample_content": selected_sample.content,
            "focus": inferred_focus,
            "avoid_focus": list(set(avoid_focus)),
            "characters": characters,
            "themes": themes,
            "tasting_timestamp": datetime.now().isoformat(),
            # 传给 pipeline 的提示语（供 LLM 参考）
            "style_guidance": (
                f"用户选择的样章风格为「{style_def.get('label', style)}」。"
                f"特征：{style_def.get('description', '')}"
            ),
        }
        return brief

    def to_user_facing(self, result: TastingResult) -> Dict[str, Any]:
        """
        将 TastingResult 转换为前端可直接渲染的结构。
        """
        return {
            "prompt": (
                f"先看看《{result.theme}》可能的样子——"
                f"你更倾向哪种讲法？"
            ),
            "hint": "这是根据你选主题实时生成的微样章，非最终成书",
            "samples": [
                {
                    "id": i,
                    "style": s.style,
                    "label": s.label,
                    "description": s.description,
                    "content": s.content,
                    "token_estimate": s.token_estimate,
                }
                for i, s in enumerate(result.samples)
            ],
            "skip_option": {
                "label": "跳过尝味，用推荐风格",
                "style": "narrative_casual",  # 默认推荐
                "description": "直接使用最受欢迎的通俗故事化风格",
            },
        }


# ── CLI 快速测试 ────────────────────────────────────────
if __name__ == "__main__":
    sampler = TastingSampler()
    result = sampler.taste(
        theme="乾元元年·蒲州的墨与血",
        characters=["颜真卿", "安禄山"],
        themes=["忠义", "家国", "书法"],
    )
    print(f"\n{'='*60}")
    print(f"  尝味采样结果 | 缓存命中: {result.cache_hit}")
    print(f"{'='*60}")
    for i, s in enumerate(result.samples):
        print(f"\n[{i+1}] {s.label} ({s.style})")
        print(f"    {s.description}")
        print(f"    约 {s.token_estimate} tokens")
        print(f"    ───────────")
        print(f"    {s.content[:120]}……")
    print(f"\n{'='*60}")
    print(f"  风格指引（传给 pipeline）：")
    print(f"    {result.taste_brief.get('style_guidance', '')}")
