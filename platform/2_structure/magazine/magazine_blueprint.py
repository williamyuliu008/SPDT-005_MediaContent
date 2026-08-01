# -*- coding: utf-8 -*-
"""
magazine_blueprint.py — 科学杂志选题策划器
============================================

功能：
  1. 根据领域主题 + 产品规格，生成 MagazineBlueprint（文章规划）
  2. 支持预置模板加载 + LLM 增强两种模式

使用方式：
  # 方式1：预置模板（无需 LLM）
  bp = MagazineBlueprintLoader().load(
      domain_topic="人工智能与科学研究的交叉突破",
      title="科学前沿",
      issue="2026-Q3",
      audience="理工科研究生",
  )

  # 方式2：LLM 增强（自动推荐文章 topic）
  bp = MagazineBlueprintGenerator(llm).generate(
      domain_topic="人工智能与科学研究的交叉突破",
      title="科学前沿",
      issue="2026-Q3",
  )
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

@dataclass
class ArticleSpec:
    """
    单篇文章规划（Blueprint 的组成单元）

    article_role: cover_story / explain / industry / news_brief / oped
    pipeline_type: science_research / deep_industry_report / oped_argument
    """
    article_role: str          # 角色（见上）
    pipeline_type: str         # 管线类型
    topic: str                 # 文章主题
    constraints: dict = field(default_factory=dict)
    # constraints 可包含：depth_level / max_signals / perspective / min_score


@dataclass
class MagazineSpec:
    """杂志规格（用户输入）"""
    title: str                 # 杂志名称（如"科学前沿"）
    domain_topic: str          # 领域主题（如"人工智能与科学研究的交叉突破"）
    issue: str                 # 期号（如"2026-Q3"）
    audience: str = ""         # 目标读者
    publication_date: str = "" # 发布日期（ISO）
    description: str = ""       # 杂志简介/编辑手记


@dataclass
class MagazineBlueprint:
    """
    杂志蓝图：包含杂志规格 + 5篇（标准结构）文章规划

    这是 Blueprint 层的核心输出，作为 Orchestrator 的输入。
    """
    spec: MagazineSpec
    articles: list[ArticleSpec]
    blueprint_id: str = ""
    generated_at: str = ""

    def __post_init__(self):
        if not self.blueprint_id:
            self.blueprint_id = f"BP-{uuid.uuid4().hex[:8].upper()}"
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def get_article(self, role: str) -> Optional[ArticleSpec]:
        return next((a for a in self.articles if a.article_role == role), None)

    def to_dict(self) -> dict:
        return {
            "blueprint_id": self.blueprint_id,
            "generated_at": self.generated_at,
            "spec": {
                "title": self.spec.title,
                "domain_topic": self.spec.domain_topic,
                "issue": self.spec.issue,
                "audience": self.spec.audience,
                "publication_date": self.spec.publication_date,
                "description": self.spec.description,
            },
            "articles": [
                {
                    "article_role": a.article_role,
                    "pipeline_type": a.pipeline_type,
                    "topic": a.topic,
                    "constraints": a.constraints,
                }
                for a in self.articles
            ],
        }


# ─────────────────────────────────────────────────────────────────
# 预置领域模板
# ─────────────────────────────────────────────────────────────────

# role → pipeline_type + depth_level 映射
ROLE_PIPELINE_MAP = {
    "cover_story": ("science_research",    "deep"),
    "explain":      ("science_research",    "medium"),
    "industry":     ("deep_industry_report","deep"),
    "news_brief":   ("science_research",    "short"),
    "oped":         ("oped_argument",       "medium"),
}

# 角色展示名称
ROLE_DISPLAY_NAMES = {
    "cover_story": "封面专题",
    "explain":      "科学解释",
    "industry":     "产业分析",
    "news_brief":   "科技新闻",
    "oped":         "观点评论",
}


# 预置领域 → 文章 topic 模板
# 其中 {domain_topic} 和 {subtopic} 由输入填充
DOMAIN_TEMPLATES = {
    "AI+Science": {
        "roles": [
            ("cover_story", "封面专题：{domain_topic}的核心突破与意义"),
            ("explain",     "深度解读：{domain_topic}背后的科学原理"),
            ("industry",    "产业透视：{domain_topic}的市场格局与技术路线"),
            ("news_brief",  "近期动态：{subtopic}领域的5-8项重要进展"),
            ("oped",        "观点交锋：{domain_topic}是机遇还是风险？"),
        ],
        "default_subtopic": "AI+Science",
    },
    "default": {
        "roles": [
            ("cover_story", "{domain_topic}领域最重要的突破是什么？"),
            ("explain",     "入门指南：{domain_topic}是什么，为什么重要"),
            ("industry",    "产业现状：{domain_topic}的市场格局与竞争态势"),
            ("news_brief",  "近期速递：{domain_topic}领域的最新进展"),
            ("oped",        "观点评论：{domain_topic}的未来该走向何方？"),
        ],
        "default_subtopic": "科技",
    },
}


# ─────────────────────────────────────────────────────────────────
# MagazineBlueprintLoader（预置模板模式）
# ─────────────────────────────────────────────────────────────────

class MagazineBlueprintLoader:
    """
    使用预置领域模板加载杂志蓝图。
    v1.0 核心实现，无需 LLM 调用。
    """

    def load(
        self,
        domain_topic: str,
        title: str = "科学前沿",
        issue: str = "",
        audience: str = "",
        publication_date: str = "",
        description: str = "",
        domain_key: str = "default",
    ) -> MagazineBlueprint:
        """
        从预置模板生成 MagazineBlueprint。

        参数：
          domain_topic：领域主题（如"人工智能与科学研究的交叉突破"）
          title：杂志名称
          issue：期号（如"2026-Q3"），默认自动生成
          audience：目标读者
          publication_date：发布日期（ISO），默认今天
          description：杂志简介
          domain_key：领域模板键，默认"default"（也支持"AI+Science"）
        """
        # 解析领域主题，提取主语和子主题
        main_topic, subtopic = self._parse_topic(domain_topic)

        # 获取模板
        template = DOMAIN_TEMPLATES.get(domain_key, DOMAIN_TEMPLATES["default"])
        if domain_key == "default" and "AI" in domain_topic and "科学" in domain_topic:
            template = DOMAIN_TEMPLATES["AI+Science"]

        # 生成期号
        if not issue:
            now = datetime.now(timezone.utc)
            quarter = (now.month - 1) // 3 + 1
            issue = f"{now.year}-Q{quarter}"

        # 生成发布日期
        if not publication_date:
            publication_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 构建 MagazineSpec
        spec = MagazineSpec(
            title=title,
            domain_topic=domain_topic,
            issue=issue,
            audience=audience or "科技爱好者、研究生及以上",
            publication_date=publication_date,
            description=description,
        )

        # 生成文章规划
        articles = []
        for role, topic_template in template["roles"]:
            pipeline_type, depth_level = ROLE_PIPELINE_MAP[role]

            # 填充 topic 模板
            topic_str = topic_template.format(
                domain_topic=main_topic,
                subtopic=template["default_subtopic"],
            )

            constraints = {
                "depth_level": depth_level,
                "target_audience": audience or spec.audience,
                "min_score": self._role_min_score(role),
            }
            if pipeline_type == "science_research":
                constraints["max_signals"] = 5 if depth_level == "deep" else 3
            elif pipeline_type == "deep_industry_report":
                constraints["max_signals"] = 6
            elif pipeline_type == "oped_argument":
                constraints["perspective"] = "支持" if role == "oped" else "中立"
                constraints["max_signals"] = 4

            articles.append(ArticleSpec(
                article_role=role,
                pipeline_type=pipeline_type,
                topic=topic_str,
                constraints=constraints,
            ))

        return MagazineBlueprint(spec=spec, articles=articles)

    def _parse_topic(self, domain_topic: str) -> tuple[str, str]:
        """
        从领域主题提取主语和子主题。
        例如："人工智能与科学研究的交叉突破" → ("人工智能", "科技")
        """
        # 简单启发式：取前 8-15 字作为主语
        main = domain_topic[:12].strip("，、的与和")
        sub = "科技"
        if "AI" in domain_topic or "人工智能" in domain_topic:
            sub = "AI+Science"
        elif "量子" in domain_topic:
            sub = "量子科技"
        elif "半导体" in domain_topic:
            sub = "半导体"
        return main, sub

    def _role_min_score(self, role: str) -> int:
        return {
            "cover_story": 80,
            "explain":      75,
            "industry":     80,
            "news_brief":   70,
            "oped":         80,
        }.get(role, 75)


# ─────────────────────────────────────────────────────────────────
# MagazineBlueprintGenerator（LLM 增强模式，v1.1）
# ─────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[3]  # → SPDT-005_MediaContent


def _load_llm_gateway():
    """延迟加载 LLM Gateway（避免循环导入）"""
    import importlib.util, sys
    cache_key = "_spdt_blueprint_llm"
    if cache_key in sys.modules:
        return sys.modules[cache_key]
    spec = importlib.util.spec_from_file_location(
        cache_key,
        str(_REPO_ROOT / "platform" / "shared" / "llm_gateway.py"),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load llm_gateway")
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module


class MagazineBlueprintGenerator:
    """
    LLM 增强的杂志蓝图生成器（v1.1）。

    LLM 根据领域主题，深度分析后推荐每篇文章的精确 topic，
    体现领域内细分方向、近期热点和叙事逻辑。

    使用方式：
      gen = MagazineBlueprintGenerator()
      gen.init_llm()  # 自动加载 LLM Gateway
      bp = gen.generate(
          domain_topic="人工智能与科学研究的交叉突破",
          title="科学前沿",
          issue="2026-Q3",
      )
    """

    # 角色定义（含约束模板）
    ROLES = [
        {
            "role": "cover_story",
            "pipeline": "science_research",
            "depth": "deep",
            "description": "封面专题：选取领域内最重大、最具冲击力的突破",
            "word_range": "3000-4000字",
        },
        {
            "role": "explain",
            "pipeline": "science_research",
            "depth": "medium",
            "description": "科学解释：核心概念入门，面向普通读者说清楚'是什么'",
            "word_range": "2000-2500字",
        },
        {
            "role": "industry",
            "pipeline": "deep_industry_report",
            "depth": "deep",
            "description": "产业分析：市场格局、技术路线、竞争态势",
            "word_range": "3000-5000字",
        },
        {
            "role": "news_brief",
            "pipeline": "science_research",
            "depth": "short",
            "description": "科技动态：5-8条近期重要进展，快速扫描",
            "word_range": "每条≤300字",
        },
        {
            "role": "oped",
            "pipeline": "oped_argument",
            "depth": "medium",
            "description": "观点交锋：有立场、有数据、有反驳",
            "word_range": "1200-1800字",
        },
    ]

    SYSTEM_PROMPT = """你是一位资深科技杂志编辑，擅长策划有深度、有张力的科技杂志内容。

你的任务是根据用户提供的领域主题，策划一期杂志的5篇文章选题。
每篇文章需要体现：
1. 独特的切入角度（不是泛泛而谈）
2. 与领域主题的紧密关联
3. 叙事上的递进或互补关系

请以 JSON 格式输出选题方案。"""

    USER_PROMPT_TEMPLATE = """## 杂志主题
**领域主题**: {domain_topic}
**杂志名称**: {title}
**目标读者**: {audience}

## 你的任务
请为这期杂志策划5篇文章选题，并说明各篇之间的叙事逻辑。

## 输出要求（JSON）
```json
{{
  "editor_note": "编辑手记：2-3句话说明本期杂志的核心理念和叙事主线",
  "articles": [
    {{
      "role": "cover_story",
      "topic": "精确的文章标题（15-30字，有冲击力）",
      "angle": "切入角度说明（1-2句话）",
      "key_points": ["要点1", "要点2", "要点3"],
      "keywords": ["关键词1", "关键词2"]
    }},
    {{
      "role": "explain",
      "topic": "精确的文章标题（15-25字）",
      "angle": "切入角度说明",
      "key_points": ["要点1", "要点2", "要点3"],
      "keywords": ["关键词1", "关键词2"]
    }},
    {{
      "role": "industry",
      "topic": "精确的文章标题（含产业/市场视角）",
      "angle": "切入角度说明",
      "key_points": ["要点1", "要点2", "要点3"],
      "keywords": ["关键词1", "关键词2"]
    }},
    {{
      "role": "news_brief",
      "topic": "精确的文章标题（含动态/速递视角）",
      "angle": "切入角度说明",
      "key_points": ["要点1", "要点2"],
      "keywords": ["关键词1", "关键词2"]
    }},
    {{
      "role": "oped",
      "topic": "精确的文章标题（含观点/争议性）",
      "angle": "切入角度说明",
      "key_points": ["要点1", "要点2", "要点3"],
      "keywords": ["关键词1", "关键词2"]
    }}
  ]
}}
```

请直接输出 JSON，不要有其他文字。"""

    def __init__(self, llm=None):
        self._llm = llm
        self._loader = MagazineBlueprintLoader()

    def init_llm(self):
        """初始化 LLM（从 LLM Gateway 加载）"""
        if self._llm is None:
            gateway = _load_llm_gateway()
            self._llm = gateway.LLMGateway()
        return self

    def generate(
        self,
        domain_topic: str,
        title: str = "科学前沿",
        issue: str = "",
        audience: str = "",
        description: str = "",
    ) -> MagazineBlueprint:
        """
        生成杂志蓝图。优先使用 LLM 增强，fallback 到预置模板。
        """
        if self._llm is None:
            return self._loader.load(
                domain_topic=domain_topic,
                title=title,
                issue=issue,
                audience=audience,
                description=description,
            )

        try:
            return self._llm_enhanced_generate(
                domain_topic, title, issue, audience, description
            )
        except Exception as exc:
            # LLM 增强失败时降级到预置模板
            import sys as _sys
            _sys.stderr.write(f"[DEBUG] LLM Blueprint failed: {type(exc).__name__}: {exc}\n")
            _sys.stderr.flush()
            return self._loader.load(
                domain_topic=domain_topic,
                title=title,
                issue=issue,
                audience=audience,
                description=description,
            )

    def _llm_enhanced_generate(
        self,
        domain_topic: str,
        title: str,
        issue: str,
        audience: str,
        description: str,
    ) -> MagazineBlueprint:
        """
        LLM 增强生成（v1.1 实现）。

        调用 LLM 分析领域主题，生成：
        1. 每篇文章的精确 topic（含切入角度）
        2. 编辑手记（杂志整体叙事主线）
        3. 各篇文章的 constraints（keywords、max_signals 等）
        """
        # 构造 prompt
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            domain_topic=domain_topic,
            title=title,
            audience=audience or "科技爱好者、研究生及以上",
        )

        # 调用 LLM
        response = self._llm.chat(
            prompt=user_prompt,
            system=self.SYSTEM_PROMPT,
            model="deepseek-v4-flash",
            temperature=0.7,
        )

        # 解析 JSON
        import json, re
        content = (response.content if hasattr(response, "content") else str(response)).strip()

        # 提取 JSON 块
        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            content,
            re.DOTALL,
        )
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = content

        plan = json.loads(json_str)

        # 生成期号和日期
        now = datetime.now(timezone.utc)
        if not issue:
            quarter = (now.month - 1) // 3 + 1
            issue = f"{now.year}-Q{quarter}"
        if not audience:
            audience = "科技爱好者、研究生及以上"

        # 构建 MagazineSpec（融合 LLM 编辑手记）
        editor_note = plan.get("editor_note", description or "")
        spec = MagazineSpec(
            title=title,
            domain_topic=domain_topic,
            issue=issue,
            audience=audience,
            publication_date=now.strftime("%Y-%m-%d"),
            description=description or editor_note,
        )

        # 构建 ArticleSpec 列表
        role_plan_map = {a["role"]: a for a in plan.get("articles", [])}
        articles = []

        for role_def in self.ROLES:
            role = role_def["role"]
            plan_article = role_plan_map.get(role, {})

            topic = plan_article.get("topic") or (
                f"{role_def['description']}：{domain_topic}"
            )
            angle = plan_article.get("angle", "")
            keywords = plan_article.get("keywords", [])
            key_points = plan_article.get("key_points", [])

            # 构建 constraints
            constraints = {
                "depth_level": role_def["depth"],
                "target_audience": audience,
                "min_score": self._role_min_score(role),
                "angle": angle,
            }
            if keywords:
                constraints["keywords"] = keywords[:5]
            if key_points:
                constraints["key_points"] = key_points[:3]

            if role_def["pipeline"] == "science_research":
                constraints["max_signals"] = 5 if role_def["depth"] == "deep" else 3
            elif role_def["pipeline"] == "deep_industry_report":
                constraints["max_signals"] = 6
                constraints["industry"] = domain_topic
            elif role_def["pipeline"] == "oped_argument":
                constraints["perspective"] = "支持"
                constraints["max_signals"] = 4

            articles.append(ArticleSpec(
                article_role=role,
                pipeline_type=role_def["pipeline"],
                topic=topic,
                constraints=constraints,
            ))

        blueprint = MagazineBlueprint(spec=spec, articles=articles)

        # 记录 LLM 分析结果到 blueprint 扩展字段
        blueprint._llm_editor_note = editor_note
        blueprint._llm_articles_plan = role_plan_map

        return blueprint

    def _role_min_score(self, role: str) -> int:
        return {
            "cover_story": 80,
            "explain":      75,
            "industry":     80,
            "news_brief":   70,
            "oped":         80,
        }.get(role, 75)


def load_blueprint(
    domain_topic: str,
    title: str = "科学前沿",
    issue: str = "",
    audience: str = "",
    description: str = "",
    use_llm: bool = False,
) -> MagazineBlueprint:
    """
    快捷函数：加载杂志蓝图。

    参数：
      use_llm: 是否使用 LLM 增强模式（v1.1）。默认 False（预置模板）。

    等价于：
      # 预置模板
      MagazineBlueprintLoader().load(...)

      # LLM 增强（v1.1）
      gen = MagazineBlueprintGenerator().init_llm()
      gen.generate(...)
    """
    if use_llm:
        gen = MagazineBlueprintGenerator().init_llm()
        return gen.generate(
            domain_topic=domain_topic,
            title=title,
            issue=issue,
            audience=audience,
            description=description,
        )
    else:
        return MagazineBlueprintLoader().load(
            domain_topic=domain_topic,
            title=title,
            issue=issue,
            audience=audience,
            description=description,
        )


# ─────────────────────────────────────────────────────────────────
# 便捷入口函数
# ─────────────────────────────────────────────────────────────────

def load_blueprint(
    domain_topic: str,
    title: str = "科学前沿",
    issue: str = "",
    audience: str = "",
    description: str = "",
) -> MagazineBlueprint:
    """
    快捷函数：从预置模板加载杂志蓝图。
    等价于 MagazineBlueprintLoader().load(...)
    """
    return MagazineBlueprintLoader().load(
        domain_topic=domain_topic,
        title=title,
        issue=issue,
        audience=audience,
        description=description,
    )
