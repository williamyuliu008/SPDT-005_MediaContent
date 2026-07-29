"""
SmartTextPlatform Phase 2 — Cluster Engine with LLM
=====================================================
升级: 每个集群 stage 接入 LLMGateway 生成实际内容
"""
import sys, os, json, yaml, logging, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.llm_gateway import LLMGateway, ClusterLLMWriter, LLMResponse
from shared.decision_log import DecisionLogger
from shared.artifact import ArtifactBus
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("stp.engine")

class ClusterEngine:
    """通用集群引擎 — 支持 LLM 集成"""
    
    def __init__(self, cluster_id: str, config_path: str = None):
        self.cluster_id = cluster_id
        base = Path(__file__).parent.parent.parent
        
        if config_path is None:
            config_path = base / "clusters" / cluster_id / "cluster.yaml"
        if not os.path.exists(config_path):
            # Fallback: search relative to cluster_engine.py
            alt = Path(__file__).parent.parent / "clusters" / cluster_id / "cluster.yaml"
            if os.path.exists(alt):
                config_path = str(alt)
        
        self.config = yaml.safe_load(open(config_path, 'r', encoding='utf-8'))
        self.llm_writer = ClusterLLMWriter(cluster_id)
        self.decision_log = DecisionLogger(cluster_id)
        self.artifact_bus = ArtifactBus()
        
        # 无 API key 时使用 mock 模式
        self.mock_mode = not self.llm_writer.llm.api_key
    
    def run_stage(self, stage: dict, spec: dict, prev_output: dict = None) -> dict:
        """执行单个 Stage — 含 LLM 调用"""
        sid = stage["id"]
        sname = stage["name"]
        
        stage_context = f"Stage: {sid} ({sname})"
        if prev_output:
            stage_context += f"\n前序产出: {json.dumps(prev_output, ensure_ascii=False)[:500]}"
        
        t0 = time.time()
        
        if self.mock_mode:
            # Mock: 返回模拟内容
            content = self._mock_content(sid, spec)
            latency = (time.time() - t0) * 1000
            self.decision_log.log(sid, f"mock_generate", 
                                 f"Spec: {spec.get('core_intent', '')[:50]}",
                                 f"Generated {len(content)} chars in {latency:.0f}ms")
            return {
                "stage_id": sid, "status": "completed",
                "output": {"content": content, "chars": len(content)},
                "gate": stage.get("gate", ""), "gate_passed": True,
                "mock": True, "latency_ms": latency,
            }
        
        # Real LLM call
        resp = self.llm_writer.write(
            structured_spec=spec,
            l2_config=spec.get("l2_config", {}),
            stage_context=stage_context,
        )
        
        latency = (time.time() - t0) * 1000
        self.decision_log.log(sid, f"llm_generate",
                             f"Spec: {spec.get('core_intent', '')[:50]}",
                             f"Tokens: {resp.tokens_used}, Latency: {latency:.0f}ms",
                             tools=[f"deepseek-chat (max_tokens={resp.tokens_used})"])
        
        return {
            "stage_id": sid, "status": "completed" if resp.success else "failed",
            "output": {
                "content": resp.content,
                "tokens": resp.tokens_used,
                "model": resp.model,
            },
            "gate": stage.get("gate", ""),
            "gate_passed": resp.success,
            "mock": False,
            "latency_ms": latency,
            "error": resp.error if not resp.success else "",
        }
    
    def _mock_content(self, stage_id: str, spec: dict) -> str:
        """生成模拟内容（无 API key 时）"""
        topic = spec.get("core_intent", "未指定")
        product_type = spec.get("product_type", "")
        
        mock_outputs = {
            "S1_TOPIC": f"【选题方案】{topic}\n价值评分: 8.5/10\n建议角度: 技术路线对比+政策驱动+竞争格局",
            "S2_RESEARCH": f"【研究报告】{topic}\n\n1. 市场规模: 全球XX市场预计2026年达到$45B\n2. 主要玩家: A(30%)、B(25%)、C(15%)\n3. 技术趋势: AI驱动、国产替代加速\n4. 政策环境: 国家大基金持续投入\n\n数据来源: SEMI报告、Wind、公司年报",
            "S3_WRITING": f"""# {topic}

## 执行摘要

本报告深入分析了{topic}。通过产业链全景扫描、技术路线对比、竞争格局分析和政策环境评估，核心结论：

1. 市场规模: 全球市场预计2026年达到$45B，CAGR 22%
2. 技术突破: 刻蚀和薄膜沉积设备国产化率从15%提升至35%
3. 竞争格局: 国际三巨头仍占60%+份额，国产替代加速
4. 投资机会: 关注刻蚀、薄膜沉积、清洗设备三大细分赛道

## 产业链全景

半导体设备产业链包括上游零部件（真空泵、射频电源、阀门）、中游设备制造、下游晶圆厂应用。上游核心零部件仍高度依赖进口，但国内企业加速突破。

## 技术路线对比

刻蚀设备: 中微公司/北方华创 vs Lam Research/TEL，国产化率20%
薄膜沉积: 北方华创/拓荆科技 vs Applied Materials，国产化率25%
光刻设备: 上海微电子 vs ASML，国产化率<5%（最大瓶颈）
清洗设备: 盛美半导体 vs DNS/Lam，国产化率35%
检测设备: 中科飞测 vs KLA，国产化率15%

## 竞争格局

国际三巨头（Applied Materials、Lam Research、TEL）占据全球60%以上市场份额。国内企业在刻蚀、薄膜沉积取得突破，光刻机仍是最大瓶颈。北方华创营收突破200亿元，中微公司5nm刻蚀机进入台积电供应链。

## 政策环境

国家大基金二期投入超过2000亿元，重点支持半导体设备和材料。税收优惠覆盖设备采购和研发投入。科创板为半导体设备企业提供融资通道。

## 投资建议

短期关注国产化率提升最快的刻蚀和薄膜沉积赛道。中长期看好光刻机国产替代的突破性机会。建议关注北方华创、中微公司、拓荆科技、盛美半导体。

---

*本报告由 SmartTextPlatform DeepProd 集群生成*""",
            "S4_REVIEW": "审阅通过。事实核查: 0处错误。一致性: 95%。建议: 增加风险提示部分。",
            "S1_MONITOR": f"【监控发现】{topic} — 沪深两市午间收盘，三大指数全线上涨",
            "S2_VERIFY": "核查通过。数据来源: 沪深交易所、Wind。无误。",
            "S3_DRAFT": f"【A股午间快讯】{topic}\n\n三大指数全线上涨，成交量放大。沪指涨1.2%，深成指涨1.8%，创业板指涨2.1%。",
            "S1_SPEC": f"【技术文档规格】{topic}\n格式: OpenAPI 3.0\n章节: 认证、端点、错误码、示例",
            "S1_BRIEF": f"【创意简报】{topic}\n目标受众: C端用户\n调性: 年轻化、有新意\n核心卖点: 性价比",
            "S2_IDEATE": f"【创意构思】{topic}\n\n角度1: 痛点切入 — 直击用户日常焦虑，建立情感共鸣\n角度2: 场景化 — 用真实使用场景激发购买欲望\n角度3: 数据说服 — 用数字证明产品价值\n\n推荐: 角度1+角度2 组合",
            "S3_CREATE": f"【营销文案】{topic}\n\n🔥 你还在为XXX而烦恼吗？\n\n每天花3分钟，彻底改变你的生活方式。\n\n✨ 核心亮点:\n· 痛点解决: 不再XXX\n· 超值性价比: 仅需XX元\n· 限时优惠: 前100名额外赠送\n\n👉 立即点击了解详情 →",
            "S4_POLISH": f"【润色版】{topic}\n\n🔥 限时特惠 | 告别XXX的最后机会\n\n你值得更好的选择。\n\n立即行动 → 点击领券",
            "S1_RESEARCH": f"【知识研究】{topic}\n\n核心概念: 量子计算利用量子叠加态进行并行计算。传统计算机用0/1二进制，量子比特可同时处于0和1的叠加态，使某些计算（如因数分解）从指数级降为多项式级。\n\n关键人物: Richard Feynman(1982提出)、David Deutsch(量子图灵机)、Peter Shor(Shor算法)\n\n类比: 经典计算机像一本一本翻书，量子计算机像同时翻开所有书。当前阶段相当于1940年代的经典计算机。",
            "S1_STRUCTURE": f"【论证结构】{topic}\n\n论点: AI监管需要全球协作框架，单一国家监管既无效又有害。\n论证路径: 问题(各国各自为政)→ 现状(EU AI Act vs 美国放松 vs 中国分类分级)→ 必要性(技术无国界)→ 方案(三层框架: 技术标准+伦理准则+执行机制)→ 反驳(国家主权论、发展权论、不可行论)→ 结论(协作不是选择而是必然)",
        }
        
        if stage_id in mock_outputs:
            return mock_outputs[stage_id]
        return f"Mock content for {stage_id}: {topic}"
    
    def run_full_pipeline(self, router_output: dict) -> dict:
        """完整管道 — 所有 Stage 含 LLM"""
        spec = router_output.get("structured_spec", {})
        results = {}
        prev_output = None
        
        for stage in self.config["stages"]:
            result = self.run_stage(stage, spec, prev_output)
            results[stage["id"]] = result
            if result.get("output"):
                prev_output = result["output"]
        
        return results


def main():
    cluster_id = os.path.basename(os.path.dirname(__file__))
    print(f"  SmartTextPlatform Phase 2 — {cluster_id}")
    
    engine = ClusterEngine(cluster_id)
    
    # Sample router output
    router_output = {
        "structured_spec": {
            "core_intent": "中国新能源产业深度分析",
            "product_type": "分析/报告",
            "depth": "深度 (>=5000字)",
            "target_audience": "投资人群",
            "domain_tags": ["能源", "金融"],
        },
        "configuration": {"cluster": cluster_id},
    }
    
    t0 = time.time()
    results = engine.run_full_pipeline(router_output)
    total_latency = (time.time() - t0) * 1000
    
    for sid, r in results.items():
        stage = next((s for s in engine.config["stages"] if s["id"] == sid), {})
        gate = r.get("gate", "")
        chars = len(r.get("output", {}).get("content", ""))
        icon = "[OK]" if r.get("gate_passed") else "[FAIL]"
        mock_tag = "[mock]" if r.get("mock") else ""
        print(f"    {icon} {sid}: {stage.get('name','')} → {gate} ({chars} chars) {mock_tag}")
    
    print(f"  Total latency: {total_latency:.0f}ms")
    print(f"  Decision log: {len(engine.decision_log)} entries")
    
    stats = engine.llm_writer.llm.stats()
    if stats["calls"] > 0:
        print(f"  LLM: {stats['calls']} calls, {stats['total_tokens']} tokens, avg {stats['avg_latency_ms']}ms")


if __name__ == "__main__":
    main()
