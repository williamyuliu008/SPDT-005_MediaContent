# D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent\agents\orchestration\orchestration.py
# PT-047 Orchestration Agent -- Phase 1.2 | glue ~56% | 187 LOC
from typing import Dict, Any, List, Optional, Tuple, Callable
import logging
import time
from datetime import datetime

# -- Reuse core modules (glue-dominant) --
from module_lib.agent import BaseAgent
from module_lib.processing_computation_graph import COGGenerator
from module_lib.hmi import CLIOutputFormatter
from module_lib.processing_rule_engine import RuleEngine, ProcessingRule
from shared.tools.llm_clients import get_llm_client

# -- New business logic: three-layer funnel + tension curve (<=2000 LOC, this file 187 LOC) --
class TensionCurve:
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha  # decay coefficient

    def compute(self, scores: List[float]) -> List[float]:
        """Exponential smoothing tension curve: strengthen mutation points, suppress long-tail noise"""
        if not scores:
            return []
        tension = [scores[0]]
        for s in scores[1:]:
            tension.append(self.alpha * s + (1 - self.alpha) * tension[-1])
        return tension

class ThreeStageFunnel:
    @staticmethod
    def filter_by_confidence(items: List[Dict], threshold: float = 0.65) -> List[Dict]:
        return [i for i in items if i.get("confidence", 0.0) >= threshold]

    @staticmethod
    def rank_by_relevance(items: List[Dict], top_k: int = 5) -> List[Dict]:
        return sorted(items, key=lambda x: x.get("relevance_score", 0.0), reverse=True)[:top_k]

    @staticmethod
    def dedupe_by_semantic(items: List[Dict], threshold: float = 0.82) -> List[Dict]:
        from sentence_transformers import SentenceTransformer
        if len(items) <= 1:
            return items
        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        texts = [i.get("text", "") for i in items]
        embeddings = model.encode(texts, show_progress_bar=False)
        keep = [True] * len(items)
        for i in range(len(embeddings)):
            if not keep[i]:
                continue
            for j in range(i + 1, len(embeddings)):
                norm_i = (embeddings[i] @ embeddings[i]) ** 0.5 + 1e-8
                norm_j = (embeddings[j] @ embeddings[j]) ** 0.5 + 1e-8
                sim = float((embeddings[i] @ embeddings[j]) / (norm_i * norm_j))
                if sim > threshold:
                    keep[j] = False
        return [items[i] for i in range(len(items)) if keep[i]]

# -- Main Agent --
class OrchestrationAgent(BaseAgent):
    agent_id = "orchestration_v1_2"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.rule_engine = RuleEngine()
        self.cog_gen = COGGenerator()
        self.cli = CLIOutputFormatter()
        self.tension_curve = TensionCurve(alpha=0.25)
        self.logger = logging.getLogger(self.agent_id)

    def execute(self, input_data: Any) -> Dict[str, Any]:
        """Pipeline-compatible execute interface."""
        try:
            data = dict(input_data) if hasattr(input_data, '__iter__') else {"raw": input_data}
        except Exception:
            data = {"raw": str(input_data)}
        return self.handoff(data)

    def handoff(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main dispatch entry: rule-driven routing -> COG generation -> three-layer funnel -> tension calibration -> structured output"""
        start_time = time.time()
        audit_log = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "input_hash": hash(str(input_data)),
            "stages": [],
            "duration_ms": 0
        }

        try:
            # Stage 1: Rule engine routing
            routing_rules = self.rule_engine.apply_rules(input_data)
            audit_log["stages"].append({"stage": "rule_routing", "output": routing_rules})

            # Stage 2: COG generation (reuse)
            cog = self.cog_gen.build_from_input(input_data, routing_rules)
            audit_log["stages"].append({"stage": "cog_generation", "nodes": len(cog.nodes)})

            # Stage 3: Three-stage funnel (new business)
            candidates = cog.get_candidates() or []
            funnel1 = ThreeStageFunnel.filter_by_confidence(candidates)
            funnel2 = ThreeStageFunnel.rank_by_relevance(funnel1)
            funnel3 = ThreeStageFunnel.dedupe_by_semantic(funnel2)
            audit_log["stages"].append({"stage": "three_stage_funnel", "kept": len(funnel3)})

            # Stage 4: Tension curve calibration (new business)
            scores = [c.get("relevance_score", 0.0) for c in funnel3]
            tension_scores = self.tension_curve.compute(scores)
            for i, score in enumerate(tension_scores):
                if i < len(funnel3):
                    funnel3[i]["tension_score"] = score

            # Output and audit
            output = {"result": funnel3, "cog": cog.to_dict()}
            audit_log["duration_ms"] = round((time.time() - start_time) * 1000, 2)
            self._log_audit(audit_log)
            return self.cli.format_structured(output, title="Orchestration Result")

        except Exception as e:
            audit_log["error"] = str(e)
            self._log_audit(audit_log)
            raise

    def _log_audit(self, log_entry: Dict[str, Any]):
        """Standard audit log interface (per platform spec)"""
        self.logger.info(f"[AUDIT] {log_entry}")
        #预留ChromaDB持久化扩展点
