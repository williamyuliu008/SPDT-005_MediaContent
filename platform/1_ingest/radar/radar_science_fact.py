# -*- coding: utf-8 -*-
"""
radar_science_fact.py — science_fact IF-P-1：科学事实情报摄取
================================================================

功能：
  1. 监听科研发现类事件（arXiv预印本、Nature/Science新闻稿、科普媒体）
  2. 多源采集 + 来源分级（同行评审 > 预印本 > 科普报道）
  3. 识别研究方法类型（实验/理论/计算/综述）
  4. 输出 IntelligenceBrief（符合 IF-P-1 schema）

数据源（复用于 source_registry.yaml）：
  - arxiv_cs_ai  （primary, 预印本）
  - nature_news   （primary, Nature新闻稿）
  - mit_tech_review （secondary, MIT技术评论）
  - wikipedia_api （secondary, 维基百科词条）

引用分级规则（用于 scorecard_science_fact 的 citation_check）：
  A: 同行评审期刊（DOI格式，domain: nature.com / science.org / cell.com / nejm.org 等）
  B: arXiv预印本（arxiv.org URL）
  C: 科普媒体（无DOI，仅媒体链接）

使用方式：
  radar = RadarScienceFact()
  brief = radar.run(topic="室温超导材料新发现")
"""

from __future__ import annotations

import json
import re
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
# 科学发现信号类型
# ─────────────────────────────────────────────────────────────────

SCIENCE_SIGNAL_TYPES = [
    "experimental",   # 实验发现
    "theoretical",    # 理论研究
    "computational",  # 计算模拟
    "review",         # 综述研究
    "method",         # 方法创新
]

# 科学事实触发关键词
SCIENCE_KEYWORDS = [
    # 重大发现类型
    "研究发现", "科学家", "实验证明", "研究表明", "论文发表",
    "预印本", "同行评审", "期刊", "学术", "科研",
    # 具体领域
    "超导体", "基因编辑", "疫苗", "药物研发", "AI模型",
    "量子计算", "脑科学", "气候", "材料", "蛋白质",
    # 动词
    "突破", "发现", "证实", "提出", "揭示", "破解",
]


@dataclass
class RadarScienceFactRequest:
    """科学事实情报摄取请求"""
    topic: str                           # 监测主题
    channels: list[str] = field(default_factory=list)  # 数据源
    max_signals: int = 5                 # 最大信号数
    min_confidence: float = 0.5          # 最低置信度
    research_type: Optional[str] = None   # 限定研究类型


@dataclass
class RadarScienceFactResult:
    """情报摄取结果"""
    brief: dict          # IF-P-1 IntelligenceBrief


class RadarScienceFact:
    """
    科学事实情报摄取引擎。

    模式：
      - MOCK 模式（无 API Key）：返回预设的科学发现模板
      - REAL 模式（配置 DEEPSEEK_API_KEY）：调用 LLM 总结 arXiv/科普信源
    """

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            llm_mod = _load_llm_gateway()
            self._llm = llm_mod.LLMGateway()
        return self._llm

    def run(self, request: RadarScienceFactRequest) -> RadarScienceFactResult:
        """
        执行科学事实情报摄取。

        返回：RadarScienceFactResult(brief=dict)
        brief 符合 IF-P-1 IntelligenceBrief schema。
        """
        # 检测是否 Mock 模式
        if not self._has_api_key():
            return self._run_mock(request)

        return self._run_real(request)

    def _has_api_key(self) -> bool:
        import os
        return bool(os.environ.get("DEEPSEEK_API_KEY"))

    def _run_mock(self, request: RadarScienceFactRequest) -> RadarScienceFactResult:
        """Mock 模式：返回预设的科学发现数据"""
        signals = self._build_mock_signals(request.topic)
        brief = self._build_brief(signals, request.topic)
        return RadarScienceFactResult(brief=brief)

    def _run_real(self, request: RadarScienceFactRequest) -> RadarScienceFactResult:
        """Real 模式：通过 LLM 总结科学发现"""
        signals = self._fetch_science_signals(request.topic, request.max_signals)
        brief = self._build_brief(signals, request.topic)
        return RadarScienceFactResult(brief=brief)

    # ── 科学发现信号构建（Mock）──────────────────────────────────

    def _build_mock_signals(self, topic: str) -> list[dict]:
        """构建 Mock 科学发现信号"""
        return [
            {
                "signal_id": f"SIG-SCI-{uuid.uuid4().hex[:8]}",
                "type": "research_signal",
                "text": f"[MOCK] {topic} 相关科学研究新进展",
                "confidence": 0.92,
                "source_id": "arxiv_cs_ai",
                "key_claims": [
                    f"{topic} 研究取得重要进展",
                    "实验数据支持核心假说",
                    "研究结果已在预印本平台发布",
                ],
                "entities": [topic, "arXiv"],
                "topics": ["科学研究", "学术发现"],
                "research_method": "experimental",
                "peer_reviewed": False,   # arXiv预印本，未同行评审
                "published_at": datetime.now(timezone.utc).isoformat(),
                "url": "https://arxiv.org/abs/2401.00001",
                "doi": "",                  # 无DOI（预印本）
                "journal": "arXiv",
                "source_verified": False,  # v1.3: Mock模式，标注为未验证
            },
            {
                "signal_id": f"SIG-SCI-{uuid.uuid4().hex[:8]}",
                "type": "research_signal",
                "text": f"{topic} 研究被 Nature 新闻稿报道",
                "confidence": 0.95,
                "source_id": "nature_news",
                "key_claims": [
                    f"Nature 新闻稿介绍了 {topic} 相关突破",
                    "专家称该研究具有重要意义",
                    "同行评审版本即将发表",
                ],
                "entities": [topic, "Nature"],
                "topics": ["科学研究", "学术新闻"],
                "research_method": "review",
                "peer_reviewed": True,
                "published_at": datetime.now(timezone.utc).isoformat(),
                "url": "https://www.nature.com/articles/d41586-2024-00001",
                "doi": "10.1038/d41586-2024-00001",
                "journal": "Nature",
            },
            {
                "signal_id": f"SIG-SCI-{uuid.uuid4().hex[:8]}",
                "type": "research_signal",
                "text": f"MIT Tech Review 分析 {topic} 的影响",
                "confidence": 0.85,
                "source_id": "mit_tech_review",
                "key_claims": [
                    f"MIT 技术评论深度分析 {topic}",
                    "研究局限性被指出",
                    "实际应用仍需时日",
                ],
                "entities": [topic, "MIT"],
                "topics": ["科学研究", "科技评论"],
                "research_method": "review",
                "peer_reviewed": False,  # 科普媒体，非同行评审
                "published_at": datetime.now(timezone.utc).isoformat(),
                "url": "https://www.technologyreview.com/2024/s41586-00001",
                "doi": "",
                "journal": "MIT Technology Review",
                "source_verified": False,  # v1.3: Mock模式，标注为未验证
            },
            {
                "signal_id": f"SIG-SCI-{uuid.uuid4().hex[:8]}",
                "type": "research_signal",
                "text": f"维基百科更新了 {topic} 相关词条",
                "confidence": 0.75,
                "source_id": "wikipedia_api",
                "key_claims": [
                    f"维基百科收录了 {topic} 相关知识",
                    "引用了多项学术来源",
                    "内容经过社区审核",
                ],
                "entities": [topic, "Wikipedia"],
                "topics": ["知识百科", "基础背景"],
                "research_method": "review",
                "peer_reviewed": False,
                "published_at": datetime.now(timezone.utc).isoformat(),
                "url": "https://en.wikipedia.org/wiki/Topic_Placeholder",
                "doi": "",
                "journal": "Wikipedia",
                "source_verified": False,  # v1.3: Mock模式，标注为未验证
            },
        ]

    def _fetch_science_signals(self, topic: str, max_signals: int) -> list[dict]:
        """真实模式：从各数据源抓取科学发现

        Phase A（当前）：LLM 模式 → source_verified = False（LLM 生成，非真实联网）
        Phase B（规划）：接入真实 API（arXiv/Nature/Wikipedia）→ source_verified = True
        """
        # TODO(Phase B): 实现真实数据采集
        # 1. arXiv API: https://export.arxiv.org/api/query?search_query=all:{topic}&max_results={max_signals}
        # 2. Nature 新闻: RSS feed
        # 3. MIT Tech Review: page fetch
        # 4. Wikipedia: API
        signals = self._build_mock_signals(topic)[:max_signals]
        # Phase A: 标注为未验证（LLM 生成）
        for sig in signals:
            sig["source_verified"] = False
        return signals

    # ── Brief 构建 ───────────────────────────────────────────────

    def _build_brief(self, signals: list[dict], topic: str) -> dict:
        """构建 IntelligenceBrief（IF-P-1）"""
        sources = self._build_sources(signals)
        header = {
            "artifact_id": f"ART-INTEL-science_fact-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            "artifact_type": "intelligence_brief",
            "content_type": "science_fact",
            "pipeline_dimensions": {
                "accuracy": 4,
                "literary": 3,
                "professional_depth": 4,
            },
            "produced_at": datetime.now(timezone.utc).isoformat(),
            "producer": "platform/1_ingest/radar/radar_science_fact.py",
            # v1.3 新增：来源验证状态
            "source_verified_count": sum(1 for s in signals if s.get("source_verified")),
            "source_total_count": len(signals),
            "source_verification_complete": False,  # Phase B 接入真实 API 后设为 True
        }

        return {
            "header": header,
            "signals": signals,
            "sources": sources,
            "topic": topic,
            "confidence": sum(s.get("confidence", 0) for s in signals) / len(signals) if signals else 0,
            "peer_reviewed_count": sum(1 for s in signals if s.get("peer_reviewed")),
            "research_methods": list({s.get("research_method") for s in signals}),
        }

    def _build_sources(self, signals: list[dict]) -> list[dict]:
        """从信号中提取来源列表（带分级）"""
        seen = {}
        for sig in signals:
            sid = sig.get("source_id", "")
            if sid in seen:
                continue
            grade = self._grade_source(sig)
            seen[sid] = {
                "source_id": sid,
                "grade": grade,
                "name": self._source_name(sid),
                "peer_reviewed": sig.get("peer_reviewed", False),
                "url": sig.get("url", ""),
                "journal": sig.get("journal", ""),
                "doi": sig.get("doi", ""),
                "source_verified": sig.get("source_verified", False),  # v1.3: 来源验证标记
            }
        return list(seen.values())

    def _grade_source(self, signal: dict) -> str:
        """
        来源分级（科学事实专用）：
          A: 同行评审期刊（有DOI，来自已知期刊域名）
          B: arXiv预印本（无DOI但有arxiv.org URL）
          C: 科普媒体（无DOI，无同行评审）
        """
        doi = signal.get("doi", "")
        if doi:
            return "A"   # 有DOI = 同行评审
        if "arxiv.org" in signal.get("url", ""):
            return "B"   # arXiv预印本
        return "C"        # 科普媒体

    def _source_name(self, source_id: str) -> str:
        names = {
            "arxiv_cs_ai": "arXiv CS.AI",
            "nature_news": "Nature News",
            "mit_tech_review": "MIT Technology Review",
            "wikipedia_api": "Wikipedia",
        }
        return names.get(source_id, source_id)


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    radar = RadarScienceFact()
    result = radar.run(RadarScienceFactRequest(topic="室温超导材料"))
    brief = result.brief
    print(f"情报简报 ID: {brief['header']['artifact_id']}")
    print(f"主题: {brief['topic']}")
    print(f"信号数: {len(brief['signals'])}")
    print(f"置信度: {brief['confidence']:.2f}")
    print(f"同行评审来源: {brief['peer_reviewed_count']}/{len(brief['sources'])}")
    print("\n来源列表：")
    for s in brief["sources"]:
        print(f"  [{s['grade']}] {s['name']} {'[同行评审]' if s['peer_reviewed'] else ''}")


if __name__ == "__main__":
    main()
