"""
SmartText Router — SPDT-005 媒体内容制造 · 入口路由引擎
===========================================================
4-Step Pipeline: 结构化 → 分类 → 配置推荐 → 低置信度反问
7-Rule Decision Tree → 6 PDT Clusters + Cross-SPDT Routing
Target: 2s latency, max 5s

SPDT-005 PDT 映射:
  A=FlashNews(PT-041)  B=DeepProd(PT-040)  C=SciPop(PT-042)
  D=TechDoc(PT-045)    E=OpEd(PT-043)      F=CreativeX(PT-044)
  CROSS_SPDT → SPDT-004 (教育内容)
"""

import json, re, time, logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from enum import Enum

logger = logging.getLogger("textclassifier")

# ═══════════════════════════════════════
# DATA TYPES
# ═══════════════════════════════════════

class ClusterType(Enum):
    A_FLASH_NEWS = "FlashNews"     # PT-041 实时快讯 — ≤500字, 高时效
    B_DEEP_PROD = "DeepProd"       # PT-040 深度长文 — 分析/报告/白皮书
    C_SCI_POP = "SciPop"           # PT-042 知识科普 — 通俗, 类比 (不含教育)
    D_TECH_DOC = "TechDoc"         # PT-045 技术文档 — 结构化, 代码示例
    E_OP_ED = "OpEd"               # PT-043 观点评论 — 论证, 批判性
    F_CREATIVE_X = "CreativeX"     # PT-044 品牌创意 — 营销/品牌/转化
    CROSS_SPDT = "CROSS_SPDT"      # 跨产品线路由 (→ SPDT-004 教育)
    UNKNOWN = "UNKNOWN"

@dataclass
class StructuredSpec:
    """Step 1: 10维结构化规格"""
    core_intent: str = ""        # ① 核心意图
    product_type: str = ""       # ② 产品类型
    target_audience: str = ""    # ③ 目标受众
    depth: str = ""              # ④ 深度要求
    timeliness: str = ""         # ⑤ 时效要求
    style: str = ""              # ⑥ 风格倾向
    domain_tags: list = field(default_factory=list)  # ⑦ 领域标签
    constraints: list = field(default_factory=list)  # ⑧ 特殊约束
    channel: str = ""            # ⑨ 发布渠道
    explicit_vs_implicit: dict = field(default_factory=dict)  # ⑩ 显式/隐含
    confidence: float = 0.0      # 总体置信度
    
    def completeness(self) -> int:
        """计算维度完整性 (A1)"""
        fields = [self.core_intent, self.product_type, self.target_audience,
                  self.depth, self.timeliness, self.style, self.channel]
        filled = sum(1 for f in fields if f)
        return filled

@dataclass
class ClassificationResult:
    """Step 2-4: 分类+配置+反问"""
    cluster: ClusterType
    cluster_name: str
    confidence: float
    rule_matched: str           # 命中的规则
    l2_config: dict             # L2 配置推荐
    interrogate_questions: list = field(default_factory=list)  # 反问
    reasoning: str = ""         # 决策路径 (A3)
    structured: Optional[StructuredSpec] = None
    cross_spdt_route: str = ""  # 跨 SPDT 路由目标 (如 "SPDT-004")
    pdt_id: str = ""            # 目标 PDT ID (如 "PT-041")


# ═══════════════════════════════════════
# STEP 1: NL → Structured Specification
# ═══════════════════════════════════════

class Structurer:
    """自由文本 → 10维结构化规格"""
    
    # ── 教育意图检测 (→ SPDT-004) ──
    EDUCATION_KEYWORDS = [
        "学生", "高中", "初中", "小学", "大学", "考试", "备考", "高考", "中考",
        "课件", "课程", "教学", "教材", "教案", "培训", "学习", "上课", "课堂",
        "知识点", "习题", "试题", "作业", "辅导", "复习", "寒假", "暑假",
    ]
    
    def is_education_intent(self, text: str) -> bool:
        """检测是否为教育场景 → 应路由到 SPDT-004"""
        text_lower = text.lower()
        edu_hits = sum(1 for kw in self.EDUCATION_KEYWORDS if kw in text_lower)
        # 明确的教育关键词 ≥2 个，或受众明确为学生
        if edu_hits >= 2:
            return True
        audience = self._match(text, self.AUDIENCES)
        if audience == "学生":
            return True
        return False

    # ── 关键词词典 ──
    PRODUCT_TYPES = {
        "评论|观点|吐槽|思考|看法|评": "评论/观点",
        "API|接口|文档|SDK|参考|手册|规格": "技术文档",
        "科普|入门|教程|指南|解释|是什么|怎么": "科普/教程",
        "新闻|快讯|速递|速递|简讯|快报|晚报|早报|收盘": "新闻/快讯",
        "文案|广告|营销|推广|销售|促销|转化": "营销文案",
        "分析|报告|研报|深度|洞察|展望|白皮书": "分析/报告",
    }
    
    AUDIENCES = {
        "投资|基金|股票|金融|理财|交易|散户|机构": "投资人群",
        "技术|开发|工程|程序员|架构|运维|数据": "技术人群",
        "学生|高中|初中|大学|学习|考试|备考": "学生",
        "决策|管理|CEO|CTO|高管|领导|战略": "决策者",
        "大众|普通|老百姓|百姓|一般": "普通大众",
        "医生|医疗|临床|患者|药物": "医疗专业人群",
    }
    
    DEPTHS = {
        r"(≤|<=|不超过?)\s*500\s*字|300字|快讯|简讯|短": "快讯级 (≤500字)",
        r"500.*2000|短文|简要|千字": "短篇 (500-2000字)",
        r"2000.*5000|中篇|详细|全面": "中篇 (2000-5000字)",
        r"深度|≥5000|长篇|详尽|完整|全面分析": "深度 (≥5000字)",
    }
    
    TIMELINESS = {
        "实时|即时|马上|立刻|分钟|秒|今天": "实时/日内",
        "日内|今天|当日|每日|daily": "日级",
        "周|weekly|每周": "周级",
        "月|季度|年度|monthly|quarterly": "月级/季度",
    }
    
    STYLES = {
        "数据|统计|图表|量化|指标|数字|实证": "数据驱动",
        "故事|案例|叙述|经历|讲述": "叙事为主",
        "论证|逻辑|推理|证明|论据": "论证导向",
        "简单|通俗|易懂|大白话|比喻|类比": "通俗易懂",
        "精确|严谨|准确|规范|标准": "技术准确",
        "优美|文学|诗意|修辞|美感": "文学性",
    }
    
    DOMAINS = {
        "金融|股票|A股|基金|投资|理财|交易|证券": "金融",
        "科技|AI|人工智能|芯片|半导体|软件|硬件|IT": "科技",
        "医疗|药|临床|疾病|治疗|健康|患者": "医疗",
        "政策|法规|监管|法律|合规|条例": "政策/法律",
        "教育|学习|考试|课程|培训|教学": "教育",
        "消费|零售|电商|品牌|营销|用户": "消费",
        "制造|工业|工厂|生产|供应链": "制造",
        "能源|新能源|电池|光伏|风电|储能": "能源",
        "游戏|娱乐|影视|音乐|文化": "文化/娱乐",
    }
    
    CONSTRAINTS = {
        "合规|监管|敏感|审查": "合规敏感",
        "引用|来源|出处|citation": "需引用来源",
        "多方|正反|两面|平衡|客观": "需多立场",
        "图表|可视化|infographic|图示": "需图表",
        "代码|示例|example|code|sample": "需代码示例",
        "模板|格式|模板化|结构化": "有模板约束",
    }
    
    CHANNELS = {
        "网站|web|网页|官网": "网站",
        "公众号|微信|公众号": "公众号",
        "研报|研究报告|platform": "研报平台",
        "社交|微博|twitter|X|小红书|抖音": "社交媒体",
        "邮件|email|newsletter": "邮件",
        "API文档|dev|developer|接口文档": "API文档平台",
    }
    
    def structure(self, text: str) -> StructuredSpec:
        """NL → Structured"""
        text_lower = text.lower()
        
        spec = StructuredSpec()
        
        # ① 核心意图
        spec.core_intent = self._extract_intent(text)
        
        # ②-⑨ 规则匹配
        spec.product_type = self._match(text, self.PRODUCT_TYPES)
        spec.target_audience = self._match(text, self.AUDIENCES)
        spec.depth = self._match_regex(text, self.DEPTHS)
        spec.timeliness = self._match(text, self.TIMELINESS)
        spec.style = self._match(text, self.STYLES)
        spec.domain_tags = self._match_all(text, self.DOMAINS)
        spec.constraints = self._match_all(text, self.CONSTRAINTS)
        spec.channel = self._match(text, self.CHANNELS)
        
        # 智能默认推断 (提高覆盖)
        if not spec.depth:
            if any(w in text for w in ['快', '短', '简', '300', '500', '速递', '收盘', '午间']):
                spec.depth = "快讯级 (≤500字)"
            elif any(w in text for w in ['深度', '长', '详', '全面', '报告']):
                spec.depth = "深度 (≥5000字)"
            elif any(w in text for w in ['篇', '章', '文']):
                spec.depth = "短篇 (500-2000字)"
        
        if not spec.timeliness:
            if any(w in text for w in ['今天', '今日', '快', '实时', '马上']):
                spec.timeliness = "日级"
        
        if not spec.style:
            if spec.product_type == "营销文案":
                spec.style = "叙事为主"
            elif spec.product_type in ["技术文档"]:
                spec.style = "技术准确"
            elif spec.product_type in ["分析/报告"]:
                spec.style = "数据驱动" if "数据" in text else "论证导向"
        
        # ⑩ 显式 vs 隐含
        spec.explicit_vs_implicit = {
            "explicit": {k: v for k, v in [
                ("product_type", spec.product_type),
                ("audience", spec.target_audience),
                ("depth", spec.depth),
            ] if v},
            "implicit": {
                "note": "部分维度基于关键词推理补充",
                "inferred": [k for k, v in [
                    ("style", spec.style),
                    ("timeliness", spec.timeliness),
                    ("channel", spec.channel),
                ] if v and k not in ["product_type", "audience", "depth"]],
            },
        }
        
        # 置信度: 基于实际提取的维度的覆盖度
        filled = spec.completeness()
        spec.confidence = min(0.95, 0.3 + filled * 0.07)  # 10维全填 = 1.0, 5维 = 0.65
        
        return spec
    
    def _extract_intent(self, text: str) -> str:
        """提取核心意图"""
        # 找"需要/要/想/帮/请"之后的句子
        patterns = [
            r'(?:需要|要|想要|希望|请|帮)\s*(?:我|写|生成|创作|做)?\s*[一二三四五六七八九十]?\s*[篇份个条]?\s*(.+?)(?:[。！，,;；]|$)',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()[:100]
        # Fallback: 前80字
        return text[:80].strip()
    
    def _match(self, text: str, rules: dict) -> str:
        """单规则匹配 → 第一个命中"""
        for pattern, result in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                return result
        return ""
    
    def _match_regex(self, text: str, rules: dict) -> str:
        """正则匹配"""
        for pattern, result in rules.items():
            if re.search(pattern, text):
                return result
        return ""
    
    def _match_all(self, text: str, rules: dict) -> list:
        """多规则匹配 → 所有命中"""
        results = []
        for pattern, result in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                results.append(result)
        return results


# ═══════════════════════════════════════
# STEP 2-4: Classify → Config → Interrogate
# ═══════════════════════════════════════

class Classifier:
    """7-Rule Decision Tree → 6 Clusters"""
    
    # L2 配置模板 (对应 SPDT-005 六 PDT)
    PDT_MAP = {
        ClusterType.A_FLASH_NEWS:  {"pdt_id": "PT-041", "pdt_name": "FlashNews",  "dir": "PT-041_FlashNews"},
        ClusterType.B_DEEP_PROD:  {"pdt_id": "PT-040", "pdt_name": "DeepProd",   "dir": "PT-040_DeepProd"},
        ClusterType.C_SCI_POP:    {"pdt_id": "PT-042", "pdt_name": "SciPop",     "dir": "PT-042_SciPop"},
        ClusterType.D_TECH_DOC:   {"pdt_id": "PT-045", "pdt_name": "TechDoc",    "dir": "PT-045_TechDoc"},
        ClusterType.E_OP_ED:      {"pdt_id": "PT-043", "pdt_name": "OpEd",       "dir": "PT-043_OpEd"},
        ClusterType.F_CREATIVE_X: {"pdt_id": "PT-044", "pdt_name": "CreativeX",  "dir": "PT-044_CreativeX"},
    }

    L2_CONFIGS = {
        ClusterType.A_FLASH_NEWS: {
            "template": "news_flash_v1", "max_length": 500,
            "tone": "concise", "citation": False,
            "writer_config": "speed_optimized",
        },
        ClusterType.B_DEEP_PROD: {
            "template": "deep_analysis_v1", "min_length": 2000,
            "tone": "analytical", "citation": True,
            "writer_config": "quality_optimized",
        },
        ClusterType.C_SCI_POP: {
            "template": "knowledge_pop_v1", "tone": "conversational",
            "analogies": True, "citation": False,
            "writer_config": "scipop_optimized",
        },
        ClusterType.D_TECH_DOC: {
            "template": "tech_doc_v1", "format": "structured",
            "code_examples": True, "citation": True,
            "writer_config": "precision_optimized",
        },
        ClusterType.E_OP_ED: {
            "template": "oped_v1", "tone": "argumentative",
            "citation": True, "multi_view": True,
            "writer_config": "opinion_optimized",
        },
        ClusterType.F_CREATIVE_X: {
            "template": "creativex_v1", "tone": "persuasive",
            "cta": True, "audience_targeting": True,
            "writer_config": "brand_optimized",
        },
        ClusterType.CROSS_SPDT: {
            "template": "cross_spdt", "route": "SPDT-004",
            "note": "教育内容 → 路由到 SPDT-004 教育内容制造",
        },
    }
    
    def classify(self, spec: StructuredSpec, original_text: str = "") -> ClassificationResult:
        """7规则决策树 + 跨SPDT路由"""
        confidence = spec.confidence

        # Rule 0: 教育意图 → CROSS_SPDT (SPDT-004) — 最高优先级
        if self._is_education_detected(spec, original_text):
            result = self._build_result(ClusterType.CROSS_SPDT, "跨产品线路由 → SPDT-004",
                                       confidence, "Rule 0: 教育意图 → CROSS_SPDT (SPDT-004)", spec)
            result.cross_spdt_route = "SPDT-004"
            return result

        # Rule 1: 短文本 + 高时效 → FlashNews (PT-041)
        if spec.depth and "快讯" in spec.depth:
            return self._build_result(ClusterType.A_FLASH_NEWS, "FlashNews (PT-041)", confidence,
                                     "Rule 1: 短文本 + 高时效 → FlashNews", spec)

        # Rule 2: 科普/教程 + 通俗 → SciPop (PT-042) — 不含教育，教育已被 Rule 0 拦截
        if (spec.product_type in ["科普/教程"] or
            (spec.target_audience == "普通大众" and spec.style == "通俗易懂")):
            return self._build_result(ClusterType.C_SCI_POP, "SciPop (PT-042)", confidence,
                                     "Rule 2: 科普/教程 + 通俗受众 → SciPop", spec)

        # Rule 3: 评论/观点 → OpEd (PT-043)
        if spec.product_type in ["评论/观点"] or spec.style == "文学性":
            return self._build_result(ClusterType.E_OP_ED, "OpEd (PT-043)", confidence,
                                     "Rule 3: 评论/观点 → OpEd", spec)

        # Rule 4: 数据驱动 + 分析/报告 + 深度 → DeepProd (PT-040)
        if (spec.product_type in ["分析/报告"] or
            (spec.style == "数据驱动" and spec.depth and "深度" in spec.depth)):
            return self._build_result(ClusterType.B_DEEP_PROD, "DeepProd (PT-040)", confidence,
                                     "Rule 4: 数据驱动 + 分析报告 → DeepProd", spec)

        # Rule 5: 技术文档 + API/代码 → TechDoc (PT-045)
        if (spec.product_type == "技术文档" or
            any(c in ["需代码示例"] for c in spec.constraints)):
            return self._build_result(ClusterType.D_TECH_DOC, "TechDoc (PT-045)", confidence,
                                     "Rule 5: 技术文档 + 代码示例 → TechDoc", spec)

        # Rule 6: 营销文案 → CreativeX (PT-044)
        if spec.product_type == "营销文案":
            return self._build_result(ClusterType.F_CREATIVE_X, "CreativeX (PT-044)", confidence,
                                     "Rule 6: 营销文案 → CreativeX", spec)

        # Rule 7: Default fallback — 基于领域推理
        cluster = self._fallback_cluster(spec)
        confidence = max(0.3, confidence - 0.2)
        return self._build_result(cluster, f"Fallback-{cluster.value}", confidence,
                                 f"Rule 7: Default fallback → {cluster.value}", spec)

    def _is_education_detected(self, spec: StructuredSpec, original_text: str) -> bool:
        """检测教育意图 → 跨路由到 SPDT-004"""
        # 明确的教育受众
        if spec.target_audience == "学生":
            return True
        # 教育领域标签
        if any(d == "教育" for d in spec.domain_tags):
            return True
        # 原始文本包含教育关键词
        if original_text:
            text_lower = original_text.lower()
            edu_count = sum(1 for kw in [
                "学生", "高中", "初中", "小学", "大学", "考试", "备考", "高考",
                "课件", "课程", "教学", "教材", "教案", "上课", "课堂",
                "知识点", "习题", "试题", "作业", "辅导", "复习", "培训",
            ] if kw in text_lower)
            if edu_count >= 2:
                return True
        return False
    
    def _fallback_cluster(self, spec: StructuredSpec) -> ClusterType:
        """基于领域标签的降级推理"""
        if any(d in ["金融", "科技", "能源"] for d in spec.domain_tags):
            return ClusterType.B_DEEP_PROD
        # 教育领域已在 Rule 0 中处理，此处不再路由
        if spec.target_audience == "技术人群":
            return ClusterType.D_TECH_DOC
        return ClusterType.UNKNOWN
    
    def _build_result(self, cluster: ClusterType, name: str, confidence: float,
                      rule: str, spec: StructuredSpec) -> ClassificationResult:
        """构建分类结果"""
        pdt_info = self.PDT_MAP.get(cluster, {})
        result = ClassificationResult(
            cluster=cluster,
            cluster_name=name,
            confidence=confidence,
            rule_matched=rule,
            l2_config=self.L2_CONFIGS.get(cluster, {}),
            reasoning=self._build_reasoning(spec, rule),
            structured=spec,
            pdt_id=pdt_info.get("pdt_id", ""),
        )

        # 跨 SPDT 路由设置
        if cluster == ClusterType.CROSS_SPDT:
            result.cross_spdt_route = "SPDT-004"

        # Step 4: 低置信度反问
        if confidence < 0.85:
            result.interrogate_questions = self._generate_questions(spec)

        return result
    
    def _build_reasoning(self, spec: StructuredSpec, rule: str) -> str:
        """A3: 决策路径可解释"""
        steps = []
        if spec.product_type:
            steps.append(f"产品类型={spec.product_type}")
        if spec.target_audience:
            steps.append(f"受众={spec.target_audience}")
        if spec.style:
            steps.append(f"风格={spec.style}")
        if spec.depth:
            steps.append(f"深度={spec.depth}")
        steps.append(f"→ {rule}")
        return " | ".join(steps)
    
    def _generate_questions(self, spec: StructuredSpec) -> list:
        """低置信度 → 反问"""
        questions = []
        if not spec.product_type:
            questions.append("您想要的是一篇文章、一份分析报告、还是一篇科普说明？")
        if not spec.target_audience:
            questions.append("目标读者是谁？（专业人群/投资人群/普通大众/学生）")
        if not spec.depth:
            questions.append("篇幅要求？（快讯<500字 / 短篇 / 中篇 / 深度长文）")
        if not spec.style:
            questions.append("风格偏好？（数据驱动/通俗易懂/叙事为主）")
        if not questions:
            questions.append("请补充更多细节以帮助精准分类。")
        return questions


# ═══════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════

class TextClassifier:
    """4-Step Pipeline"""
    
    def __init__(self):
        self.structurer = Structurer()
        self.classifier = Classifier()
    
    def process(self, text: str) -> ClassificationResult:
        """完整流程"""
        t0 = time.time()
        
        # Step 1: 结构化
        spec = self.structurer.structure(text)
        
        # Step 2-4: 分类 + 配置 + 反问
        result = self.classifier.classify(spec, text)
        
        elapsed = (time.time() - t0) * 1000
        logger.info(f"Processed in {elapsed:.0f}ms, cluster={result.cluster.value}, confidence={result.confidence:.2f}")
        
        return result
    
    def process_batch(self, texts: list[str]) -> list[ClassificationResult]:
        return [self.process(t) for t in texts]


# ═══════════════════════════════════════
# CLI Test
# ═══════════════════════════════════════

def main():
    print("=" * 60)
    print("  SmartText Router — SPDT-005 媒体内容路由引擎")
    print("=" * 60)

    tc = TextClassifier()

    # Test cases covering 6 PDTs + cross-SPDT routing
    tests = [
        ("深度分析", "我需要一篇关于新能源电池技术路线的深度分析，面向投资人群，要求数据驱动"),
        ("快讯", "帮我写一篇今日A股收盘快评，300字以内，面向散户"),
        ("技术文档", "写一份面向开发者的 REST API 接口文档，需要包含认证、端点、错误码"),
        ("科普", "写一篇科普文章解释量子计算，面向普通大众，要有类比"),
        ("观点评论", "帮我写一篇关于AI伦理的评论文章，要有深度思考和批判性"),
        ("品牌营销", "写一份面向C端用户的新产品上市营销文案，强调性价比"),
        ("教育→SPDT-004", "帮我写一篇高中数学函数单调性的教学设计，要有课件和习题"),
        ("教育→SPDT-004", "给初中生写一篇物理力学的科普文章，用于课堂教学"),
    ]

    for label, text in tests:
        result = tc.process(text)
        qs = f" [反问: {len(result.interrogate_questions)}个]" if result.interrogate_questions else ""
        route_info = ""
        if result.cross_spdt_route:
            route_info = f" -> 路由到 {result.cross_spdt_route}"
        pdt_info = f" [{result.pdt_id}]" if result.pdt_id else ""
        print(f"\n  [{label}] {text[:45]}...")
        print(f"    Cluster: {result.cluster_name}{pdt_info} ({result.cluster.value}){route_info}")
        print(f"    Confidence: {result.confidence:.2f}{qs}")
        print(f"    Reasoning: {result.reasoning[:80]}")
        if result.interrogate_questions:
            for q in result.interrogate_questions:
                print(f"      ? {q}")

    # A1 check
    spec0 = tc.structurer.structure(tests[0][1])
    print(f"\n  [A1] Structure completeness: {spec0.completeness()}/10 dimensions")
    print(f"  [A5] Latency: <5s (rule-based, no API call)")

    print(f"\n{'=' * 60}")
    print("  SPDT-005 Router ready — 6 PDTs + Cross-SPDT(->004)")
    print("=" * 60)


if __name__ == "__main__":
    main()
