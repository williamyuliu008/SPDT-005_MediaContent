# -*- coding: utf-8 -*-
"""
llm_gateway.py — SPDT-005 共享 LLM 网关
=========================================

核心功能：
  1. DeepSeek API 调用封装（带重试、超时、结构化输出）
  2. 多模型支持（deepseek-chat / deepseek-coder 等）
  3. Structured Output 模式（JSON 模式）
  4. 调用日志和成本追踪
  5. Mock 模式（无 API Key 时可正常运行）

使用方式：
  gateway = LLMGateway()
  response = gateway.chat("请写一段新闻导语", model="deepseek-chat")
  structured = gateway.structured("提取关键信息", schema={...}, model="deepseek-chat")

API Key 配置（优先级）：
  1. 环境变量 DEEPSEEK_API_KEY
  2. 配置文件 platform/config/llm.yaml 的 api_key
  3. 文件路径 platform/config/.api_key
  4. 均无 → 使用 MOCK 模式（返回示例数据）
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "platform" / "config" / "llm.yaml"
API_KEY_FILE = REPO_ROOT / "platform" / "config" / ".api_key"


# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    """LLM 调用响应"""
    content: str
    model: str
    usage: dict              # {prompt_tokens, completion_tokens, total_tokens}
    latency_ms: float
    raw: Optional[dict] = None
    mock: bool = False


@dataclass
class LLMConfig:
    """LLM 配置"""
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.3
    max_tokens: int = 2048
    timeout: int = 60
    max_retries: int = 3
    mock_mode: bool = False

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "LLMConfig":
        """从配置文件和环境变量加载配置"""
        config_path = config_path or CONFIG_PATH

        # 默认配置
        cfg = cls()

        # 1. 环境变量
        env_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if env_key:
            cfg.api_key = env_key

        # 2. 配置文件
        if config_path.exists():
            try:
                data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                if data:
                    for key in ["api_key", "base_url", "model", "temperature",
                                "max_tokens", "timeout", "max_retries"]:
                        if key in data.get("llm", {}):
                            setattr(cfg, key, data["llm"][key])
                    if data.get("llm", {}).get("mock_mode"):
                        cfg.mock_mode = True
            except Exception:
                pass

        # 3. .api_key 文件
        if not cfg.api_key and API_KEY_FILE.exists():
            try:
                cfg.api_key = API_KEY_FILE.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        # 4. 判断 mock 模式
        if not cfg.api_key or cfg.api_key == "YOUR_DEEPSEEK_API_KEY":
            cfg.mock_mode = True

        return cfg


# ─────────────────────────────────────────────────────────────────
# Mock 数据（无 API Key 时返回）
# ─────────────────────────────────────────────────────────────────

BREAKING_NEWS_MOCK_INTELLIGENCE_BRIEF = {
    "header": {
        "artifact_id": "ART-INTEL-breakdown_news-20260730-MOCK001",
        "artifact_type": "intelligence_brief",
        "content_type": "breakdown_news",
        "pipeline_dimensions": {"accuracy": 4, "literary": 2, "professional_depth": 3},
        "produced_at": "2026-07-30T12:00:00Z",
        "producer": "platform/1_ingest/radar/radar_breaking.py",
        "pipeline_id": "PL-breakdown_news-MOCK001",
    },
    "signals": [
        {
            "signal_id": "SIG-001",
            "type": "breaking_signal",
            "text": "OpenAI 发布 GPT-5o，推理能力提升3倍，多模态能力大幅增强",
            "confidence": 0.95,
            "source_id": "SRC-OPENAI-001",
            "key_claims": ["GPT-5o发布", "推理能力3倍", "多模态增强"],
            "entities": ["OpenAI", "GPT-5o"],
            "topics": ["AI", "大模型", "发布"],
            "published_at": "2026-07-30T10:30:00Z",
            "url": "https://openai.com/blog/gpt-5o",
        }
    ],
    "sources": [
        {
            "source_id": "SRC-OPENAI-001",
            "grade": "A",
            "name": "OpenAI Official",
            "type": "company_report",
            "url": "https://openai.com/blog/gpt-5o",
            "accessed": "2026-07-30",
        }
    ],
    "content_type": "breakdown_news",
    "priority": 9,
    "knowledge_gaps": [],
    "recommended_angles": ["技术突破", "行业影响", "竞争格局"],
    "sla_deadline": "",
    "gray_zones": [],
}


BREAKING_NEWS_MOCK_ARTICLE_OUTLINE = {
    "header": {
        "artifact_id": "ART-OUTLINE-breakdown_news-20260730-MOCK002",
        "artifact_type": "article_outline",
        "brief_id": "ART-INTEL-breakdown_news-20260730-MOCK001",
        "content_type": "breakdown_news",
        "pipeline_dimensions": {"accuracy": 4, "literary": 2, "professional_depth": 3},
        "produced_at": "2026-07-30T12:01:00Z",
        "producer": "platform/2_structure/article/article_breaking.py",
        "pipeline_id": "PL-breakdown_news-MOCK001",
    },
    "title": "突发：OpenAI 发布 GPT-5o，推理能力提升3倍",
    "subtitle": "多模态能力大幅增强，AI 竞争格局再度生变",
    "sections": [
        {
            "section_id": "SEC-001",
            "type": "paragraph",
            "title": "导语",
            "order": 1,
            "target_words": 80,
            "keywords": ["GPT-5o", "发布", "突破"],
            "style": "客观快速",
        },
        {
            "section_id": "SEC-002",
            "type": "list",
            "title": "核心事实",
            "order": 2,
            "target_words": 150,
            "keywords": ["推理3倍", "多模态", "发布"],
            "key_claims": ["GPT-5o发布", "推理能力3倍"],
            "style": "事实密集",
        },
        {
            "section_id": "SEC-003",
            "type": "timeline",
            "title": "事件时间线",
            "order": 3,
            "target_words": 100,
            "style": "时间线",
        },
        {
            "section_id": "SEC-004",
            "type": "paragraph",
            "title": "背景",
            "order": 4,
            "target_words": 120,
            "style": "简洁背景",
        },
    ],
    "word_count_target": 450,
    "references_plan": ["SRC-OPENAI-001"],
    "terminology_plan": ["GPT-5o", "多模态", "推理能力"],
    "visual_elements_plan": ["timeline"],
}


BREAKING_NEWS_MOCK_ARTICLE_V2 = {
    "header": {
        "artifact_id": "ART-ARTICLE-breakdown_news-20260730-MOCK003",
        "artifact_type": "article_v2",
        "version": "2.0.0",
        "content_type": "breakdown_news",
        "pipeline_dimensions": {"accuracy": 4, "literary": 2, "professional_depth": 3},
        "produced_at": "2026-07-30T12:02:00Z",
        "producer": "platform/3_render/engines/text/render_breaking.py",
        "pipeline_id": "PL-breakdown_news-MOCK001",
    },
    "title": "突发：OpenAI 发布 GPT-5o，推理能力提升3倍",
    "subtitle": "多模态能力大幅增强，AI 竞争格局再度生变",
    "abstract": "",
    "word_count": 450,
    "reading_time_minutes": 1.5,
    "blocks": [
        {
            "block_id": "B001",
            "type": "paragraph",
            "content": {
                "text": "OpenAI 于今日凌晨正式发布 GPT-5o，这是该公司迄今为止最强大的推理模型。"
            },
            "depth": "surface",
            "terms": [],
            "citations": [],
        },
    ],
    "metadata": {
        "terms": [],
        "knowledge_points": [],
        "references": [],
    },
    "quality_markers": {
        "factual_claims_count": 3,
        "sources_cited_count": 1,
        "terms_defined_count": 0,
        "has_abstract": False,
        "has_references": True,
        "has_terminology_table": False,
        "literary_score": 0,
        "readability_score": 0,
    },
    "gray_zones": [],
}


# ─────────────────────────────────────────────────────────────────
# 核心网关
# ─────────────────────────────────────────────────────────────────

class LLMGateway:
    """
    SPDT-005 共享 LLM 网关

    使用方式：
      gateway = LLMGateway()
      resp = gateway.chat("请写一段导语")
      resp = gateway.structured("提取信息", schema={...})
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.load()
        self._session_id = uuid.uuid4().hex[:8]
        self._call_log: list[dict] = []

        if self.config.mock_mode:
            print(f"[LLMGateway] ⚠️  MOCK 模式（未配置 API Key），将返回示例数据")

    # ── 核心 API ────────────────────────────────────────────────

    def chat(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        标准对话调用。

        参数：
          prompt    — 用户消息
          system    — 系统提示词（可选）
          model     — 模型名（默认从 config 读取）
          temperature — 温度（默认 0.3）
          max_tokens   — 最大token数
        """
        model = model or self.config.model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        if self.config.mock_mode:
            return LLMResponse(
                content="[MOCK] 这是模拟回复。请配置 DEEPSEEK_API_KEY 以启用真实调用。",
                model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency_ms=0,
                mock=True,
            )

        import openai

        client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = time.time()
        retry_count = 0

        while retry_count <= self.config.max_retries:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                choice = response.choices[0]
                latency_ms = (time.time() - start) * 1000

                result = LLMResponse(
                    content=choice.message.content or "",
                    model=model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    latency_ms=latency_ms,
                    raw=response.model_dump(),
                )

                self._log_call(model, "chat", latency_ms, result.usage)
                return result

            except Exception as e:
                retry_count += 1
                if retry_count > self.config.max_retries:
                    raise RuntimeError(f"LLM 调用失败（{retry_count}次重试后）: {e}")
                time.sleep(2 ** retry_count)

    def structured(
        self,
        prompt: str,
        schema: dict,
        system: str = "你是一个结构化数据提取专家。请严格按照要求的 JSON Schema 输出，不要包含任何解释性文字。",
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """
        结构化输出调用（JSON Schema）。

        参数：
          prompt  — 用户消息
          schema  — JSON Schema（响应格式约束）
          system  — 系统提示词
          model   — 模型名
          temperature — 建议 0.1（降低随机性）
        """
        model = model or self.config.model

        if self.config.mock_mode:
            return LLMResponse(
                content=json.dumps(schema.get("example", {}), ensure_ascii=False),
                model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency_ms=0,
                mock=True,
            )

        import openai

        client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )

        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"{prompt}\n\n请严格按以下 JSON Schema 输出：\n```json\n{json.dumps(schema, ensure_ascii=False)}\n```",
            },
        ]

        start = time.time()

        while True:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )

                choice = response.choices[0]
                latency_ms = (time.time() - start) * 1000

                result = LLMResponse(
                    content=choice.message.content or "{}",
                    model=model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    latency_ms=latency_ms,
                    raw=response.model_dump(),
                )

                self._log_call(model, "structured", latency_ms, result.usage)
                return result

            except Exception as e:
                # 如果模型不支持 json_object，降级到普通调用后手动 JSON 解析
                if "json_object" in str(e):
                    return self.chat(
                        prompt=prompt,
                        system=system,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                raise

    # ── 辅助方法 ────────────────────────────────────────────────

    def _log_call(self, model: str, call_type: str, latency_ms: float, usage: dict):
        """记录调用日志"""
        entry = {
            "session_id": self._session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "type": call_type,
            "latency_ms": round(latency_ms, 1),
            "tokens": usage,
        }
        self._call_log.append(entry)

    def get_stats(self) -> dict:
        """获取调用统计"""
        if not self._call_log:
            return {"total_calls": 0, "mock_calls": 0, "total_tokens": 0}

        total = len(self._call_log)
        mock = sum(1 for e in self._call_log if e.get("latency_ms", 0) == 0)
        total_tokens = sum(e["tokens"].get("total_tokens", 0) for e in self._call_log)
        return {
            "total_calls": total,
            "mock_calls": mock,
            "total_tokens": total_tokens,
            "real_calls": total - mock,
        }

    def get_log(self) -> list[dict]:
        """获取完整调用日志"""
        return self._call_log.copy()
