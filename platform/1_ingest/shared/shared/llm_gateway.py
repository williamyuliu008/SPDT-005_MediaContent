"""
SmartTextPlatform Phase 2 — LLM Gateway
=========================================
DeepSeek API (OpenAI 兼容) → 6 集群统一调用
"""

import os, json, time, logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger("llm_gateway")

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
# Cluster-specific LLM Prompts
# ═══════════════════════════════════════

CLUSTER_PROMPTS = {
    "flashnews": {
        "system": "你是专业财经快讯写手。输出简洁、准确、信息密度高的快讯，≤300字。只写事实，不写观点。",
        "format": "快讯格式：标题(≤20字) + 正文(3-5句)",
    },
    "deepprod": {
        "system": "你是资深行业分析师。输出深度、结构化、数据驱动的分析报告。引用来源，标注数据出处。",
        "format": "报告格式：执行摘要→产业链全景→技术分析→竞争格局→风险评估→投资建议",
    },
    "techdoc": {
        "system": "你是技术文档工程师。输出精确、结构化、含代码示例的技术文档。Markdown 格式。",
        "format": "文档格式：概述→安装→API参考→示例→错误码→FAQ",
    },
    "creativex": {
        "system": "你是资深创意文案。输出吸引眼球、转化率高的营销文案。多版本输出供选择。",
        "format": "文案格式：标题→痛点→解决方案→行动号召",
    },
    "scipop": {
        "system": "你是科学传播者。用通俗语言解释复杂概念，善用类比和故事。面向非专业读者。",
        "format": "科普格式：引入(类比)→核心概念→展开解释→总结",
    },
    "oped": {
        "system": "你是观点评论员。输出有深度、有论证、包含正反方对比的观点文章。",
        "format": "观点格式：论点→正方论据→反方论据→综合判断",
    },
}


class ClusterLLMWriter:
    """集群 LLM 写作器 — 每个集群专用"""
    
    def __init__(self, cluster_id: str, llm: LLMGateway = None):
        self.cluster_id = cluster_id
        self.llm = llm or LLMGateway()
        self.prompt_config = CLUSTER_PROMPTS.get(cluster_id, CLUSTER_PROMPTS["deepprod"])
    
    def write(self, structured_spec: dict, l2_config: dict = None,
              stage_context: str = "") -> LLMResponse:
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
{self.prompt_config['format']}

请严格按照上述格式输出。"""
        
        max_tokens = 4096
        if self.cluster_id == "deepprod":
            max_tokens = 8192  # 深度报告需要更长
        elif self.cluster_id == "flashnews":
            max_tokens = 1024  # 快讯很短
        
        return self.llm.call(
            system_prompt=self.prompt_config["system"],
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.7,
        )


# ═══════════════════════════════════════
# CLI Test
# ═══════════════════════════════════════

def main():
    print("=" * 60)
    print("  SmartTextPlatform Phase 2 — LLM Gateway")
    print("=" * 60)
    
    # Test without API key (demonstrate prompt building)
    for cluster_id in CLUSTER_PROMPTS:
        writer = ClusterLLMWriter(cluster_id)
        spec = {
            "core_intent": "测试意图",
            "product_type": "测试",
            "depth": "短篇",
        }
        print(f"\n  [{cluster_id}] Prompt config:")
        print(f"    System: {writer.prompt_config['system'][:60]}...")
        print(f"    Format: {writer.prompt_config['format'][:60]}...")
    
    print(f"\n{'=' * 60}")
    print("  LLM Gateway ready for API key configuration")
    print("  Set DEEPSEEK_API_KEY to enable actual generation")
    print("=" * 60)


if __name__ == "__main__":
    main()
