"""
PT-047 shared.tools.llm_clients — OMAS LLM 客户端桥接 + Agent 依赖桩
优先从 OMAS SDC 加载，缺失时提供桩实现。
"""
from __future__ import annotations

# ── 桥接: 尝试从 OMAS SDC 加载真实实现 ───────────────────
try:
    import sys, os
    _omas_shared = r"D:\6_agent_project\omas\src\shared"
    if _omas_shared not in sys.path:
        sys.path.insert(0, _omas_shared)
    from tools.llm_clients import chat, chat_json, engine_status as _engine_status
    # 导出真实函数
    __all__ = ["chat", "chat_json", "engine_status", "LLMClient", "LLMResponse",
               "LLMConfig", "get_openai_client", "get_llm_client"]
except Exception:
    # Fallback: 桩实现
    import json, os
    from dataclasses import dataclass
    from typing import Any, Dict, Optional

    def chat(prompt: str, model: str = None, max_tokens: int = 4096,
             temperature: float = 0.2, preferred_engine: str = None, timeout: int = None) -> str:
        return json.dumps({"stub": True, "prompt_len": len(prompt)})

    def chat_json(prompt: str, model: str = None, max_tokens: int = 4096) -> dict:
        return {"stub": True}

    def engine_status() -> dict:
        return {"engines": {}}

    __all__ = ["chat", "chat_json", "engine_status", "LLMClient", "LLMResponse",
               "LLMConfig", "get_openai_client", "get_llm_client"]


# ── Agent 依赖桩（agents 导入但 OMAS 未提供）──────────────
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class LLMConfig:
    """LLM 配置桩。"""
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout: int = 30


@dataclass
class LLMResponse:
    """LLM 响应桩。"""
    content: str
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "success": self.success,
            "error": self.error,
        }


class LLMClient:
    """LLM 客户端桩。"""
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()

    def chat(self, prompt: str, **kwargs) -> LLMResponse:
        text = chat(prompt, model=self.config.model,
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    timeout=kwargs.get("timeout"))
        try:
            content = json.loads(text).get("content", text)
        except Exception:
            content = text
        return LLMResponse(content=content, model=self.config.model)


def get_openai_client() -> LLMClient:
    """获取 OpenAI 兼容客户端桩。"""
    return LLMClient(config=LLMConfig(model="gpt-4"))


def get_llm_client() -> LLMClient:
    """获取默认 LLM 客户端桩。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("QWEN_API_KEY", "")
    cfg = LLMConfig(api_key=api_key)
    return LLMClient(config=cfg)
