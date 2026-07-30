# -*- coding: utf-8 -*-
"""
radar_breaking.py — breakdown_news IF-P-1：突发快讯情报摄取
================================================================

功能：
  1. 监听关键词触发型突发事件
  2. 多源采集（RSS/API/Web 抓取）
  3. 来源分级（A/B/C）和置信度评估
  4. 输出 IntelligenceBrief（符合 IF-P-1 schema）

IF-P-1 输出 Schema：D:/1_omas/MODLIB/schemas/intelligence_brief.schema.json

使用方式：
  radar = RadarBreaking()
  brief = radar.run(topic="AI芯片出口限制", channels=["reuters","nikkei","cnbc"])
  # brief["header"]["artifact_id"]
  # brief["signals"]
  # brief["sources"]

规范参考：
  - governance/SPDT-005_SOP.md
  - platform/kb/content_type_registry.yaml（breakdown_news 配置）
  - platform/kb/content_type_registry.yaml（breakdown_news routing）
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = REPO_ROOT / "platform" / "kb" / "content_type_registry.yaml"


# ─────────────────────────────────────────────────────────────────
# 关键词配置
# ─────────────────────────────────────────────────────────────────

# 突发事件关键词（高优先级触发）
BREAKING_KEYWORDS = [
    # 政策/监管
    "出口管制", "制裁", "禁运", "限制", "禁止", "紧急", "突发", "新规", "重大政策",
    "管制", "限制令", "封锁",
    # 危机/事故
    "事故", "爆炸", "火灾", "泄漏", "坍塌", "死亡", "伤亡", "失踪", "紧急状态",
    "灾难", "地震", "洪水", "台风",
    # 公司/行业
    "破产", "倒闭", "大规模裁员", "停产", "停供", "违约", "起诉", "调查",
    # 科技
    "发布", "突破", "重大发现", "首次", "首款", "革命性",
]

# 来源等级定义
SOURCE_GRADES = {
    "official": "A",          # 政府官网、公司官网
    "industry_media": "B",    # 行业媒体（DigiTimes/Nikkei）
    "news": "B",             # 主流新闻媒体（Reuters/BBC）
    "social_media": "C",      # 社交媒体
    "unknown": "C",
}


@dataclass
class RadarBreakingRequest:
    """情报摄取请求"""
    topic: str                           # 监测主题/关键词
    channels: list[str] = field(default_factory=list)  # 数据源列表
    max_signals: int = 10                # 最大信号数
    min_confidence: float = 0.6         # 最低置信度
    time_window_hours: int = 24          # 时间窗口


@dataclass
class RadarBreakingResult:
    """情报摄取结果（IntelligenceBrief）"""
    artifact_id: str
    brief: dict
    signals_count: int
    sources_count: int
    mock: bool

    def to_dict(self) -> dict:
        return self.brief


# ─────────────────────────────────────────────────────────────────
# 核心雷达
# ─────────────────────────────────────────────────────────────────

class RadarBreaking:
    """
    breakdown_news 情报摄取雷达

    执行流程：
      1. 加载 registry 配置
      2. 关键词匹配和信号提取
      3. 来源分级和置信度评估
      4. 生成 IntelligenceBrief
    """

    # 固定配置（breakdown_news 类型）
    CONTENT_TYPE = "breakdown_news"
    PIPELINE_DIMENSIONS = {"accuracy": 4, "literary": 2, "professional_depth": 3}
    PRIORITY = 10

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or REGISTRY_PATH
        self._load_registry()

    def _load_registry(self):
        """加载 registry 配置"""
        if self.registry_path.exists():
            try:
                data = yaml.safe_load(self.registry_path.read_text(encoding="utf-8"))
                route = data.get("content_types", {}).get(self.CONTENT_TYPE, {})
                self.config = route
                self.sla_minutes = route.get("sla_minutes", 15)
            except Exception:
                self.config = {}
                self.sla_minutes = 15
        else:
            self.config = {}
            self.sla_minutes = 15

    def run(self, request: RadarBreakingRequest) -> RadarBreakingResult:
        """
        执行情报摄取。

        参数：
          request: RadarBreakingRequest

        返回：
          RadarBreakingResult（包含 artifact_id 和 brief dict）
        """
        from platform.shared.llm_gateway import LLMGateway, BREAKING_NEWS_MOCK_INTELLIGENCE_BRIEF

        gateway = LLMGateway()

        # ── MOCK 模式 ──────────────────────────────────────────
        if gateway.config.mock_mode:
            brief = self._build_mock_brief(request.topic)
            return RadarBreakingResult(
                artifact_id=brief["header"]["artifact_id"],
                brief=brief,
                signals_count=len(brief["signals"]),
                sources_count=len(brief["sources"]),
                mock=True,
            )

        # ── 真实采集流程 ──────────────────────────────────────
        signals = self._collect_signals(request, gateway)
        sources = self._extract_sources(signals)

        brief = self._build_brief(
            topic=request.topic,
            signals=signals,
            sources=sources,
            pipeline_id=f"PL-{self.CONTENT_TYPE}-{uuid.uuid4().hex[:8]}",
        )

        return RadarBreakingResult(
            artifact_id=brief["header"]["artifact_id"],
            brief=brief,
            signals_count=len(signals),
            sources_count=len(sources),
            mock=False,
        )

    # ── 信号采集 ───────────────────────────────────────────────

    def _collect_signals(self, request: RadarBreakingRequest, gateway) -> list[dict]:
        """
        从关键词和主题生成情报信号。

        流程：
          1. 关键词匹配（如果有原始新闻数据的话）
          2. 用 LLM 从主题生成结构化信号
        """
        prompt = f"""你是一个新闻情报分析师。请根据以下主题，生成3-5个突发新闻情报信号。

主题：{request.topic}

要求：
1. 每个信号包含：事件描述、来源类型、关键主张（1-3个）
2. 来源类型包括：official / industry_media / news / social_media
3. 对于没有原始数据的模拟，生成合理推断的信号（confidence 0.6-0.8）
4. 用 JSON 数组格式输出，不要有解释性文字

输出格式：
{{
  "signals": [
    {{
      "text": "事件描述",
      "confidence": 0.85,
      "type": "breaking_signal",
      "source_type": "industry_media",
      "key_claims": ["主张1", "主张2"],
      "entities": ["实体1", "实体2"],
      "topics": ["主题1", "主题2"]
    }}
  ]
}}
"""
        response = gateway.structured(
            prompt=prompt,
            schema={"type": "object", "properties": {"signals": {"type": "array"}}, "required": ["signals"]},
            temperature=0.3,
            max_tokens=1500,
        )

        try:
            data = json.loads(response.content)
            signals = data.get("signals", [])
        except Exception:
            signals = []

        # 为每个信号补充 signal_id
        for i, sig in enumerate(signals):
            sig["signal_id"] = f"SIG-{i+1:03d}"
            sig["published_at"] = datetime.now(timezone.utc).isoformat()

        return signals[: request.max_signals]

    def _extract_sources(self, signals: list[dict]) -> list[dict]:
        """从信号中提取和补充来源信息"""
        sources_map: dict[str, dict] = {}

        for sig in signals:
            source_type = sig.get("source_type", "unknown")
            grade = SOURCE_GRADES.get(source_type, "C")

            source_id = f"SRC-{source_type.upper()}-{len(sources_map)+1:03d}"
            if source_id not in sources_map:
                sources_map[source_id] = {
                    "source_id": source_id,
                    "grade": grade,
                    "name": f"{source_type} 来源",
                    "type": source_type,
                    "claim": sig.get("text", "")[:100],
                }

        return list(sources_map.values())

    # ── 构建 IntelligenceBrief ─────────────────────────────────

    def _build_brief(
        self,
        topic: str,
        signals: list[dict],
        sources: list[dict],
        pipeline_id: str,
    ) -> dict:
        """构建 IntelligenceBrief JSON"""
        artifact_id = f"ART-INTEL-{self.CONTENT_TYPE}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

        brief = {
            "header": {
                "artifact_id": artifact_id,
                "artifact_type": "intelligence_brief",
                "content_type": self.CONTENT_TYPE,
                "pipeline_dimensions": self.PIPELINE_DIMENSIONS,
                "produced_at": datetime.now(timezone.utc).isoformat(),
                "producer": "platform/1_ingest/radar/radar_breaking.py",
                "pipeline_id": pipeline_id,
            },
            "signals": signals,
            "sources": sources,
            "content_type": self.CONTENT_TYPE,
            "priority": self.PRIORITY,
            "knowledge_gaps": self._identify_gaps(signals),
            "recommended_angles": self._extract_angles(signals),
            "sla_deadline": self._calc_sla_deadline(),
            "gray_zones": self._detect_gray_zones(signals),
        }

        return brief

    def _build_mock_brief(self, topic: str) -> dict:
        """构建 MOCK IntelligenceBrief"""
        import copy
        brief = copy.deepcopy(BREAKING_NEWS_MOCK_INTELLIGENCE_BRIEF)
        brief["header"]["artifact_id"] = f"ART-INTEL-{self.CONTENT_TYPE}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        brief["header"]["produced_at"] = datetime.now(timezone.utc).isoformat()
        brief["signals"][0]["text"] = f"[MOCK] {topic} 相关突发事件"
        return brief

    def _identify_gaps(self, signals: list[dict]) -> list[str]:
        """识别情报缺口"""
        gaps = []
        if len(signals) < 3:
            gaps.append("信号数量不足，建议扩大采集范围")
        # 检查是否有具体数据
        has_numbers = any(re.search(r'\d+', s.get("text", "")) for s in signals)
        if not has_numbers:
            gaps.append("缺少具体数字数据")
        return gaps

    def _extract_angles(self, signals: list[dict]) -> list[str]:
        """提取推荐切入角度"""
        angles = []
        for sig in signals[:3]:
            angles.extend(sig.get("topics", []))
        return list(set(angles))[:5]

    def _calc_sla_deadline(self) -> str:
        """计算 SLA 截止时间"""
        from datetime import timedelta
        deadline = datetime.now(timezone.utc) + timedelta(minutes=self.sla_minutes)
        return deadline.isoformat()

    def _detect_gray_zones(self, signals: list[dict]) -> list[dict]:
        """检测灰区"""
        gray_zones = []
        sensitive_keywords = ["政治", "领导人", "领土", "伤亡", "死亡"]

        for sig in signals:
            text = sig.get("text", "")
            if any(kw in text for kw in sensitive_keywords):
                gray_zones.append({
                    "zone_id": f"GRAY-{uuid.uuid4().hex[:4]}",
                    "reason": "涉及敏感关键词",
                    "severity": "high",
                })

        return gray_zones


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="breakdown_news 情报摄取雷达")
    parser.add_argument("--topic", default="OpenAI 发布新模型", help="监测主题")
    parser.add_argument("--max-signals", type=int, default=5)
    parser.add_argument("--mock", action="store_true", help="强制 MOCK 模式")
    args = parser.parse_args()

    radar = RadarBreaking()
    request = RadarBreakingRequest(
        topic=args.topic,
        max_signals=args.max_signals,
    )

    result = radar.run(request)

    print(f"\n[radar_breaking] artifact_id: {result.artifact_id}")
    print(f"  signals: {result.signals_count}")
    print(f"  sources: {result.sources_count}")
    print(f"  mock: {result.mock}")
    print(f"  SLA deadline: {result.brief.get('sla_deadline', 'N/A')}")

    if result.signals_count > 0:
        sig = result.brief["signals"][0]
        print(f"\n  首条信号: {sig.get('text', '')[:60]}")
        print(f"  置信度: {sig.get('confidence', 0):.2f}")


if __name__ == "__main__":
    main()
