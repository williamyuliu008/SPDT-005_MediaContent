"""GroupArmy LLM Gateway — DeepSeek API"""
import json, urllib.request, os

API_KEY = open(r'D:\5_know\deepseek_api.txt').read().strip()
API_URL = "https://api.deepseek.com/v1/chat/completions"

def generate(prompt: str, system: str = "", max_tokens: int = 2048, temperature: float = 0.7) -> str:
    """Call DeepSeek API"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    data = json.dumps({
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode('utf-8')
    
    req = urllib.request.Request(API_URL, data=data, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    })
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        return result['choices'][0]['message']['content']

# Cluster-specific system prompts
SYSTEM_PROMPTS = {
    'A': "你是一个专业的财经新闻记者。撰写简洁、准确、信息密集的快讯。",
    'B': "你是一个资深的行业分析师。撰写深度、数据驱动、逻辑严谨的分析报告。",
    'C': "你是一个创意营销专家。撰写有吸引力、有转化力的营销文案。",
    'D': "你是一个技术文档工程师。撰写清晰、准确、结构化的技术文档。",
    'E': "你是一个科学传播者。用通俗易懂的语言和生动的类比解释复杂概念。",
    'F': "你是一个评论家和观点作家。撰写有深度、有批判性、论证充分的观点文章。",
}

def generate_for_cluster(cluster_id: str, prompt: str, spec: dict = None) -> str:
    """为特定集群生成内容"""
    system = SYSTEM_PROMPTS.get(cluster_id, SYSTEM_PROMPTS['B'])
    max_tokens = {
        'A': 500, 'B': 4096, 'C': 1024, 'D': 2048, 'E': 2048, 'F': 2048
    }.get(cluster_id, 2048)
    
    return generate(prompt, system=system, max_tokens=max_tokens)
