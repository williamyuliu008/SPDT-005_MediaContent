# -*- coding: utf-8 -*-
"""
smarttext_classifier.py — SPDT-005 自然语言内容分类器
=====================================================

功能：
  1. 接收自然语言内容需求（标题/描述/关键词）
  2. 使用 LLM 对照 registry 中 6 种 content_type 做分类
  3. 输出 ContentSpec（含 content_type + metadata）
  4. 支持单类型和多类型（复杂请求拆分为多个 ContentSpec）

与 pipeline_router.py 的关系：
  pipeline_router.py 负责：已知 content_type → 执行管线
  smarttext_classifier.py 负责：NL 需求 → 确定 content_type

使用方式：
  classifier = SmartTextClassifier()
  spec = classifier.classify("DeepMind发布AlphaFold3，影响深远")
  # → ContentSpec(content_type="science_research", title="...", channels=["markdown","web"])

  specs = classifier.classify_multi("DeepMind发布AlphaFold3")
  # → [ContentSpec(...), ContentSpec(...)]  多类型拆分结果
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

import yaml

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
LLM_GATEWAY_PATH = REPO_ROOT / "platform" / "shared" / "llm_gateway.py"
REGISTRY_PATH = REPO_ROOT / "platform" / "kb" / "content_type_registry.yaml"

# ─────────────────────────────────────────────────────────────────
# LLM Gateway（带缓存）
# ─────────────────────────────────────────────────────────────────

def _load_llm_gateway():
    import importlib.util
    cache_key = "_spdt05_llm_clf"
    if cache_key in sys.modules:
        return sys.modules[cache_key]
    spec = importlib.util.spec_from_file_location(cache_key, str(LLM_GATEWAY_PATH))
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module


# ─────────────────────────────────────────────────────────────────
# ContentSpecLite — 分类器专用简化版（不依赖 pipeline_router）
# ─────────────────────────────────────────────────────────────────

@dataclass
class ContentSpecLite:
    """SmartTextClassifier 输出的内容规格（pipeline_router.ContentSpec 兼容）"""
    content_type: str
    title: str = ""
    description: str = ""
    target_audience: str = ""
    channels: list[str] = field(default_factory=list)
    priority: int = 5
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "content_type": self.content_type,
            "title": self.title,
            "description": self.description,
            "target_audience": self.target_audience,
            "channels": self.channels,
            "priority": self.priority,
            "metadata": self.metadata,
        }

    def to_router_spec(self):
        """转换为 pipeline_router.ContentSpec（懒加载，避免模块名冲突）"""
        import importlib.util, sys
        _key = "_spdt05_pipeline_router"
        if _key not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                _key,
                str(REPO_ROOT / "platform/1_ingest/router/pipeline_router.py"),
            )
            m = importlib.util.module_from_spec(spec)
            sys.modules[_key] = m
            spec.loader.exec_module(m)
        ContentSpec = sys.modules[_key].ContentSpec
        return ContentSpec(
            content_type=self.content_type,
            title=self.title,
            description=self.description,
            target_audience=self.target_audience,
            channels=self.channels,
            priority=self.priority,
            metadata=self.metadata,
        )

    def save(self, output_dir: Optional[Path] = None) -> Path:
        """持久化到 JSON 文件"""
        if output_dir is None:
            output_dir = REPO_ROOT / "platform" / "5_deliver" / "checkpoint" / "content_specs"
        output_dir.mkdir(parents=True, exist_ok=True)
        spec_id = uuid.uuid4().hex[:8]
        path = output_dir / f"spec_{spec_id}.json"
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path


# ─────────────────────────────────────────────────────────────────
# 分类引擎
# ─────────────────────────────────────────────────────────────────

@dataclass
class ClassificationResult:
    """LLM 分类结果（含置信度和理由）"""
    content_type: str
    confidence: float       # 0.0–1.0
    reasoning: str         # 为什么选这个类型
    title_hint: str        # 建议的标题
    audience_hint: str     # 建议的受众
    channels_hint: list[str]  # 建议的发布渠道
    priority_hint: int     # 建议优先级 1-10

    def to_spec(self) -> ContentSpecLite:
        return ContentSpecLite(
            content_type=self.content_type,
            title=self.title_hint,
            description=self.reasoning,
            target_audience=self.audience_hint,
            channels=self.channels_hint,
            priority=self.priority_hint,
            metadata={
                "classification_confidence": self.confidence,
                "classification_reasoning": self.reasoning,
                "classified_at": datetime.now(timezone.utc).isoformat(),
                "classifier": "SmartTextClassifier_v1.0",
            },
        )


class SmartTextClassifier:
    """
    自然语言 → ContentSpec 分类器

    工作流程：
      1. 加载 registry（content_type 定义 + 三维分类维度）
      2. 构造分类 prompt（含 registry 中的类型定义）
      3. 调用 LLM，返回 JSON 分类结果
      4. 解析为 ClassificationResult → ContentSpecLite
      5. 记录分类日志
    """

    # Registry 中已注册的类型（按 priority 降序排列）
    CONTENT_TYPES = [
        "breakdown_news",
        "science_research",
        "deep_industry_report",
        "science_fact",
        "oped_argument",
        "product_review",
        "creative",
    ]

    # 三维分类维度说明（给 LLM 参考）
    DIMENSION_DESCRIPTIONS = """
维度说明：
  accuracy（准确性）: 1=低（创意为主），5=极高（医疗/学术级）
  literary（文学性）: 1=客观简洁，5=文学化表达
  professional_depth（专业深度）: 1=大众可读，5=行业专家级

触发信号：
  - breakdown_news：突发事件/危机/重大政策/事故，时间敏感
  - science_research：新论文/新发现/SLA≤2h，五段式叙事
  - deep_industry_report：行业分析/3000-8000字/数据驱动/SLA=4h
  - science_fact：长效知识点/非触发式/科普图谱/SLA=4h
  - oped_argument：有立场/论点/说服力/七段式
  - product_review：产品评测/对比/购买建议
  - creative：非虚构故事/人物特稿/叙事感

注意：sla_hours 为 0 表示无 SLA 限制（常态化内容）
"""

    SYSTEM_PROMPT = """你是一个媒体内容类型分类专家。

根据用户输入的自然语言内容需求，判断最适合的内容类型，并输出结构化的分类结果。

{registry_summary}

{dimensions}

输出要求：
  - 只选择一个最匹配的类型（content_type）
  - 置信度 0.0-1.0，低于 0.6 时标记为 uncertain
  - reasoning 说明为什么选这个类型，以及为什么不选其他
  - title_hint：从用户需求中提炼一个吸引人的标题（≤20字）
  - audience_hint：目标受众（≤15字）
  - channels_hint：推荐发布渠道（最多3个，从 ["markdown","web","feishu","wechat_mp","mobile","feeds"] 中选）
  - priority_hint：1-10，10最高（突发事件=10，深度报告=5，常态内容=3）

返回格式（严格 JSON，不要额外文字）：
{{"content_type":"<类型>","confidence":0.0-1.0,"reasoning":"...","title_hint":"...","audience_hint":"...","channels_hint":["..."],"priority_hint":1-10}}
"""

    USER_PROMPT_TEMPLATE = "内容需求：{nl_input}\n\n请分类。"

    def __init__(self, registry_path: Optional[Path] = None, mock: bool = False):
        self.registry_path = registry_path or REGISTRY_PATH
        self.registry = self._load_registry()
        self.mock = mock
        self._log: list[dict] = []

    def _load_registry(self) -> dict:
        if not self.registry_path.exists():
            return {"content_types": {}}
        return yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or {}

    def _build_registry_summary(self) -> str:
        """从 registry 中提取类型摘要，给 LLM 参考"""
        types = self.registry.get("content_types", {})
        lines = []
        for key, cfg in types.items():
            if cfg.get("status") == "skeleton":
                continue  # 骨架类型不参与分类
            dims = cfg.get("pipeline_dimensions", {})
            lines.append(
                f"- {key}: {cfg.get('label', key)}\n"
                f"  accuracy={dims.get('accuracy','?')} literary={dims.get('literary','?')} "
                f"professional_depth={dims.get('professional_depth','?')}\n"
                f"  {cfg.get('description','')}"
            )
        return "\n".join(lines) if lines else "(registry empty)"

    def classify(self, nl_input: str) -> ContentSpecLite:
        """
        将自然语言需求分类为 ContentSpecLite。

        参数：
          nl_input: 自然语言描述，如"DeepMind发布AlphaFold3，影响深远"

        返回：
          ContentSpecLite 对象
        """
        if not nl_input or not nl_input.strip():
            return self._default_spec("无效输入，使用默认路由")

        try:
            result = self._llm_classify(nl_input)
        except Exception as e:
            result = self._rule_classify(nl_input, error=str(e))

        spec = result.to_spec()

        # 记录日志
        self._log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nl_input": nl_input[:100],
            "content_type": spec.content_type,
            "confidence": spec.metadata.get("classification_confidence", 0),
            "title": spec.title,
        })

        return spec

    def classify_multi(self, nl_input: str) -> list[ContentSpecLite]:
        """
        多类型分类（处理复杂请求）。

        如果单一分类置信度 < 0.7，或关键词跨越多个类型，
        拆分为多个 ContentSpec。
        """
        primary = self.classify(nl_input)

        if primary.metadata.get("classification_confidence", 1.0) >= 0.7:
            return [primary]

        # 尝试多类型推断
        multi_types = self._infer_multi_types(nl_input)
        if len(multi_types) > 1:
            return multi_types

        return [primary]

    def _llm_classify(self, nl_input: str) -> ClassificationResult:
        """调用 LLM 进行分类"""
        if self.mock:
            return self._rule_classify(nl_input, error="mock mode")

        llm = _load_llm_gateway()
        gateway = llm.LLMGateway()

        registry_summary = self._build_registry_summary()
        system = self.SYSTEM_PROMPT.format(
            registry_summary=registry_summary,
            dimensions=self.DIMENSION_DESCRIPTIONS,
        )
        user = self.USER_PROMPT_TEMPLATE.format(nl_input=nl_input)

        raw = gateway.chat(user, system=system, model=None, temperature=0.1)
        return self._parse_classification(raw, nl_input)

    def _parse_classification(self, raw: str, nl_input: str) -> ClassificationResult:
        """从 LLM 输出中解析 JSON"""
        # 提取 JSON 块
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return ClassificationResult(
                    content_type=data.get("content_type", ""),
                    confidence=float(data.get("confidence", 0.5)),
                    reasoning=data.get("reasoning", ""),
                    title_hint=data.get("title_hint", nl_input[:20]),
                    audience_hint=data.get("audience_hint", "大众读者"),
                    channels_hint=data.get("channels_hint", ["markdown", "web"]),
                    priority_hint=int(data.get("priority_hint", 5)),
                )
            except (json.JSONDecodeError, ValueError):
                pass

        # JSON 解析失败，降级到规则匹配
        return self._rule_classify(nl_input, error=f"parse failed: {raw[:50]}")

    def _rule_classify(self, nl_input: str, error: str = "") -> ClassificationResult:
        """
        规则匹配降级（LLM 失败时使用，或 mock 模式）。

        基于关键词的快速分类，不依赖 LLM。
        """
        nl = nl_input.lower()

        # 优先级高的关键词
        breaking_kw = ["突发", "紧急", "刚刚", "快讯", " breaking", "突发新闻", "危机", "重大"]
        science_kw = ["研究", "论文", "发现", "science", "实验", "科学家", "nature", "arxiv"]
        industry_kw = ["行业", "报告", "分析", "市场", "深度", "数据", "公司", "财报", "产业"]
        oped_kw = ["观点", "评论", "认为", "应该", "必须", "批评", "支持", "opinion", "editorial"]
        review_kw = ["评测", "测评", "对比", "体验", "产品", "手机", "电脑", "review"]
        creative_kw = ["故事", "人物", "采访", "特稿", "纪录", "叙述", "story"]

        for kw in breaking_kw:
            if kw in nl:
                return ClassificationResult(
                    content_type="breakdown_news", confidence=0.8, reasoning=f"关键词命中: {kw}",
                    title_hint=nl_input[:20], audience_hint="大众", channels_hint=["markdown","web","feishu"], priority_hint=10,
                )
        for kw in science_kw:
            if kw in nl:
                return ClassificationResult(
                    content_type="science_research", confidence=0.75, reasoning=f"关键词命中: {kw}",
                    title_hint=nl_input[:20], audience_hint="关注科技的读者", channels_hint=["markdown","web"], priority_hint=7,
                )
        for kw in industry_kw:
            if kw in nl:
                return ClassificationResult(
                    content_type="deep_industry_report", confidence=0.7, reasoning=f"关键词命中: {kw}",
                    title_hint=nl_input[:20], audience_hint="行业从业者", channels_hint=["markdown","web","feishu"], priority_hint=5,
                )
        for kw in oped_kw:
            if kw in nl:
                return ClassificationResult(
                    content_type="oped_argument", confidence=0.7, reasoning=f"关键词命中: {kw}",
                    title_hint=nl_input[:20], audience_hint="公共议题读者", channels_hint=["web","feishu"], priority_hint=7,
                )
        for kw in review_kw:
            if kw in nl:
                return ClassificationResult(
                    content_type="product_review", confidence=0.7, reasoning=f"关键词命中: {kw}",
                    title_hint=nl_input[:20], audience_hint="消费者", channels_hint=["web","wechat_mp"], priority_hint=4,
                )
        for kw in creative_kw:
            if kw in nl:
                return ClassificationResult(
                    content_type="creative", confidence=0.7, reasoning=f"关键词命中: {kw}",
                    title_hint=nl_input[:20], audience_hint="大众", channels_hint=["web","feishu"], priority_hint=3,
                )

        # 默认：science_research
        return ClassificationResult(
            content_type="science_research", confidence=0.5,
            reasoning=f"无明确关键词，回退默认值. error={error}",
            title_hint=nl_input[:20], audience_hint="大众", channels_hint=["markdown","web"], priority_hint=5,
        )

    def _infer_multi_types(self, nl_input: str) -> list[ContentSpecLite]:
        """推断多类型（启发式）"""
        specs: list[ContentSpecLite] = []
        nl = nl_input.lower()

        if any(k in nl for k in ["深度", "行业", "分析", "报告"]) and any(k in nl for k in ["发现", "研究", "论文"]):
            specs.append(self._rule_classify(nl_input, "multi: deep+research").to_spec())
            specs.append(self._rule_classify(nl_input, "multi: science_research").to_spec())
        elif any(k in nl for k in ["观点", "评论"]) and any(k in nl for k in ["发现", "研究"]):
            specs.append(self._rule_classify(nl_input, "multi: oped").to_spec())
            specs.append(self._rule_classify(nl_input, "multi: science").to_spec())

        return specs[:2]  # 最多 2 个

    def _default_spec(self, reason: str) -> ContentSpecLite:
        return ContentSpecLite(
            content_type="science_research",
            title="",
            description=reason,
            target_audience="大众读者",
            channels=["markdown", "web"],
            priority=5,
            metadata={"fallback": True, "reason": reason},
        )

    @property
    def classification_log(self) -> list[dict]:
        """返回分类历史"""
        return self._log.copy()


# ─────────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os

    mock = not bool(os.environ.get("DEEPSEEK_API_KEY"))
    print(f"[SmartTextClassifier] {'Mock' if mock else 'LLM'} 模式启动\n")

    classifier = SmartTextClassifier(mock=mock)

    # 测试用例
    tests = [
        "DeepMind发布AlphaFold3，生物学革命",
        "2026年中国新能源汽车行业深度分析报告",
        "突发：某地发现不明原因肺炎病例",
        "AI监管是必要的刹车而非倒车",
        "小米15 ultra评测：影像旗舰的极限在哪里",
        "一位乡村教师的二十六年坚守",
    ]

    for i, test in enumerate(tests, 1):
        print(f"[{i}] 输入: {test}")
        spec = classifier.classify(test)
        print(f"    → 类型: {spec.content_type}  置信度: {spec.metadata.get('classification_confidence','?')}")
        print(f"    → 标题: {spec.title}")
        print(f"    → 受众: {spec.target_audience}")
        print(f"    → 渠道: {spec.channels}")
        print(f"    → 优先级: {spec.priority}")
        print(f"    → 理由: {spec.metadata.get('classification_reasoning','')}")
        print()

    print(f"共分类 {len(classifier.classification_log)} 条")
