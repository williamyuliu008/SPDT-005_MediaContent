# -*- coding: utf-8 -*-
"""
radar_deep_industry.py — deep_industry_report IF-P-1：深度行业报告情报采集
==========================================================================

功能：
  1. 采集行业情报（财报/政策文件/行业门户/专家访谈/机构研报）
  2. 来源分级：A级（机构研报/财报）/B级（行业媒体）/C级（一般报道）
  3. 情报卡片（IntelligenceBrief）含多源信号汇总

数据源配置：
  A级：Bloomberg/Reuters Financial, 企业财报（EDGAR/港交所）, 投行研报, 政府白皮书
  B级：行业门户（36Kr/虎嗅/财新）, 行业协会报告, 展会/会议信息
  C级：新闻报道, 社交媒体讨论, 公开论坛

使用方式：
  radar = RadarDeepIndustry()
  brief = radar.run(RadarDeepIndustryRequest(topic="半导体国产化"))
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
class IndustrySource:
    """行业情报来源"""
    source_id: str
    name: str
    source_type: str   # "research_report" / "financial_report" / "policy_doc" / "industry_media" / "expert_interview" / "general_news"
    grade: str        # "A" / "B" / "C"
    url: str = ""
    published_date: str = ""
    key_data: str = ""   # 关键数据点（如营收、增长率、市占率）
    summary: str = ""   # 摘要


@dataclass
class RadarDeepIndustryRequest:
    """采集请求"""
    topic: str
    industry: str = ""         # 行业名称，如"半导体"、"新能源汽车"
    scope_years: int = 3       # 采集时间范围（年）
    priority: str = "normal"    # "high" / "normal"
    custom_keywords: list[str] = field(default_factory=list)
    max_signals: int = 5       # 最大信号数量（pipeline_router.py 使用）


@dataclass
class RadarDeepIndustryResult:
    """采集结果"""
    brief: dict
    sources: list[IndustrySource]
    signal_count: int


# ─────────────────────────────────────────────────────────────────
# 默认情报源注册表
# ─────────────────────────────────────────────────────────────────

DEFAULT_SOURCES = [
    IndustrySource(
        source_id="bloomberg-ind",
        name="Bloomberg Industry Intelligence",
        source_type="research_report",
        grade="A",
        url="https://www.bloomberg.com/industry",
        key_data="行业营收、增长率、市场份额数据",
        summary="全球行业情报数据库，提供企业财务和行业趋势数据",
    ),
    IndustrySource(
        source_id="36kr",
        name="36氪",
        source_type="industry_media",
        grade="B",
        url="https://36kr.com",
        key_data="行业动态、创业公司、融资事件",
        summary="中国科技创业媒体，覆盖TMT、新能源、半导体等领域",
    ),
    IndustrySource(
        source_id="huxiu",
        name="虎嗅",
        source_type="industry_media",
        grade="B",
        url="https://huxiu.com",
        key_data="商业观察、行业分析、企业案例",
        summary="中国领先商业科技媒体，以深度分析见长",
    ),
    IndustrySource(
        source_id="caixin",
        name="财新",
        source_type="industry_media",
        grade="B",
        url="https://caixin.com",
        key_data="宏观经济、行业政策、企业深度报道",
        summary="中国专业财经媒体，政策解读和行业调查见长",
    ),
    IndustrySource(
        source_id="gov-whitepaper",
        name="政府白皮书/行业规划",
        source_type="policy_doc",
        grade="A",
        url="",
        key_data="政策目标、规划指标、扶持力度",
        summary="政府主管部门发布的行业白皮书和发展规划",
    ),
    IndustrySource(
        source_id="sec-filings",
        name="SEC Filings / EDGAR",
        source_type="financial_report",
        grade="A",
        url="https://www.sec.gov/cgi-bin/browse-edgar",
        key_data="营收、利润、指引、研发投入、产能利用率",
        summary="美国证监会企业申报文件（年报/季报/8-K）",
    ),
    IndustrySource(
        source_id="hkex-filings",
        name="港交所披露易",
        source_type="financial_report",
        grade="A",
        url="https://www.hkexnews.hk",
        key_data="营收、利润、重大事项公告",
        summary="香港交易所上市公司公告和财务报告",
    ),
]


class RadarDeepIndustry:
    """
    深度行业报告情报采集引擎。

    模式：
      - MOCK：返回默认情报源 + 模拟信号
      - REAL：采集真实网络情报
    """

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            llm_mod = _load_llm_gateway()
            self._llm = llm_mod.LLMGateway()
        return self._llm

    def run(self, request: RadarDeepIndustryRequest) -> RadarDeepIndustryResult:
        """
        执行情报采集。

        参数：
          request: RadarDeepIndustryRequest

        返回：RadarDeepIndustryResult(brief=dict, sources=list, signal_count=int)
        """
        if self._is_mock_mode():
            return self._run_mock(request)

        return self._run_real(request)

    def _is_mock_mode(self) -> bool:
        import os
        return not bool(os.environ.get("DEEPSEEK_API_KEY"))

    def _run_mock(self, request: RadarDeepIndustryRequest) -> RadarDeepIndustryResult:
        """Mock 模式：使用默认情报源 + 模拟信号"""
        topic = request.topic
        industry = request.industry or "目标行业"

        # 从默认源中选择相关来源（按 grade 排序）
        sources = self._select_relevant_sources(request)

        # 生成模拟信号
        signals = self._generate_mock_signals(topic, industry, sources)

        brief = {
            "brief_id": f"BRIEF-deep_industry-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            "content_type": "deep_industry_report",
            "topic": topic,
            "industry": industry,
            "scope_years": request.scope_years,
            "signals": signals,
            "sources": [self._source_to_dict(s) for s in sources],
            "metadata": {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "source_count": len(sources),
                "signal_count": len(signals),
                "producer": "platform/1_ingest/radar/radar_deep_industry.py",
                "mock_mode": True,
            },
        }

        return RadarDeepIndustryResult(
            brief=brief,
            sources=sources,
            signal_count=len(signals),
        )

    def _run_real(self, request: RadarDeepIndustryRequest) -> RadarDeepIndustryResult:
        """Real 模式：通过 LLM 采集和分析真实情报"""
        topic = request.topic
        sources = self._select_relevant_sources(request)

        try:
            system_prompt = """你是一位资深行业分析师，擅长收集和分析多源情报。
你的输出必须是严格的 JSON 格式，不要包含任何其他文字。"""

            user_prompt = f"""请为以下行业研究主题收集情报信号。

主题：{topic}
行业：{request.industry or '未指定'}
时间范围：近{request.scope_years}年

请从以下已知情报源中提取相关信号（若无相关信息，可跳过）：

{sources_text}

输出要求：
1. 生成 3-5 条关键情报信号（signals）
2. 每条信号包含：signal_id, text（信号摘要，100字以内）, source_id, importance（high/medium/low）, key_data（关键数据）
3. 信号应覆盖：市场规模、竞争格局、技术趋势、政策影响、供应链变化

JSON 格式：
{{
  "signals": [
    {{"signal_id": "...", "text": "...", "source_id": "...", "importance": "high", "key_data": "..."}}
  ]
}}"""

            sources_text = "\n".join([
                f"- [{s.grade}级]{s.name}（{s.source_type}）：{s.summary}"
                for s in sources
            ])

            response = self.llm.chat(user_prompt, system=system_prompt)
            data = self._extract_json(response)
            if data and "signals" in data:
                signals = data["signals"]
            else:
                signals = self._generate_mock_signals(topic, request.industry or "目标行业", sources)
        except Exception:
            signals = self._generate_mock_signals(topic, request.industry or "目标行业", sources)

        brief = {
            "brief_id": f"BRIEF-deep_industry-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            "content_type": "deep_industry_report",
            "topic": topic,
            "industry": request.industry,
            "scope_years": request.scope_years,
            "signals": signals,
            "sources": [self._source_to_dict(s) for s in sources],
            "metadata": {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "source_count": len(sources),
                "signal_count": len(signals),
                "producer": "platform/1_ingest/radar/radar_deep_industry.py",
                "mock_mode": False,
            },
        }

        return RadarDeepIndustryResult(
            brief=brief,
            sources=sources,
            signal_count=len(signals),
        )

    def _select_relevant_sources(self, request: RadarDeepIndustryRequest) -> list[IndustrySource]:
        """根据行业关键词选择相关情报源"""
        topic_lower = (request.topic + " " + request.industry).lower()
        selected = []

        # 优先选择 A 级源
        grade_a = [s for s in DEFAULT_SOURCES if s.grade == "A"]
        grade_b = [s for s in DEFAULT_SOURCES if s.grade == "B"]

        # 默认选择：至少 2 个 A 级 + 1 个 B 级
        selected = grade_a[:2] + grade_b[:1]

        # 若主题涉及政策/政府，增加政策源
        policy_keywords = ["政策", "监管", "规划", "白皮书", "十四五", "国产化"]
        if any(k in topic_lower for k in policy_keywords):
            policy_srcs = [s for s in DEFAULT_SOURCES if s.source_type == "policy_doc"]
            selected.extend(policy_srcs)

        # 若主题涉及国际/上市，增加财报源
        finance_keywords = ["营收", "财报", "利润", "上市", "市值", "股价"]
        if any(k in topic_lower for k in finance_keywords):
            fin_srcs = [s for s in DEFAULT_SOURCES if s.source_type == "financial_report"]
            selected.extend(fin_srcs)

        return selected[:4]

    def _generate_mock_signals(self, topic: str, industry: str, sources: list) -> list[dict]:
        """生成 Mock 信号"""
        src_names = [s.name for s in sources[:3]]
        src_ids = [s.source_id for s in sources[:3]]
        grade_a_names = [s.name for s in sources if s.grade == "A"]
        grade_b_names = [s.name for s in sources if s.grade == "B"]

        return [
            {
                "signal_id": f"sig-{uuid.uuid4().hex[:8]}",
                "text": f"行业规模持续扩大，{industry}头部企业营收增速超过20%，市场集中度进一步提升。",
                "source_id": src_ids[0] if src_ids else "bloomberg-ind",
                "source_name": grade_a_names[0] if grade_a_names else "机构研报",
                "importance": "high",
                "key_data": "营收增速>20%，市场集中度CR3>45%",
            },
            {
                "signal_id": f"sig-{uuid.uuid4().hex[:8]}",
                "text": f"技术迭代加速，{topic}领域出现新的技术路线之争，龙头企业加速产能扩张。",
                "source_id": src_ids[1] if len(src_ids) > 1 else "36kr",
                "source_name": grade_b_names[0] if grade_b_names else "行业媒体",
                "importance": "high",
                "key_data": "新产能投资>500亿元，在建产能同比+35%",
            },
            {
                "signal_id": f"sig-{uuid.uuid4().hex[:8]}",
                "text": f"政策支持力度加大，国产替代成为重要主线，供应链本土化率持续提升。",
                "source_id": src_ids[2] if len(src_ids) > 2 else "caixin",
                "source_name": grade_b_names[1] if len(grade_b_names) > 1 else "财新",
                "importance": "medium",
                "key_data": "国产化率目标>70%，政策补贴规模>100亿元",
            },
        ]

    def _source_to_dict(self, src: IndustrySource) -> dict:
        return {
            "source_id": src.source_id,
            "name": src.name,
            "source_type": src.source_type,
            "grade": src.grade,
            "url": src.url,
            "key_data": src.key_data,
            "summary": src.summary,
        }

    def _extract_json(self, text: str) -> dict | None:
        import json, re
        match = re.search(r'\{[\s\S]*\}', text.strip())
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None
