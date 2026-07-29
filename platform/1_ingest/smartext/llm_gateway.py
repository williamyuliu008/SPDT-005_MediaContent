"""
SmartTextPlatform — LLM Gateway (smartext 独立版)
====================================================
DeepSeek API (OpenAI 兼容) → 6 集群统一调用

从 shared/llm_gateway.py 迁入，保持接口兼容。
原先的 shared/llm_gateway.py 保留不动，此为 smartext 独立实例。
"""

import os, json, time, logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger("smartext.gateway")

# ═══════════════════════════════════════
# LLM Gateway
# ═══════════════════════════════════════

@dataclass
class LLMResponse:
    """标准化 LLM 响应"""
    content: str
    model: str
    tokens_used: int
    latency_ms: float
    success: bool
    error: str = ""


class LLMGateway:
    """DeepSeek API 网关 — 6 集群共用"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or "https://api.deepseek.com"
        self.model = "deepseek-chat"
        self._call_count = 0
        self._total_tokens = 0
        self._total_latency = 0.0
    
    def call(self, system_prompt: str, user_prompt: str,
             max_tokens: int = 4096, temperature: float = 0.7) -> LLMResponse:
        """调用 LLM"""
        t0 = time.time()
        
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers, json=payload, timeout=60,
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                latency = (time.time() - t0) * 1000
                
                self._call_count += 1
                self._total_tokens += tokens
                self._total_latency += latency
                
                return LLMResponse(
                    content=content, model=self.model,
                    tokens_used=tokens, latency_ms=latency, success=True,
                )
            else:
                return LLMResponse(
                    content="", model=self.model, tokens_used=0,
                    latency_ms=(time.time()-t0)*1000, success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
                
        except Exception as e:
            return LLMResponse(
                content="", model=self.model, tokens_used=0,
                latency_ms=(time.time()-t0)*1000, success=False,
                error=str(e)[:200],
            )
    
    def stats(self) -> dict:
        return {
            "calls": self._call_count,
            "total_tokens": self._total_tokens,
            "avg_latency_ms": round(self._total_latency / max(1, self._call_count), 1),
        }


# ═══════════════════════════════════════
# Cluster-specific LLM Writer
# ═══════════════════════════════════════

class ClusterLLMWriter:
    """集群 LLM 写作器 — 从 YAML 配置驱动（非硬编码 prompt）"""
    
    def __init__(self, cluster_id: str, prompt_config: dict, llm: LLMGateway = None):
        self.cluster_id = cluster_id
        self.llm = llm or LLMGateway()
        self.prompt_config = prompt_config
        self._cluster_cfg = prompt_config.get("cluster", {})
        self._stages = prompt_config.get("stages", {})
    
    def write(self, structured_spec: dict, l2_config: dict = None,
              stage_context: str = "", stage_id: str = None) -> LLMResponse:
        """根据结构化规格生成内容"""
        
        # 构建 user prompt
        spec_text = json.dumps(structured_spec, ensure_ascii=False, indent=2)
        config_text = json.dumps(l2_config or {}, ensure_ascii=False)
        
        user_prompt = f"""请根据以下结构化需求生成内容：

【需求规格】
{spec_text}

【L2 配置】
{config_text}

【当前阶段】
{stage_context}

【输出格式】
{self._cluster_cfg.get('format', '')}

请严格按照上述格式输出。"""
        
        # 选择 system prompt：优先使用 stage 专用
        system_prompt = self._cluster_cfg.get("system", "你是专业的文字创作助手。")
        if stage_id and stage_id in self._stages:
            system_prompt = self._stages[stage_id].get("system", system_prompt)
        
        # 分级 max_tokens
        max_tokens = self._cluster_cfg.get("max_tokens", 4096)
        if stage_id and stage_id in self._stages:
            max_tokens = self._stages[stage_id].get("max_tokens", max_tokens)
        
        temperature = self._cluster_cfg.get("temperature", 0.7)
        
        return self.llm.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
