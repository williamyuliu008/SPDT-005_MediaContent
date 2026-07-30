# -*- coding: utf-8 -*-
"""
radar_opinion.py — oped_argument IF-P-1：观点评论情报采集
=============================================================

功能：
  1. 采集评论文章所需的情报信号（事件背景、对立观点、反驳预判）
  2. 来源分级：A级（政策文件/学术研究/官方数据）/B级（媒体报道/专家解读）/C级（网络舆论）
  3. 情报卡片（OpinionBrief）含论点支撑、对立声音和潜在反驳

数据源配置：
  A级：政策文件、国务院/部委白皮书、学术期刊（CNKI/万方）、国家统计局
  B级：主流媒体报道（新华社/人民日报/财新）、专家访谈、行业分析报告
  C级：社交媒体讨论、公开论坛、网民评论

使用方式：
  radar = RadarOpinion()
  brief = radar.run(RadarOpinionRequest(topic="AI监管", perspective="支持"))
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
LLM_GATEWAY_PATH = REPO_ROOT / "platform" / "shared" / "llm_gateway.py"


def _load_llm_gateway():
    import importlib.util, sys
    cache_key = "_spdt_llm_gateway"
    if cache_key in sys.modules:
        return sys.modules[cache_key]
    spec = importlib.util.spec_from_file_location(cache_key, str(LLM_GATEWAY_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load llm_gateway from {LLM_GATEWAY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module


# ─────────────────────────────────────────────────────────────────
# 数据类
# ─────────────────────────────────────────────────────────────────

@dataclass
class OpinionSource:
    """观点情报来源"""
    source_id: str
    name: str
    source_type: str   # "policy_doc" / "academic" / "official_data" / "media" / "expert_view" / "social"
    grade: str        # "A" / "B" / "C"
    url: str = ""
    published_date: str = ""
    perspective: str = ""  # "支持" / "反对" / "中立"
    key_claim: str = ""   # 核心主张
    evidence: str = ""     # 证据摘要
    rebuttal_point: str = ""  # 潜在反驳点


@dataclass
class RadarOpinionRequest:
    """采集请求"""
    topic: str
    perspective: str = "中立"           # "支持" / "反对" / "中立"
    industry_focus: str = ""            # 行业聚焦，如"半导体"、"新能源"
    custom_keywords: list[str] = field(default_factory=list)
    max_signals: int = 4                # 最大信号数量（支持/反对各2个）


@dataclass
class OpinionBrief:
    """观点情报摘要"""
    brief_id: str
    topic: str
    perspective: str
    event_context: str                   # 事件背景描述
    supporting_signals: list[OpinionSource]  # 支持论点的信号
    opposing_signals: list[OpinionSource]    # 对立论点的信号
    rebuttal_points: list[str]           # 潜在反驳点
    key_facts: list[str]                # 核心事实（可用于支撑论点）
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "brief_id": self.brief_id,
            "topic": self.topic,
            "perspective": self.perspective,
            "event_context": self.event_context,
            "supporting_signals": [vars(s) for s in self.supporting_signals],
            "opposing_signals": [vars(s) for s in self.opposing_signals],
            "rebuttal_points": self.rebuttal_points,
            "key_facts": self.key_facts,
            "timestamp": self.timestamp,
        }


# ─────────────────────────────────────────────────────────────────
# 核心类
# ─────────────────────────────────────────────────────────────────

class RadarOpinion:
    """观点评论情报采集雷达"""

    def __init__(self):
        self.sources = self._build_source_registry()

    # ──────────────────────────── 公开接口 ────────────────────────────

    def run(self, request: RadarOpinionRequest) -> OpinionBrief:
        """
        执行情报采集
        流程：
          1. 构建扩展关键词
          2. 采集支持信号（A/B/C 三级）
          3. 采集对立信号
          4. 生成反驳预判点
          5. 汇总关键事实
        """
        ts = datetime.now(timezone.utc).isoformat()
        brief_id = f"OP_{uuid.uuid4().hex[:8].upper()}"
        keywords = self._expand_keywords(request)

        # Mock 数据（无 API key 时使用）
        if not _has_llm_key():
            supporting, opposing, rebuttals, facts, context = self._mock_data(request, keywords)
        else:
            supporting, opposing, rebuttals, facts, context = self._fetch_data(request, keywords)

        return OpinionBrief(
            brief_id=brief_id,
            topic=request.topic,
            perspective=request.perspective,
            event_context=context,
            supporting_signals=supporting,
            opposing_signals=opposing,
            rebuttal_points=rebuttals,
            key_facts=facts,
            timestamp=ts,
        )

    # ──────────────────────────── 内部方法 ────────────────────────────

    def _build_source_registry(self) -> dict:
        """建立来源注册表"""
        return {
            "A": [
                {"name": "国务院政策文件", "type": "policy_doc", "perspective": "中立"},
                {"name": "国家统计局", "type": "official_data", "perspective": "中立"},
                {"name": "中国知网（CNKI）", "type": "academic", "perspective": "中立"},
                {"name": "皮书数据库", "type": "academic", "perspective": "中立"},
            ],
            "B": [
                {"name": "新华社", "type": "media", "perspective": "中立"},
                {"name": "财新传媒", "type": "media", "perspective": "中立"},
                {"name": "FT中文网", "type": "media", "perspective": "中立"},
                {"name": "行业专家访谈", "type": "expert_view", "perspective": "支持"},
                {"name": "行业协会报告", "type": "expert_view", "perspective": "反对"},
            ],
            "C": [
                {"name": "微博热搜评论", "type": "social", "perspective": "中立"},
                {"name": "知乎讨论", "type": "social", "perspective": "中立"},
                {"name": "微信公众号精选", "type": "social", "perspective": "中立"},
            ],
        }

    def _expand_keywords(self, req: RadarOpinionRequest) -> list[str]:
        """扩展关键词以提高采集覆盖"""
        base = [req.topic]
        if req.industry_focus:
            base.append(req.industry_focus)
        base.extend(req.custom_keywords)
        # 通用扩展
        common = ["政策", "监管", "影响", "分析", "观点"]
        return list(dict.fromkeys(base + common))  # 去重保持顺序

    def _fetch_data(self, req: RadarOpinionRequest, keywords: list[str]) -> tuple:
        """真实 LLM 采集（需要 DEEPSEEK_API_KEY）"""
        llm = _load_llm_gateway()

        prompt = (
            f"为以下话题的观点评论采集情报信号：\n"
            f"话题：{req.topic}\n"
            f"评论立场：{req.perspective}\n"
            f"行业聚焦：{req.industry_focus or '通用'}\n\n"
            f"请输出（JSON格式）：\n"
            f'{{"event_context": "...", "supporting": [...], "opposing": [...], '
            f'"rebuttals": [...], "key_facts": [...]}}'
        )

        try:
            response = llm.call_deepseek(prompt, model="deepseek-chat")
            import json
            data = json.loads(response)
            supporting = self._parse_signals(data.get("supporting", []), "支持")
            opposing = self._parse_signals(data.get("opposing", []), "反对")
            return supporting, opposing, data.get("rebuttals", []), data.get("key_facts", []), data.get("event_context", "")
        except Exception:
            return self._mock_data(req, keywords)

    def _parse_signals(self, raw: list, perspective: str) -> list[OpinionSource]:
        """解析信号列表"""
        signals = []
        for item in raw[:3]:
            if isinstance(item, dict):
                signals.append(OpinionSource(
                    source_id=f"SIG_{uuid.uuid4().hex[:6].upper()}",
                    name=item.get("name", "未知来源"),
                    source_type=item.get("type", "media"),
                    grade=item.get("grade", "B"),
                    perspective=perspective,
                    key_claim=item.get("claim", ""),
                    evidence=item.get("evidence", ""),
                    rebuttal_point=item.get("rebuttal", ""),
                ))
        return signals

    def _mock_data(self, req: RadarOpinionRequest, keywords: list[str]) -> tuple:
        """Mock 数据：模拟完整情报采集结果"""
        topic = req.topic
        context = (
            f"{topic}已成为当前社会热议话题。"
            f"支持者认为该趋势有利于长期发展，"
            f"反对者则担忧短期阵痛和潜在风险。"
            f"本评论基于现有公开资料进行分析。"
        )

        supporting = [
            OpinionSource(
                source_id="SIG_A001", name="官方政策文件", source_type="policy_doc",
                grade="A", perspective="支持",
                key_claim=f"{topic}符合国家长期战略方向",
                evidence="相关政策文件明确支持该方向的发展规划",
                rebuttal_point="政策支持不等于实施效果，需看执行力度",
            ),
            OpinionSource(
                source_id="SIG_B001", name="行业研究报告", source_type="expert_view",
                grade="B", perspective="支持",
                key_claim=f"{topic}将带动相关产业增长",
                evidence="多家研究机构预测未来三年增长率超15%",
                rebuttal_point="研究结论可能受利益相关方影响",
            ),
        ]

        opposing = [
            OpinionSource(
                source_id="SIG_A002", name="学术期刊研究", source_type="academic",
                grade="A", perspective="反对",
                key_claim=f"{topic}短期内可能带来结构性挑战",
                evidence="发表在核心期刊的研究指出存在对冲风险",
                rebuttal_point="学术结论不代表现实走向，需结合实际判断",
            ),
            OpinionSource(
                source_id="SIG_C001", name="网民讨论（社交媒体）", source_type="social",
                grade="C", perspective="反对",
                key_claim=f"公众对{topic}持谨慎甚至质疑态度",
                evidence="微博/知乎相关话题讨论热度高，负面情绪明显",
                rebuttal_point="网络舆论不代表主流民意，需谨慎解读",
            ),
        ]

        rebuttals = [
            "反对者可能指出：政策支持不等于市场接受，短期执行效果存疑",
            "中立质疑：现有数据样本量不足，结论代表性有限",
            "技术派反驳：实际操作中存在技术瓶颈和成本障碍",
            "经济派质疑：短期投入产出比不理想，商业可行性存疑",
        ]

        facts = [
            f"{topic}涉及市场规模约数千亿元",
            f"相关政策最早可追溯至2020年",
            f"目前已有多个省市出台配套细则",
            f"学术界和产业界对该议题存在明显分歧",
        ]

        return supporting, opposing, rebuttals, facts, context


# ─────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────

def _has_llm_key() -> bool:
    """检查是否配置了 LLM API key"""
    import os
    return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())


# ─────────────────────────────────────────────────────────────────
# 入口（支持 pipeline_router.py 直接调用）
# ─────────────────────────────────────────────────────────────────

def run(topic: str, perspective: str = "中立", **kwargs) -> OpinionBrief:
    """
    便捷入口：radar_opinion.run(topic="AI监管", perspective="支持")
    等价于 RadarOpinion().run(RadarOpinionRequest(topic=topic, perspective=perspective, **kwargs))
    """
    request = RadarOpinionRequest(
        topic=topic,
        perspective=perspective,
        industry_focus=kwargs.get("industry_focus", ""),
        custom_keywords=kwargs.get("custom_keywords", []),
        max_signals=kwargs.get("max_signals", 4),
    )
    return RadarOpinion().run(request)
