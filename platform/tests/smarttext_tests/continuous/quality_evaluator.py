"""
SmartTextPlatform — 文字质量深度评估器
=========================================
对集群产出的文字进行多维度质量评估。
当有 API key 时，用 LLM 做裁判评估；
无 API key 时，用启发式规则评估。
"""

import sys, os, json, re
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))

# ═══════════════════════════════════════
# 评估维度定义
# ═══════════════════════════════════════

DIMENSIONS = {
    "relevance": {
        "name": "相关性",
        "weight": 0.25,
        "description": "内容与输入需求的匹配程度",
    },
    "completeness": {
        "name": "完整性",
        "weight": 0.20,
        "description": "是否覆盖了需求中的所有要点",
    },
    "structure": {
        "name": "结构性",
        "weight": 0.15,
        "description": "内容组织是否清晰、有层次",
    },
    "style_adherence": {
        "name": "风格符合度",
        "weight": 0.15,
        "description": "体裁和语气是否符合集群要求",
    },
    "readability": {
        "name": "可读性",
        "weight": 0.15,
        "description": "文本是否流畅、易懂、无冗余",
    },
    "originality": {
        "name": "原创性",
        "weight": 0.10,
        "description": "是否避免模板化、有独特视角",
    },
}

# ═══════════════════════════════════════
# 启发式评估器 (无 LLM 时)
# ═══════════════════════════════════════

class HeuristicEvaluator:
    """基于规则的文字质量评估"""
    
    def evaluate(self, content: str, spec: dict, cluster_id: str) -> dict:
        scores = {}
        
        # 相关性: 检查核心意图关键词是否出现
        intent = spec.get("core_intent", "")
        intent_keywords = self._extract_keywords(intent)
        if intent_keywords:
            hits = sum(1 for kw in intent_keywords if kw.lower() in content.lower())
            scores["relevance"] = min(100, int(hits / max(1, len(intent_keywords)) * 100))
        else:
            scores["relevance"] = 70
        
        # 完整性: 内容长度 + 结构元素
        has_title = bool(re.search(r'^#+\s', content, re.MULTILINE))
        has_paragraphs = content.count('\n\n') >= 2
        has_list = bool(re.search(r'^[\d\-\*]\s', content, re.MULTILINE))
        has_conclusion = any(kw in content[-300:] for kw in ["总结", "结论", "建议", "展望"])
        
        completeness_markers = [has_title, has_paragraphs, has_list, has_conclusion]
        scores["completeness"] = int(sum(completeness_markers) / len(completeness_markers) * 100)
        
        # 结构性: 段落分隔 + 标题层级
        h1_count = len(re.findall(r'^#\s', content, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s', content, re.MULTILINE))
        if h1_count > 0 and h2_count >= 2:
            scores["structure"] = 90
        elif h1_count > 0 or h2_count >= 1:
            scores["structure"] = 70
        elif has_paragraphs:
            scores["structure"] = 50
        else:
            scores["structure"] = 30
        
        # 风格符合度: 按集群类型的特征词检测
        style_keywords = {
            "flashnews": ["涨", "跌", "点", "%", "成交", "指数"],
            "deepprod": ["分析", "数据", "趋势", "市场", "行业", "建议"],
            "techdoc": ["安装", "配置", "参数", "API", "接口", "示例"],
            "creativex": ["限时", "优惠", "立即", "点击", "了解", "发现"],
            "scipop": ["比如", "就像", "想象", "简单", "理解", "原理"],
            "oped": ["认为", "然而", "但是", "应该", "必须", "如果"],
        }
        expected = style_keywords.get(cluster_id, [])
        if expected:
            hits = sum(1 for kw in expected if kw in content)
            scores["style_adherence"] = min(100, int(hits / max(1, len(expected)) * 100))
        else:
            scores["style_adherence"] = 60
        
        # 可读性: 句子长度、段落长度
        sentences = re.split(r'[。！？\n]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            avg_sentence_len = sum(len(s) for s in sentences) / len(sentences)
            if 15 <= avg_sentence_len <= 80:
                scores["readability"] = 90
            elif 10 <= avg_sentence_len <= 120:
                scores["readability"] = 70
            else:
                scores["readability"] = 50
        else:
            scores["readability"] = 40
        
        # 原创性: 检测是否重复/模板化
        unique_chars = len(set(content)) / max(1, len(content))
        if unique_chars > 0.4:
            scores["originality"] = 85
        elif unique_chars > 0.3:
            scores["originality"] = 60
        else:
            scores["originality"] = 40
        
        # mock 检测
        if "Mock content" in content or "[mock]" in content.lower():
            scores["originality"] = 10
        
        # 加权综合
        overall = sum(scores.get(k, 0) * v["weight"] for k, v in DIMENSIONS.items())
        scores["overall"] = round(overall)
        
        return scores
    
    def _extract_keywords(self, text: str) -> list:
        """从文本提取关键词"""
        # 简单分词 + 过滤停用词
        stopwords = {"的", "了", "是", "在", "和", "与", "或", "对", "从", "到", 
                     "为", "等", "及", "向", "以", "中", "上", "下", "关于",
                     "一篇", "一个", "一", "需要", "要求", "进行"}
        chars = '，。！？、；：""''（）【】《》\n\r'
        for c in chars:
            text = text.replace(c, ' ')
        words = [w for w in text.split() if len(w) >= 2 and w not in stopwords]
        return list(set(words))[:10]


# ═══════════════════════════════════════
# LLM 评估器 (有 API key 时)
# ═══════════════════════════════════════

class LLMEvaluator:
    """使用 LLM 做裁判评估文字质量"""
    
    def __init__(self):
        from shared.llm_gateway import LLMGateway
        self.llm = LLMGateway()
        self.available = bool(self.llm.api_key)
    
    def evaluate(self, content: str, spec: dict, cluster_id: str) -> dict:
        if not self.available:
            return HeuristicEvaluator().evaluate(content, spec, cluster_id)
        
        intent = spec.get("core_intent", "")
        product_type = spec.get("product_type", "")
        audience = spec.get("target_audience", "")
        
        eval_prompt = f"""你是一个文字质量评审专家。请对以下 AI 生成的文字内容进行多维度评分。

【创作需求】
- 核心意图: {intent}
- 产品类型: {product_type}
- 目标受众: {audience}
- 所属集群: {cluster_id}

【评审维度】(每项0-100分)

1. 相关性(25%): 内容是否紧扣需求意图，有无偏题
2. 完整性(20%): 是否覆盖了需求中的各项要点
3. 结构性(15%): 组织是否清晰，层次是否分明
4. 风格符合度(15%): 体裁和语气是否符合该集群的定位
5. 可读性(15%): 表达是否流畅易懂，有无冗余
6. 原创性(10%): 是否避免了模板化表达，有独特视角

【待评审内容】
{content[:3000]}

请以 JSON 格式输出评分和简要理由:
{{"relevance": 分, "completeness": 分, "structure": 分, "style_adherence": 分, "readability": 分, "originality": 分, "overall": 分, "comment": "一句话总结"}}"""
        
        resp = self.llm.call(
            system_prompt="你是专业的文字质量评审专家。只输出JSON，不要输出其他内容。",
            user_prompt=eval_prompt,
            max_tokens=500,
            temperature=0.3,
        )
        
        if resp.success:
            try:
                return json.loads(resp.content)
            except json.JSONDecodeError:
                pass
        
        return HeuristicEvaluator().evaluate(content, spec, cluster_id)


# ═══════════════════════════════════════
# 批量评估
# ═══════════════════════════════════════

def evaluate_batch(cases_with_content: list, use_llm: bool = None) -> list:
    """对一批生成内容进行质量评估"""
    if use_llm is None:
        from shared.llm_gateway import LLMGateway
        use_llm = bool(LLMGateway().api_key)
    
    evaluator = LLMEvaluator() if use_llm else HeuristicEvaluator()
    
    results = []
    for case in cases_with_content:
        scores = evaluator.evaluate(
            case["content"], 
            case.get("spec", {}).get("structured_spec", {}),
            case.get("cluster", ""),
        )
        results.append({
            "id": case.get("id", ""),
            "cluster": case.get("cluster", ""),
            "label": case.get("label", ""),
            "scores": scores,
        })
    
    return results


def main():
    print("=" * 60)
    print("  SmartTextPlatform — 文字质量评估器")
    print("=" * 60)
    
    evaluator = HeuristicEvaluator()
    
    # 测试用例
    test_content = "# 测试标题\n\n这是一段测试内容，用于验证质量评估器。\n\n## 第二部分\n\n内容包含多个段落。"
    test_spec = {"core_intent": "测试内容生成"}
    
    scores = evaluator.evaluate(test_content, test_spec, "deepprod")
    
    print("\n  评估结果:")
    for dim, info in DIMENSIONS.items():
        score = scores.get(dim, 0)
        bar = "█" * (score // 10) + "░" * (10 - score // 10)
        print(f"    {info['name']:<10} [{bar}] {score}")
    
    print(f"\n    综合评分: {scores.get('overall', 0)}/100")
    print(f"\n  可用 LLM 评估: {LLMEvaluator().available}")
    print("=" * 60)


if __name__ == "__main__":
    main()
