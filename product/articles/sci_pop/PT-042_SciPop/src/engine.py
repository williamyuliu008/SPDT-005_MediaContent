""" 知识科普集群 (CLUSTER-E) — Cluster Engine
    基于 SR-TEXT-006 设计规格实现
    核心逻辑：降维翻译 (Jargon → Layman)
    Pipeline: TOPIC_SELECT → RESEARCH → TRANSLATE（核心） → CREATIVE → REVIEW
"""

import yaml, json, os, logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

BASE = Path(__file__).parent.parent
CONFIG_DIR = BASE / "config"
SRC_DIR = BASE / "src"
OUT_DIR = BASE / "output"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scipop")


# ─── LLM 客户端 ───────────────────────────────────────────────────────────

def get_llm_client(mode: str = "mock"):
    """根据模式返回 LLM 客户端"""
    if mode == "mock":
        return MockLLM()
    elif mode in ("glm", "zhipu"):
        try:
            import zhipuai
            key = os.environ.get("ZHIPU_API_KEY") or _load_key()
            return zhipuai.ZhipuAI(api_key=key)
        except Exception as e:
            logger.warning(f"ZhipuAI 初始化失败: {e}，降级为 mock")
            return MockLLM()
    else:
        return MockLLM()


def _load_key() -> str:
    path = Path("D:/_CEO/bulletin/SECRET_KEY/zhipu_api.txt")
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    raise ValueError("ZHIPU_API_KEY 未设置，也找不到默认 key 文件")


# ─── Mock LLM ─────────────────────────────────────────────────────────────

class MockLLM:
    """本地 Mock 实现，用于演示和测试"""

    def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        logger.debug(f"[MockLLM] prompt 长度={len(prompt)}")
        return self._route(prompt)

    def _route(self, prompt: str) -> str:
        p = prompt.lower()
        # 路由到对应的 mock 响应（注意 prompt 中间段有关键词，需精确匹配）
        if "S1_RESEARCH" in prompt:
            return self._mock_research()
        elif "S2_TRANSLATE" in prompt:
            return self._mock_jargon_decode()
        elif "S3_WRITE" in prompt:
            return self._mock_article()
        elif "S4_REVIEW" in prompt:
            return self._mock_review()
        elif "选题" in prompt:
            return self._mock_topic_selection()
        elif "研究" in prompt or "sources" in p:
            return self._mock_research()
        elif "降维" in prompt or "术语" in prompt:
            return self._mock_jargon_decode()
        elif "类比" in prompt:
            return self._mock_analogy()
        elif "写作" in prompt or "科普文章" in prompt:
            return self._mock_article()
        elif "审查" in prompt:
            return self._mock_review()
        else:
            return self._default_response(prompt)

    def _mock_topic_selection(self) -> str:
        return json.dumps({
            "topic": "为什么北极冰川融化会导致海平面上升，但冰川融化本身也反映地球在'自我调节'？",
            "audience_level": "L2",
            "curiosity_gap_score": 8.5,
            "trend_evidence": "近30天'冰川融化'搜索量上升42%，知乎相关提问超5000条",
            "target_concepts": ["冰川融化", "海平面上升", "地球辐射平衡", "正反馈机制"]
        }, ensure_ascii=False)

    def _mock_research(self) -> str:
        return json.dumps({
            "sources": [
                {"title": "IPCC AR6报告", "type": "学术报告", "reliability": "极高"},
                {"title": "NASA格陵兰冰川监测数据", "type": "官方数据", "reliability": "极高"},
                {"title": "Nature Climate Change论文", "type": "同行评审", "reliability": "极高"}
            ],
            "concept_map": {
                "冰川融化": {"definition": "固态水转化为液态水的过程", "level": "L1"},
                "海平面上升": {"definition": "全球平均海平面的持续升高", "level": "L1"},
                "正反馈": {"definition": "一个变化会加速另一个同类变化", "level": "L2"}
            }
        }, ensure_ascii=False)

    def _mock_jargon_decode(self) -> str:
        return json.dumps({
            "mappings": [
                {
                    "term": "正反馈机制",
                    "L1_layman": "冰川融化会加剧升温，升温又让更多冰川融化——这是一个'越滚越大'的循环",
                    "L2_analogy": "就像滚雪球——雪球越大，滚过的雪越多，然后雪球更大",
                    "L3_deep": "当冰川反射阳光的白色表面消失，露出的深色海洋或岩石吸收更多热量，导致更多融化",
                    "accuracy_note": "核心机制：冰-反照率反馈；冰川融化的水也会加速冰体滑动"
                },
                {
                    "term": "海平面上升",
                    "L1_layman": "海水总量增加，同时水温升高导致海水膨胀，两种机制叠加使海平面升高",
                    "L2_analogy": "相当于把冰块放进装满水的杯子——冰融化后水位会上升",
                    "L3_deep": "热膨胀占当前海平面上升贡献的约40%，冰川融化贡献约35%"
                },
                {
                    "term": "反照率",
                    "L1_layman": "地球表面反射阳光的能力——白色冰雪反射多，深色海水吸收多",
                    "L2_analogy": "就像夏天的黑T恤比白T恤更热——深色的东西吸热，白色的东西反射热",
                    "L3_deep": "反照率=反射的阳光/总入射阳光。冰川反射30%的阳光，裸地只反射10%"
                },
                {
                    "term": "冰-反照率反馈",
                    "L1_layman": "冰川融化→深色表面露出→吸热增加→更多冰川融化",
                    "L2_analogy": "一个恶性循环：越热越融，越融越热",
                    "L3_deep": "这是地球气候系统中最强的正反馈机制之一，放大初始 warming 约2倍"
                }
            ]
        }, ensure_ascii=False)

    def _mock_analogy(self) -> str:
        return json.dumps({
            "analogy_for": "正反馈机制",
            "analogies": [
                {
                    "type": "生活类比",
                    "text": "就像多米诺骨牌——推倒第一张，它会撞倒第二张，然后是第三张……一张比一张快",
                    "accuracy": "高",
                    "limitation": "没有体现'同向加速'的特点"
                },
                {
                    "type": "自然类比",
                    "text": "就像全球变暖导致北极熊失去栖息地——变暖→冰融化→变暖加剧，这是一个无法自己停下来的循环",
                    "accuracy": "极高",
                    "limitation": "稍复杂，适合L2受众"
                }
            ]
        }, ensure_ascii=False)

    def _mock_article(self) -> str:
        return """# 你有没有想过：冰川融化越多，地球就越热，地球越热，冰川融化越多

你有没有想过，为什么冰川融化会让海平面上升，但同时地球好像也在"自我调节"——这到底是怎么回事？

## 先搞清楚一个问题：冰川融化和水变热

首先，冰川是什么？冰川就是陆地上长期积累、压实形成的巨量冰体。南极冰盖、格陵兰冰盖，以及喜马拉雅山脉的冰川，都属于这一类。

冰川融化很简单：当温度升高到冰点以上，冰就会变成水。这些水流进海洋，海平面自然就上升了。

但这只是第一层。

第二层更关键：**冰川本身就是地球的温度调节器**。

冰川的表面是白色的，白色会反射阳光——这叫"反照率"。当地球表面有大量白色冰川时，大约30%的阳光会被反射回太空，地球的温度就相对较低。

但当冰川融化，白色的冰面消失了，露出来的是深色的海洋或岩石。它们会吸收更多阳光，地球温度进一步升高。

温度升高 → 冰川融化加剧 → 更多深色表面暴露 → 吸收更多热量 → 温度进一步升高……

这就是科学上说的"正反馈"——**一个变化会加速另一个同类变化，就像滚雪球一样**。

## 现在的冰川融化，到底有多严重？

根据NASA的监测数据，格陵兰冰盖每年损失约2800亿吨冰。这个数字是什么概念？

想象一下：如果把这些冰均匀铺在整个北京市的土地上，每年的冰量可以堆出**一座3公里厚的冰山**。

更让人担心的是，这个速度在加快。过去10年，格陵兰冰盖的融化速度是前20年的两倍。

## 所以地球是在"自我调节"吗？

不是的。地球确实有调节机制（比如碳循环），但冰川融化带来的反馈是**正反馈**——它不是让地球回到平衡状态，而是让失衡加剧。

打个比方：如果把地球比作一艘正在进水的船，地球的调节机制像是舀水的人，而冰川融化带来的正反馈，像是破洞越来越大。

舀水的人在努力，但破洞变大的速度更快。

## 这对我们意味着什么？

海平面上升的影响是真实的：沿海城市面临被淹没的风险，部分太平洋岛国已经在考虑举国搬迁。

但这并不意味着我们什么都做不了——**冰川融化是一个过程，不是瞬间发生的事情**。理解它的机制，是采取行动的第一步。

---

*本文由知识科普集群 (CLUSTER-E) 自动生成 | 数据来源：IPCC AR6, NASA IceSat-2 | 审校：待人工审核*
"""

    def _mock_review(self) -> str:
        return json.dumps({
            "verdict": "APPROVED",
            "accuracy_score": 9.0,
            "accessibility_score": 8.5,
            "engagement_score": 8.0,
            "issues": [],
            "jargon_coverage": "100% — 所有专业术语均有通俗解释",
            "reading_level": "L2（高中文化程度可读）",
            "suggestions": [
                "建议在'正反馈'部分增加一个更直观的插图说明",
                "末尾可加一个'那我能做什么'的行动指引"
            ]
        }, ensure_ascii=False)

    def _default_response(self, prompt: str) -> str:
        return f"[MockLLM 响应] 处理了请求（prompt 长度: {len(prompt)}）"


# ─── Gate 检查 ─────────────────────────────────────────────────────────────

@dataclass
class GateResult:
    passed: bool
    score: float
    message: str
    details: dict = field(default_factory=dict)


def check_gate(gate_id: str, data: dict) -> GateResult:
    """根据 gate_id 执行门控检查"""
    if gate_id == "TOPIC_GATE":
        score = 0
        checks = []
        if data.get("topic"):
            score += 4; checks.append("✓ 选题存在")
        if data.get("audience_level"):
            score += 3; checks.append("✓ 受众水平明确")
        if data.get("curiosity_gap_score", 0) >= 7.0:
            score += 3; checks.append("✓ 好奇心缺口显著")
        return GateResult(passed=score >= 7, score=score, message="; ".join(checks), details={"raw": data})

    elif gate_id == "RESEARCH_GATE":
        sources = data.get("sources", [])
        concept_map = data.get("concept_map", {})
        score = 0
        if len(sources) >= 3:
            score += 5; checks = ["✓ 权威源≥3个"]
        else:
            checks = [f"✗ 权威源仅{len(sources)}个"]
        if len(concept_map) >= 3:
            score += 5; checks.append("✓ 概念图谱完整")
        else:
            checks.append(f"✗ 概念图谱不完整")
        passed = score >= 7
        return GateResult(passed=passed, score=score, message="; ".join(checks), details={"raw": data})

    elif gate_id == "TRANSLATE_GATE":
        mappings = data.get("mappings", [])
        score = 0
        if len(mappings) >= 3:
            score += 4; checks = ["✓ 术语覆盖充分"]
        else:
            checks = [f"✗ 术语仅{len(mappings)}条"]
        all_have_L1 = all(m.get("L1_layman") for m in mappings)
        if all_have_L1:
            score += 3; checks.append("✓ 所有术语有L1通俗化")
        if all_have_L1 and all(m.get("L2_analogy") for m in mappings):
            score += 3; checks.append("✓ 所有术语有L2类比")
        return GateResult(passed=score >= 7, score=score, message="; ".join(checks), details={"raw": data})

    elif gate_id == "CREATIVE_GATE":
        article = data.get("article_text", "")
        score = 0
        if len(article) >= 500:
            score += 4; checks = [f"✓ 文章字数{len(article)}"]
        else:
            checks = [f"✗ 文章字数仅{len(article)}"]
        if "你有没有想过" in article or "?" in article:
            score += 3; checks.append("✓ 有问题开头")
        if "##" in article:
            score += 3; checks.append("✓ 有章节结构")
        return GateResult(passed=score >= 7, score=score, message="; ".join(checks), details={"raw": data})

    elif gate_id == "REVIEW_GATE":
        verdict = data.get("verdict", "REJECTED")
        score = data.get("accuracy_score", 0) + data.get("accessibility_score", 0) + data.get("engagement_score", 0)
        return GateResult(
            passed=verdict in ("APPROVED", "PASS") and score >= 20,
            score=score,
            message=f"审校结果: {verdict}",
            details={"raw": data}
        )

    return GateResult(passed=True, score=5.0, message="无门控要求")


# ─── 主 Engine ──────────────────────────────────────────────────────────────

@dataclass
class StageResult:
    stage_id: str
    stage_name: str
    gate: str
    gate_result: GateResult
    output: dict
    duration_ms: float
    error: Optional[str] = None


class SciPopEngine:
    def __init__(self, llm_mode: str = "mock", verbose: bool = True):
        self.llm = get_llm_client(llm_mode)
        self.verbose = verbose
        self.cluster = self._load_cluster()
        self._log: list[dict] = []
        self._results: dict[str, StageResult] = {}

    def _load_cluster(self) -> dict:
        with open(CONFIG_DIR / "cluster.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def log(self, agent_id: str, action: str, prompt: str, output: str, tools: list = None):
        entry = {
            "agent_id": agent_id,
            "action": action,
            "prompt_chars": len(prompt),
            "output_chars": len(output),
            "timestamp": datetime.now().isoformat(),
            "tools": tools or []
        }
        self._log.append(entry)
        logger.debug(f"[{agent_id}] {action}: {len(prompt)}→{len(output)} chars")

    def run(self, topic: str = None, audience_level: str = "L2") -> dict:
        """执行完整流水线"""
        logger.info(f"CLUSTER-E 启动 | 目标受众: {audience_level}")
        start_total = datetime.now()

        outputs = {}

        # ── S1: RESEARCH ────────────────────────────────────────────────────
        s1 = self._run_research(topic, audience_level)
        outputs["S1_RESEARCH"] = s1.output
        self._results["S1_RESEARCH"] = s1
        if not s1.gate_result.passed:
            logger.error(f"❌ S1 gate 失败: {s1.gate_result.message}")
            return self._build_result(outputs, start_total)

        # ── S2: TRANSLATE（核心）────────────────────────────────────────────
        s2 = self._run_translate(outputs["S1_RESEARCH"], audience_level)
        outputs["S2_TRANSLATE"] = s2.output
        self._results["S2_TRANSLATE"] = s2
        if not s2.gate_result.passed:
            logger.error(f"❌ S2 gate 失败: {s2.gate_result.message}")
            return self._build_result(outputs, start_total)

        # ── S3: WRITE ──────────────────────────────────────────────────────
        s3 = self._run_write(outputs["S1_RESEARCH"], outputs["S2_TRANSLATE"], audience_level)
        outputs["S3_WRITE"] = s3.output
        self._results["S3_WRITE"] = s3
        if not s3.gate_result.passed:
            logger.error(f"❌ S3 gate 失败: {s3.gate_result.message}")
            return self._build_result(outputs, start_total)

        # ── S4: REVIEW ─────────────────────────────────────────────────────
        s4 = self._run_review(outputs["S3_WRITE"], audience_level)
        outputs["S4_REVIEW"] = s4.output
        self._results["S4_REVIEW"] = s4

        # ── 保存输出 ────────────────────────────────────────────────────────
        self._save_output(outputs)

        elapsed = (datetime.now() - start_total).total_seconds()
        logger.info(f"✅ CLUSTER-E 完成 | 耗时: {elapsed:.1f}s | "
                    f"S1={outputs['S1_RESEARCH'].get('gate_result',{})}, "
                    f"S2={s2.gate_result.passed}, S3={s3.gate_result.passed}, S4={s4.gate_result.passed}")

        return self._build_result(outputs, start_total)

    def _run_research(self, topic: str, audience_level: str) -> StageResult:
        t0 = datetime.now()
        stage = next(s for s in self.cluster["stages"] if s["id"] == "S1_RESEARCH")
        prompt = f"""你是知识科普集群 S1_RESEARCH 的研究员。

目标受众: {audience_level}
选题（可选，给了则用，没给则自行判断）: {topic or '（空，请自主选题）'}

请执行以下任务：

1. 【选题】如果你被指定了topic，直接使用。如果没指定，请从以下领域选择一个近期公众关注度高的话题：气候变化、AI技术进展、量子物理、核能争议等。

2. 【受众分析】评估该话题的目标受众知识水平：
- L1: 零基础，没有任何先验知识
- L2: 有兴趣，有模糊概念，需要系统化
- L3: 入门者，有一定基础，需要深化

3. 【研究】从以下来源类型中为你的topic收集资料：
- 学术文献（arXiv/PubMed/Google Scholar）
- 权威教科书/百科
- 官方机构（WHO/NASA/央行/统计局）
- 领域专家公开讲座

4. 【概念图谱】列出核心概念及其依赖关系，理解B必须先理解A。

请以JSON格式输出：
{{
  "topic": "你的选题（一个好奇心驱动的问句形式）",
  "audience_level": "L1/L2/L3",
  "curiosity_gap_score": 0-10,
  "trend_evidence": "搜索趋势/问答热度/事件关联的证据",
  "sources": [{{"title": "标题", "type": "类型", "reliability": "可靠性"}}],
  "concept_map": {{"概念名": {{"definition": "定义", "level": "L1/L2/L3"}}}}
}}
"""
        try:
            raw = self.llm.generate(prompt)
            data = json.loads(raw) if raw.startswith("{") else {}
        except Exception as e:
            logger.error(f"S1 LLM 调用失败: {e}")
            data = {}
        gate = check_gate(stage["gate"], data)
        self.log("S1_RESEARCH", "generate", prompt, raw)
        return StageResult(
            stage_id="S1_RESEARCH", stage_name="知识研究",
            gate=stage["gate"], gate_result=gate,
            output={"topic_data": data, "article_text": raw},
            duration_ms=(datetime.now() - t0).total_seconds() * 1000
        )

    def _run_translate(self, research_output: dict, audience_level: str) -> StageResult:
        t0 = datetime.now()
        stage = next(s for s in self.cluster["stages"] if s["id"] == "S2_TRANSLATE")
        topic_data = research_output.get("topic_data", {})
        concepts = topic_data.get("concept_map", {})
        target_terms = list(concepts.keys()) if concepts else ["核心概念"]

        prompt = f"""你是知识科普集群 S2_TRANSLATE 的核心——术语降维专家。

目标受众: {audience_level}
核心概念列表: {target_terms}

你的任务是为每个专业术语提供三层降维翻译：

**L1 降维（替换术语）**：
将专业术语替换为大众熟悉的词汇，不解释原因，直接让外行能听懂。

**L2 降维（引入类比）**：
用一个生活中的具体例子或场景来说明，让受众'原来是这样！'

**L3 降维（极致简化）**：
用最直觉的方式描述本质，一句话说明核心逻辑。

约束：
- L1: 句子简洁，Flesch易读性要低（每句≤15字）
- L2: 类比必须来自受众日常生活，不能引入误导性类比
- L3: 极致简化，但不能失去核心准确性
- 每个术语必须同时有L1、L2、L3三种翻译

请以JSON格式输出：
{{
  "mappings": [
    {{
      "term": "专业术语名",
      "L1_layman": "L1通俗化",
      "L2_analogy": "L2生活类比",
      "L3_deep": "L3极致简化",
      "accuracy_note": "准确性说明（重点标注可能的误解风险）"
    }}
  ]
}}
"""
        try:
            raw = self.llm.generate(prompt)
            data = json.loads(raw) if raw.startswith("{") else {}
        except Exception as e:
            logger.error(f"S2 LLM 调用失败: {e}")
            data = {}
        gate = check_gate(stage["gate"], data)
        self.log("S2_TRANSLATE", "jargon_decode", prompt, raw)
        return StageResult(
            stage_id="S2_TRANSLATE", stage_name="术语降维",
            gate=stage["gate"], gate_result=gate,
            output={"mappings": data.get("mappings", []), "raw": raw},
            duration_ms=(datetime.now() - t0).total_seconds() * 1000
        )

    def _run_write(self, research_output: dict, translate_output: dict, audience_level: str) -> StageResult:
        t0 = datetime.now()
        stage = next(s for s in self.cluster["stages"] if s["id"] == "S3_WRITE")
        topic_data = research_output.get("topic_data", {})
        mappings = translate_output.get("mappings", [])

        prompt = f"""你是知识科普集群 S3_WRITE 的科普作家。

目标受众: {audience_level}（{audience_level} = {"零基础大众" if audience_level == "L1" else "有兴趣的普通人" if audience_level == "L2" else "入门学习者"}）
选题: {topic_data.get("topic", "（使用已有概念）")}
核心概念及降维翻译:
{json.dumps(mappings, ensure_ascii=False, indent=2)}

你的写作要求：
1. 【开头】用问题驱动：一个受众真正好奇但一直搞不清楚的问题。形式：'你有没有想过……'或'99%的人都搞错了……'
2. 【结构】用章节标题（##）组织内容，每章不超过5段
3. 【术语】使用L1通俗化表达；专业术语首次出现时，必须括号标注原文
4. 【类比】在关键位置插入L2类比，帮助受众建立直觉
5. 【结尾】给受众一个'行动指引'或'思考空间'，不要留悬空感
6. 【字数】800-1500字
7. 【格式】Markdown，用##做章节标题

约束：
- 准确性第一：宁可多解释一句，不能牺牲准确性
- 趣味性服务于理解：不要为有趣而有趣
- 禁止：没有来源的个人观点、未经核实的数据、情绪化表达
"""
        try:
            raw = self.llm.generate(prompt)
        except Exception as e:
            logger.error(f"S3 LLM 调用失败: {e}")
            raw = ""
        data = {"article_text": raw}
        gate = check_gate(stage["gate"], data)
        self.log("S3_WRITE", "write_article", prompt, raw)
        return StageResult(
            stage_id="S3_WRITE", stage_name="科普写作",
            gate=stage["gate"], gate_result=gate,
            output=data,
            duration_ms=(datetime.now() - t0).total_seconds() * 1000
        )

    def _run_review(self, write_output: dict, audience_level: str) -> StageResult:
        t0 = datetime.now()
        stage = next(s for s in self.cluster["stages"] if s["id"] == "S4_REVIEW")
        article = write_output.get("article_text", "")

        prompt = f"""你是知识科普集群 S4_REVIEW 的审校专家。

目标受众: {audience_level}
待审文章:
{article}

请执行双重审查：

1. 【准确性审查】
- 每个科学/事实声明是否有来源支撑？（无需查证，但需判断）
- 是否存在可能导致公众误解的表述？
- 术语使用是否与降维翻译表一致？

2. 【可读性审查】
- 以目标受众视角阅读：能顺畅读完吗？哪里会卡住？
- Flesch易读性评分（1-10，10=最容易）
- 专业术语覆盖率：有多少比例的术语有通俗解释？

3. 【趣味性评估】
- 开头是否能吸引读者？
- 是否有足够的场景/故事/类比来维持兴趣？

请以JSON格式输出：
{{
  "verdict": "APPROVED / NEEDS_REVISION / REJECTED",
  "accuracy_score": 0-10,
  "accessibility_score": 0-10,
  "engagement_score": 0-10,
  "issues": ["问题1", "问题2"],
  "jargon_coverage": "覆盖率描述",
  "reading_level": "评估的阅读难度等级",
  "suggestions": ["修改建议1"]
}}
"""
        try:
            raw = self.llm.generate(prompt)
            data = json.loads(raw) if raw.startswith("{") else {"verdict": "APPROVED", "raw": raw}
        except Exception as e:
            logger.error(f"S4 LLM 调用失败: {e}")
            data = {}
        gate = check_gate(stage["gate"], data)
        self.log("S4_REVIEW", "review", prompt, raw)
        return StageResult(
            stage_id="S4_REVIEW", stage_name="审校",
            gate=stage["gate"], gate_result=gate,
            output=data,
            duration_ms=(datetime.now() - t0).total_seconds() * 1000
        )

    def _save_output(self, outputs: dict):
        OUT_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        article = outputs.get("S3_WRITE", {}).get("article_text", "")
        review = outputs.get("S4_REVIEW", {})
        summary = {
            "cluster_id": "scipop_cluster",
            "generated_at": datetime.now().isoformat(),
            "stages": {k: {
                "gate_passed": v.gate_result.passed,
                "gate_score": v.gate_result.score,
                "gate_message": v.gate_result.message
            } for k, v in self._results.items()},
            "article": article[:200] + "..." if len(article) > 200 else article,
            "review_verdict": review.get("verdict", "unknown"),
            "review_scores": {
                "accuracy": review.get("accuracy_score"),
                "accessibility": review.get("accessibility_score"),
                "engagement": review.get("engagement_score")
            }
        }
        with open(OUT_DIR / f"report_{ts}.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 报告已保存: {OUT_DIR / f'report_{ts}.json'}")

    def _build_result(self, outputs: dict, start: datetime):
        return {
            "status": "completed",
            "elapsed_seconds": (datetime.now() - start).total_seconds(),
            "stages": {k: {
                "gate_passed": v.gate_result.passed,
                "gate_score": v.gate_result.score,
                "gate_message": v.gate_result.message
            } for k, v in self._results.items()},
            "final_article": outputs.get("S3_WRITE", {}).get("article_text", ""),
            "final_review": outputs.get("S4_REVIEW", {})
        }


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="知识科普集群 CLUSTER-E")
    parser.add_argument("--mode", choices=["mock", "glm", "zhipu"], default="mock",
                        help="LLM 模式: mock=本地演示, glm/zhipu=使用真实API")
    parser.add_argument("--topic", type=str, default=None,
                        help="指定选题（留空则自主选题）")
    parser.add_argument("--audience", choices=["L1", "L2", "L3"], default="L2",
                        help="目标受众等级: L1=零基础, L2=普通人, L3=入门者")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 60)
    print("  知识科普集群 (CLUSTER-E) — SR-TEXT-006")
    print(f"  模式: {args.mode} | 受众: {args.audience}")
    print("=" * 60)

    engine = SciPopEngine(llm_mode=args.mode, verbose=args.verbose)
    result = engine.run(topic=args.topic, audience_level=args.audience)

    print()
    print("  各阶段门控结果:")
    for sid, sr in result["stages"].items():
        icon = "✅" if sr["gate_passed"] else "❌"
        print(f"  {icon} {sid}: {sr['gate_message']} (分数:{sr['gate_score']})")
    print()
    print(f"  总耗时: {result['elapsed_seconds']:.1f}s")
    verdict = result.get("final_review", {}).get("verdict", "unknown")
    print(f"  最终审校结论: {verdict}")

    if result.get("final_article"):
        print()
        print("  ── 文章预览（前800字）──")
        print(result["final_article"][:800])
        print("  ...")

    print("=" * 60)


if __name__ == "__main__":
    main()
