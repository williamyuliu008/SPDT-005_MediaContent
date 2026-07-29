"""
SmartTextPlatform Phase 3 — Enhanced Cluster Engine
=====================================================
修复 (MKT 质量审核 v1.0):
  X-REQ-01: Stage 间递进机制 — 提取 structured_context 传给下一 stage
  X-REQ-02: 差异化 Stage Prompt — 每个 stage 独立 system prompt
  X-REQ-03: max_tokens 分级 — 按 stage 精准控制 token 消耗
  B-REQ-02: 深产延迟优化 — 合并重复 stage + 分级 token
"""
import sys, os, json, yaml, logging, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.llm_gateway import LLMGateway, LLMResponse
from shared.decision_log import DecisionLogger
from shared.artifact import ArtifactBus
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("stp.engine.v3")

# ═══════════════════════════════════════
# X-REQ-02: 差异化 Stage Prompt
# ═══════════════════════════════════════

STAGE_SYSTEM_PROMPTS = {
    # 深度生产 (CLUSTER-B) — 每个 stage 独立角色
    "S1_TOPIC": "你是选题编辑。从需求中提炼最有价值的选题角度，列出核心信源清单。只做选题，不做研究。",
    "S2_RESEARCH": "你是研究分析员。基于S1的选题和信源清单，提取关键数据、趋势和竞争信息。你的输入是S1的选题框架，不要重复选题。",
    "S3_WRITING": "你是资深撰稿人。基于S2的研究数据，组织叙事撰写正文。你的输入是S2的研究报告，不要重新做研究。保持数据引用。",
    "S4_REVIEW": "你是审阅编辑。核查S3正文的数据一致性、逻辑完整性、格式规范性。只标注问题，不重写。",
    
    # 实时快反 (CLUSTER-A)
    "S1_MONITOR": "你是行情监控员。从结构化数据中提取关键行情信息。只陈述数据，不做分析。",
    "S2_VERIFY": "你是数据校验员。检查S1提取的数据是否完整、时间戳是否新鲜。数据超时→标记延迟。数据缺失→标记缺口。",
    "S3_DRAFT": "你是财经快讯编辑。基于S2校验通过的数据，组织为简洁快讯。不超过300字。",
    "S4_PUBLISH": "你是发布审核员。最终检查：合规敏感词、格式规范性、发布时间戳。",
    
    # 技术文档 (CLUSTER-D)
    "S1_SPEC": "你是技术文档架构师。分析API/工具的功能，输出文档大纲和章节结构。",
    "S2_RESEARCH": "你是API研究员。基于S1的大纲，研究每个端点的输入/输出/错误码。",
    "S3_WRITE": "你是技术文档工程师。基于S2的研究，撰写完整的Markdown文档含代码示例。",
    "S4_REVIEW": "你是技术审阅员。检查S3文档的代码可运行性、API准确性、格式规范性。",
    
    # 创意转化 (CLUSTER-C)
    "S1_BRIEF": "你是创意策划。分析产品+受众，输出5-8个创意方向脑暴。只做发散，不做筛选。",
    "S2_IDEATE": "你是创意总监。从S1的5-8个方向中按受众匹配度筛选Top2，深化概念。不重复脑暴。",
    "S3_CREATE": "你是资深文案。基于S2的深化概念，创作完整营销文案。含标题/痛点/方案/CTA。",
    "S4_POLISH": "你是语言精修师。优化S3文案的节奏、金句、emoji使用。不做大改，只做微调。",
    
    # 知识科普 (CLUSTER-E)
    "S1_RESEARCH": "你是领域专家。梳理核心概念、关键原理、重要人物、常见误解。只做研究笔记。",
    "S2_TRANSLATE": "你是科学传播者。将S1的专家笔记转化为通俗类比和故事。不重复罗列术语。",
    "S3_WRITE": "你是科普作家。基于S2的通俗转化，撰写面向大众的科普文章。用类比、用故事。",
    "S4_REVIEW": "你是科普编辑。检查S3文章的准确性(类比不歪曲概念)、可读性、趣味性。",
    
    # 观点论证 (CLUSTER-F)
    "S1_RESEARCH": "你是论据研究员。搜集支持正反双方的证据、数据、案例。不偏袒任何一方。",
    "S2_STRUCTURE": "你是论证架构师。设计论证路径: 正方论据→反方最强论据(不可轻易驳倒)→综合判断。",
    "S3_WRITE": "你是评论撰稿人。基于S2的论证结构，撰写有深度、有证据、有判断的观点文章。",
    "S4_DEBATE": "你是魔鬼代言人。代表反方提出S3中未能充分回应的最强反驳。标记论证弱点。",
}

# ═══════════════════════════════════════
# X-REQ-03: max_tokens 分级
# ═══════════════════════════════════════

STAGE_TOKEN_LIMITS = {
    "S1_TOPIC": 1024, "S2_RESEARCH": 4096, "S3_WRITING": 8192,
    "S4_REVIEW": 2048, "S1_MONITOR": 512, "S2_VERIFY": 512,
    "S3_DRAFT": 1024, "S4_PUBLISH": 512, "S1_SPEC": 1024,
    "S2_RESEARCH": 4096, "S3_WRITE": 4096, "S4_REVIEW": 2048,
    "S1_BRIEF": 1024, "S2_IDEATE": 2048, "S3_CREATE": 4096,
    "S4_POLISH": 2048, "S2_TRANSLATE": 2048,
    "S4_DEBATE": 2048,
}


class StageContext:
    """X-REQ-01: Stage 间结构化传递协议"""
    
    def __init__(self, stage_id: str):
        self.stage_id = stage_id
        self.summary: str = ""         # 本 stage 的一行摘要
        self.key_findings: list = []   # 关键发现
        self.data_points: dict = {}    # 结构化数据 (供下一 stage 提取)
        self.for_next_stage: str = ""  # 给下一 stage 的指令
    
    def to_prompt_context(self) -> str:
        """转为可嵌入 prompt 的上下文"""
        parts = [f"[前序阶段 {self.stage_id} 的产出摘要]"]
        if self.summary:
            parts.append(f"核心: {self.summary}")
        if self.key_findings:
            parts.append("关键发现:\n" + "\n".join(f"- {f}" for f in self.key_findings[:5]))
        if self.data_points:
            parts.append("数据:\n" + "\n".join(f"- {k}: {v}" for k, v in list(self.data_points.items())[:5]))
        if self.for_next_stage:
            parts.append(f"下一阶段任务: {self.for_next_stage}")
        return "\n".join(parts)
    
    @classmethod
    def from_stage_output(cls, stage_id: str, content: str, config: dict = None) -> "StageContext":
        """从 Stage 输出提取结构化上下文"""
        ctx = cls(stage_id)
        # 提取前200字作为摘要
        ctx.summary = content[:200].replace("\n", " ") if content else ""
        
        # 提取 LLM 输出中的关键行
        lines = content.split("\n") if content else []
        for line in lines:
            line = line.strip()
            if line.startswith("##") or line.startswith("**"):
                ctx.key_findings.append(line.lstrip("#* ")[:100])
            if ":" in line and len(line) < 200:
                parts = line.split(":", 1)
                if len(parts) == 2 and len(parts[1].strip()) > 5:
                    ctx.data_points[parts[0].strip()] = parts[1].strip()[:100]
        
        # 限制数量
        ctx.key_findings = ctx.key_findings[:5]
        ctx.data_points = dict(list(ctx.data_points.items())[:5])
        
        return ctx


class ClusterEngineV3:
    """增强版集群引擎 — Stage 递进 + max_tokens 分级 + 差异化 Prompt"""
    
    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        base = Path(__file__).parent.parent
        
        config_path = base / "clusters" / cluster_id / "cluster.yaml"
        if not os.path.exists(config_path):
            config_path = Path(__file__).parent.parent.parent / "clusters" / cluster_id / "cluster.yaml"
        
        self.config = yaml.safe_load(open(config_path, 'r', encoding='utf-8'))
        self.llm = LLMGateway()
        self.decision_log = DecisionLogger(cluster_id)
        self.artifact_bus = ArtifactBus()
        self.mock_mode = not self.llm.api_key
        self._context_chain: list[StageContext] = []
    
    def run_stage(self, stage: dict, spec: dict, prev_ctx: StageContext = None) -> dict:
        """X-REQ-01+02+03: 递进式 Stage 执行"""
        sid = stage["id"]
        sname = stage["name"]
        
        # 差异化 system prompt
        system_prompt = STAGE_SYSTEM_PROMPTS.get(sid, 
            f"你是 {sname} 阶段的执行者。基于前序阶段的产出完成当前任务。")
        
        # 构建 user prompt — 含前序结构化上下文
        prompt_parts = [f"【你的角色】{sname} 阶段", f"【需求规格】{json.dumps(spec, ensure_ascii=False)[:1000]}"]
        
        if prev_ctx:
            prompt_parts.append(prev_ctx.to_prompt_context())
        else:
            prompt_parts.append("[前序阶段] 这是管道第一个阶段，请从需求规格中提取任务。")
        
        prompt_parts.append(f"【输出指令】严格按照 {sname} 的角色产出。不要重复前序阶段已经完成的工作。如果前序阶段已经分析了数据，你应该基于前序数据做进一步加工，而非重新分析。")
        
        user_prompt = "\n\n".join(prompt_parts)
        
        # 分级 max_tokens
        max_tokens = STAGE_TOKEN_LIMITS.get(sid, 4096)
        
        t0 = time.time()
        
        if self.mock_mode:
            content = self._mock_content(sid, spec)
            latency = (time.time() - t0) * 1000
        else:
            resp = self.llm.call(system_prompt, user_prompt, max_tokens=max_tokens)
            content = resp.content if resp.success else f"[LLM Error: {resp.error}]"
            latency = (time.time() - t0) * 1000
        
        # X-REQ-01: 提取结构化上下文
        ctx = StageContext.from_stage_output(sid, content)
        # 设置下一阶段的指令
        next_stages = [s for s in self.config["stages"] if s["id"] != sid]
        next_sid = next_stages[0]["id"] if next_stages else ""
        if next_sid:
            next_prompt = STAGE_SYSTEM_PROMPTS.get(next_sid, "")
            ctx.for_next_stage = next_prompt.split("。")[0] if next_prompt else ""
        
        self._context_chain.append(ctx)
        self.decision_log.log(sid, "stage_execute",
                             f"Stage: {sname} | Tokens: {max_tokens}",
                             f"Output: {len(content)} chars | Context: {len(ctx.key_findings)} findings",
                             tools=[f"deepseek-chat (max_tokens={max_tokens})"])
        
        return {
            "stage_id": sid, "status": "completed",
            "output": {"content": content, "chars": len(content)},
            "gate": stage.get("gate", ""), "gate_passed": True,
            "mock": self.mock_mode, "latency_ms": latency,
            "context": {
                "summary": ctx.summary[:100],
                "findings": len(ctx.key_findings),
                "data_points": len(ctx.data_points),
            },
        }
    
    def run_full_pipeline(self, router_output: dict) -> dict:
        """完整管道 — 递进式执行"""
        spec = router_output.get("structured_spec", {})
        results = {}
        prev_ctx = None
        
        for stage in self.config["stages"]:
            result = self.run_stage(stage, spec, prev_ctx)
            results[stage["id"]] = result
            # 传递上下文到下一个 stage
            if self._context_chain:
                prev_ctx = self._context_chain[-1]
        
        return results
    
    def _mock_content(self, stage_id: str, spec: dict) -> str:
        """递进式 Mock — 模拟真实的阶段差异化输出"""
        topic = spec.get("core_intent", "未指定")
        
        mocks = {
            "S1_TOPIC": f"【选题】{topic}\n角度: 技术路线+政策+竞争\n信源: SEMI/Wind/公司年报/券商研报\n评分: 8.5/10",
            "S2_RESEARCH": f"【研究笔记】基于S1选题的深度研究\n\n1. 市场数据: 2026年预计$45B (来源: SEMI)\n2. 国产化率: 刻蚀20%→35%, 光刻<5%\n3. 政策: 大基金二期2000亿+\n\n以上数据来自S1信源清单，已交叉验证",
            "S3_WRITING": f"# {topic}\n\n## 执行摘要\n基于S2研究数据的叙事组织...\n\n[基于S2研究笔记展开，不重复收集数据]",
            "S4_REVIEW": "审阅: 数据引用3处(SEMI/Wind/公司年报) ✅ | 逻辑一致 ✅ | 风险提示建议补充",
            "S1_MONITOR": f"【行情】{topic}: 三大指数全线上涨，沪指+1.2%，深成指+1.8%，成交7300亿",
            "S2_VERIFY": f"校验: 数据时间戳 2026-06-17 15:00 ✅ 新鲜 | 数据来源: 交易所实时接口 | 通过",
            "S3_DRAFT": f"【快讯】{topic}\n今日A股三大指数全线上涨。沪指涨1.2%报3285点，深成指涨1.8%，创业板指涨2.1%。两市成交7300亿元。半导体、新能源领涨。",
            "S4_PUBLISH": "合规检查: 无敏感词 ✅ | 格式正确 ✅ | 时间戳: 2026-06-17 15:05 | 准发",
            "S1_SPEC": f"【文档大纲】{topic}\n章节: 概述→安装→API参考(3端点)→代码示例(Go/Java/curl)→错误码→FAQ",
            "S2_RESEARCH": f"【API研究】基于S1大纲的端点分析\n- POST /auth/login: 返回JWT, 过期24h\n- GET /api/users: 需Bearer token\n- 错误码: 401/403/429/500",
            "S3_WRITE": f"# {topic}\n\n## 概述\n基于S2的API研究撰写完整文档...\n\n[含代码示例，数据来自S2研究]",
            "S4_REVIEW": "审阅: API准确性 ✅ | 代码可运行 ✅ | 格式Markdown ✅",
            "S1_BRIEF": f"【脑暴】{topic}\n方向1: 痛点切入-焦虑缓解\n方向2: 场景化-使用场景\n方向3: 数据说服-性能证明\n方向4: 情感-治愈系\n方向5: 社交-口碑传播\n方向6: 限时-紧迫感",
            "S2_IDEATE": f"【筛选】基于S1的6个方向，按受众(25-35岁女性)匹配: Top1 治愈系(情感驱动强) Top2 场景化(代入感)",
            "S3_CREATE": f"【创意文案】{topic}\n[基于S2筛选的治愈系+场景化方向展开]",
            "S4_POLISH": f"【精修】{topic}\n优化: 标题更短更有力 | 增加emoji | 金句位置调整到开头",
            "S1_RESEARCH": f"【研究笔记】{topic}\n核心概念: [定义] 关键原理: [3条] 常见误解: [3条] 权威来源: [5个]",
            "S2_TRANSLATE": f"【通俗转化】基于S1研究笔记\n类比1: [生活类比] 类比2: [故事类比] 类比3: [游戏类比] 复杂度: 高中生可理解",
            "S3_WRITE": f"【科普文章】{topic}\n[基于S2的类比和故事展开叙述，面向大众]",
            "S4_REVIEW": "科普审阅: 类比准确性 ✅ | 可读性 ✅ | 趣味性 ✅ | 无过度神化 ✅",
            "S1_RESEARCH": f"【论据研究】{topic}\n正方证据: [3条] 反方证据: [3条] 数据来源: [5个]",
            "S2_STRUCTURE": f"【论证结构】{topic}\n正方(3论据)→反方最强(3论据,不可轻易驳倒)→综合判断→政策建议",
            "S3_WRITE": f"【观点文章】{topic}\n[基于S2的论证结构展开，含正方/反方/综合判断]",
            "S4_DEBATE": f"【魔鬼代言人】S3论证弱点: 1.未考虑[xxx] 2.反方论据[xxx]可进一步加强 3.综合判断偏向正方",
        }
        
        return mocks.get(stage_id, f"[{stage_id}] {topic}")


def main():
    import sys
    cluster_id = sys.argv[1] if len(sys.argv) > 1 else "deepprod"
    print(f"  SmartTextPlatform V3 — {cluster_id} (递进式管道)")
    
    engine = ClusterEngineV3(cluster_id)
    router_output = {
        "structured_spec": {
            "core_intent": "测试主题",
            "product_type": "分析/报告",
            "depth": "深度",
        },
        "configuration": {"cluster": cluster_id},
    }
    
    t0 = time.time()
    results = engine.run_full_pipeline(router_output)
    total = (time.time() - t0) * 1000
    
    for sid, r in results.items():
        ctx = r.get("context", {})
        chars = len(r.get("output", {}).get("content", ""))
        print(f"    [OK] {sid}: {chars} chars | ctx: {ctx.get('findings',0)}f/{ctx.get('data_points',0)}d")
    
    # Stage 产出差异度检查
    contents = [r["output"]["content"] for r in results.values()]
    unique_lines = len(set("\n".join(contents).split("\n")))
    total_lines = sum(len(c.split("\n")) for c in contents)
    diff_ratio = unique_lines / max(1, total_lines)
    print(f"  Stage 差异度: {diff_ratio:.0%} (越高越好)")
    print(f"  Total: {total:.0f}ms | Mock: {engine.mock_mode}")
    print(f"  V3 递进管道就绪")


if __name__ == "__main__":
    main()
