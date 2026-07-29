import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from module_lib.agent import BaseAgent, AgentConfig, AgentMessage
from module_lib.processing_computation_graph import ComputationGraph, GraphNode, GraphEdge
from module_lib.hmi import CLIOutput, CLIInput
from shared.tools.llm_clients import LLMClient, LLMResponse
class ReflectionConfig(BaseModel):
    agent_id: str = "reflection_agent_047"
    max_iterations: int = 3
    confidence_threshold: float = 0.75
    tension_threshold: float = 0.6
    funnel_stages: List[str] = ["surface", "deep", "core"]
class AuditEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: str
    action: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
class FunnelResult(BaseModel):
    stage: str
    score: float
    insights: List[str]
    tension_value: float
class ReflectionResult(BaseModel):
    final_insights: List[str]
    confidence: float
    tension_curve: List[float]
    funnel_results: List[FunnelResult]
    audit_trail: List[AuditEntry]
class RuleEngine:
    def __init__(self, rules: Optional[List[Dict[str, Any]]] = None):
        self.rules = rules or self._default_rules()
        self.audit_log: List[AuditEntry] = []
    def _default_rules(self) -> List[Dict[str, Any]]:
        return [
            {"id": "rule_001", "condition": "confidence < 0.5", "action": "reprocess"},
            {"id": "rule_002", "condition": "tension > 0.8", "action": "flag_for_review"},
            {"id": "rule_003", "condition": "insight_count < 3", "action": "expand_search"}
        ]
    def evaluate(self, context: Dict[str, Any]) -> List[str]:
        actions = []
        for rule in self.rules:
            if self._check_condition(rule["condition"], context):
                actions.append(rule["action"])
                self._log_action("rule_evaluation", {"rule_id": rule["id"], "action": rule["action"]})
        return actions
    def _check_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        try:
            if "confidence <" in condition:
                threshold = float(condition.split("<")[1].strip())
                return context.get("confidence", 1.0) < threshold
            elif "tension >" in condition:
                threshold = float(condition.split(">")[1].strip())
                return context.get("tension", 0.0) > threshold
            elif "insight_count <" in condition:
                threshold = int(condition.split("<")[1].strip())
                return len(context.get("insights", [])) < threshold
            return False
        except:
            return False
    def _log_action(self, action: str, metadata: Dict[str, Any]) -> None:
        entry = AuditEntry(
            agent_id="rule_engine",
            action=action,
            metadata=metadata
        )
        self.audit_log.append(entry)
class ThreeLayerFunnel:
    def __init__(self):
        self.stages = ["surface", "deep", "core"]
        self.stage_weights = {"surface": 0.3, "deep": 0.5, "core": 0.8}
    def process(self, input_data: Dict[str, Any]) -> List[FunnelResult]:
        results = []
        current_data = input_data.copy()
        for stage in self.stages:
            stage_result = self._process_stage(stage, current_data)
            results.append(stage_result)
            current_data["refined_insights"] = stage_result.insights
            current_data["stage_score"] = stage_result.score
        return results
    def _process_stage(self, stage: str, data: Dict[str, Any]) -> FunnelResult:
        if stage == "surface":
            insights = self._surface_analysis(data)
            score = self._calculate_score(insights, stage)
        elif stage == "deep":
            insights = self._deep_analysis(data)
            score = self._calculate_score(insights, stage)
        else:
            insights = self._core_analysis(data)
            score = self._calculate_score(insights, stage)
        tension = self._calculate_tension(insights, stage)
        return FunnelResult(stage=stage, score=score, insights=insights, tension_value=tension)
    def _surface_analysis(self, data: Dict[str, Any]) -> List[str]:
        raw_text = data.get("text", "")
        insights = []
        if len(raw_text) > 50:
            insights.append(f"Surface pattern detected: length={len(raw_text)}")
        keywords = data.get("keywords", [])
        if keywords:
            insights.append(f"Keywords identified: {', '.join(keywords[:3])}")
        if not insights:
            insights.append("No surface patterns found")
        return insights
    def _deep_analysis(self, data: Dict[str, Any]) -> List[str]:
        insights = data.get("refined_insights", [])
        score = data.get("stage_score", 0.0)
        deep_insights = []
        for insight in insights:
            if score > 0.4:
                deep_insights.append(f"Deep analysis: {insight} (confidence: {score:.2f})")
        if not deep_insights:
            deep_insights.append("Deep analysis yielded no additional insights")
        return deep_insights
    def _core_analysis(self, data: Dict[str, Any]) -> List[str]:
        insights = data.get("refined_insights", [])
        score = data.get("stage_score", 0.0)
        core_insights = []
        for insight in insights:
            if score > 0.6:
                core_insights.append(f"Core insight extracted: {insight}")
        if not core_insights:
            core_insights.append("Core analysis complete - no critical insights")
        return core_insights
    def _calculate_score(self, insights: List[str], stage: str) -> float:
        base_score = len(insights) * 0.2
        weight = self.stage_weights.get(stage, 0.5)
        return min(base_score * weight, 1.0)
    def _calculate_tension(self, insights: List[str], stage: str) -> float:
        if not insights:
            return 0.0
        tension = len(insights) * 0.15
        if "no" in insights[0].lower() or "not" in insights[0].lower():
            tension += 0.2
        return min(tension, 1.0)
class TensionCurveGenerator:
    def __init__(self):
        self.curve_points: List[float] = []
    def generate(self, funnel_results: List[FunnelResult]) -> List[float]:
        self.curve_points = []
        for result in funnel_results:
            tension = result.tension_value
            stage_weight = self._get_stage_weight(result.stage)
            adjusted_tension = tension * stage_weight
            self.curve_points.append(adjusted_tension)
        return self._smooth_curve(self.curve_points)
    def _get_stage_weight(self, stage: str) -> float:
        weights = {"surface": 0.4, "deep": 0.7, "core": 1.0}
        return weights.get(stage, 0.5)
    def _smooth_curve(self, points: List[float]) -> List[float]:
        if len(points) < 2:
            return points
        smoothed = [points[0]]
        for i in range(1, len(points) - 1):
            smoothed.append((points[i-1] + points[i] + points[i+1]) / 3)
        smoothed.append(points[-1])
        return smoothed
class ReflectionAgent(BaseAgent):
    def __init__(self, config: Optional[ReflectionConfig] = None):
        _cfg = config or ReflectionConfig()
        super().__init__(AgentConfig(agent_id=_cfg.agent_id))
        self._reflection_cfg = _cfg  # Pydantic config (avoids conflict with BaseAgent.config)
        self.rule_engine = RuleEngine()
        self.funnel = ThreeLayerFunnel()
        self.tension_curve_gen = TensionCurveGenerator()
        self.llm_client = LLMClient()
        self.computation_graph = ComputationGraph()
        self.audit_trail: List[AuditEntry] = []
        self._setup_graph()

    def _setup_graph(self) -> None:
        cfg = self._reflection_cfg
        node_input = GraphNode(id="input", type="input", config={})
        node_funnel = GraphNode(id="funnel", type="process", config={"stages": cfg.funnel_stages})
        node_tension = GraphNode(id="tension", type="process", config={})
        node_rules = GraphNode(id="rules", type="decision", config={"threshold": cfg.confidence_threshold})
        node_output = GraphNode(id="output", type="output", config={})
        self.computation_graph.add_node(node_input)
        self.computation_graph.add_node(node_funnel)
        self.computation_graph.add_node(node_tension)
        self.computation_graph.add_node(node_rules)
        self.computation_graph.add_node(node_output)
        self.computation_graph.add_edge(GraphEdge(source="input", target="funnel"))
        self.computation_graph.add_edge(GraphEdge(source="funnel", target="tension"))
        self.computation_graph.add_edge(GraphEdge(source="tension", target="rules"))
        self.computation_graph.add_edge(GraphEdge(source="rules", target="output"))
    def execute(self, input_data: Any) -> Dict[str, Any]:
        """Pipeline-compatible execute interface."""
        try:
            # Wrap dict input as a pseudo-AgentMessage
            msg = type("Msg", (), {
                "sender": "pipeline",
                "payload": dict(input_data) if isinstance(input_data, dict) else {"raw": input_data},
                "msg_type": "pipeline_request"
            })()
            result = self.process_message(msg)
            return result.payload if hasattr(result, "payload") else {}
        except Exception as e:
            return {"error": str(e), "agent_id": self._reflection_cfg.agent_id}

    def process_message(self, message: AgentMessage) -> AgentMessage:
        self._log_audit("process_start", {"sender": message.sender, "msg_type": message.msg_type})
        input_data = message.payload.get("data", {})
        funnel_results = self.funnel.process(input_data)
        tension_curve = self.tension_curve_gen.generate(funnel_results)
        context = {
            "confidence": self._calculate_confidence(funnel_results),
            "tension": tension_curve[-1] if tension_curve else 0.0,
            "insights": [insight for result in funnel_results for insight in result.insights]
        }
        actions = self.rule_engine.evaluate(context)
        final_insights = self._apply_actions(actions, context, funnel_results)
        result = ReflectionResult(
            final_insights=final_insights,
            confidence=context["confidence"],
            tension_curve=tension_curve,
            funnel_results=funnel_results,
            audit_trail=self.audit_trail
        )
        self._log_audit("process_complete", {"result_summary": f"insights={len(final_insights)}, confidence={context['confidence']:.2f}"})
        return AgentMessage(
            sender=self._reflection_cfg.agent_id,
            recipient=message.sender,
            msg_type="reflection_result",
            payload={"result": result.model_dump()}
        )
    def _calculate_confidence(self, funnel_results: List[FunnelResult]) -> float:
        if not funnel_results:
            return 0.0
        scores = [r.score for r in funnel_results]
        return sum(scores) / len(scores)
    def _apply_actions(self, actions: List[str], context: Dict[str, Any], funnel_results: List[FunnelResult]) -> List[str]:
        insights = context.get("insights", [])
        for action in actions:
            if action == "reprocess" and context["confidence"] < self._reflection_cfg.confidence_threshold:
                new_insights = self._llm_refine(insights)
                insights.extend(new_insights)
                self._log_audit("action_reprocess", {"new_insights_count": len(new_insights)})
            elif action == "flag_for_review" and context["tension"] > self._reflection_cfg.tension_threshold:
                insights.append(f"FLAG: High tension detected ({context['tension']:.2f}) - review recommended")
                self._log_audit("action_flag", {"tension": context["tension"]})
            elif action == "expand_search":
                expanded = self._expand_insights(funnel_results)
                insights.extend(expanded)
                self._log_audit("action_expand", {"expanded_count": len(expanded)})
        return insights
    def _llm_refine(self, insights: List[str]) -> List[str]:
        prompt = f"Refine and expand these insights: {json.dumps(insights)}"
        response = self.llm_client.chat(prompt)
        if response and response.content:
            return [response.content]
        return ["LLM refinement produced no additional insights"]
    def _expand_insights(self, funnel_results: List[FunnelResult]) -> List[str]:
        expanded = []
        for result in funnel_results:
            if result.score < 0.5:
                expanded.append(f"Expanding {result.stage} stage analysis")
        return expanded
    def _log_audit(self, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        entry = AuditEntry(
            agent_id=self.config.agent_id,
            action=action,
            metadata=metadata
        )
        self.audit_trail.append(entry)
    def handoff(self, target_agent_id: str, data: Dict[str, Any]) -> AgentMessage:
        self._log_audit("handoff_initiated", {"target": target_agent_id})
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender=self.config.agent_id,
            receiver=target_agent_id,
            message_type="handoff",
            payload={"data": data, "audit": [e.dict() for e in self.audit_trail]}
        )
        return message
    def get_audit_log(self) -> List[AuditEntry]:
        return self.audit_trail
class CLIInterface:
    def __init__(self, agent: ReflectionAgent):
        self.agent = agent
        self.cli_output = CLIOutput()
        self.cli_input = CLIInput()
    def run(self) -> None:
        self.cli_output.display("Reflection Agent CLI Interface")
        self.cli_output.display(f"Agent ID: {self.agent.config.agent_id}")
        while True:
            self.cli_output.display("\nOptions:")
            self.cli_output.display("1. Process text")
            self.cli_output.display("2. View audit log")
            self.cli_output.display("3. Exit")
            choice = self.cli_input.get_input("Select option: ")
            if choice == "1":
                self._process_text()
            elif choice == "2":
                self._show_audit()
            elif choice == "3":
                break
            else:
                self.cli_output.display("Invalid option")
    def _process_text(self) -> None:
        text = self.cli_input.get_input("Enter text to analyze: ")
        keywords_input = self.cli_input.get_input("Enter keywords (comma-separated, optional): ")
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()] if keywords_input else []
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender="cli_user",
            receiver=self.agent.config.agent_id,
            message_type="process_request",
            payload={"data": {"text": text, "keywords": keywords}}
        )
        response = self.agent.process_message(message)
        result_data = response.payload.get("result", {})
        self.cli_output.display("\n--- Reflection Results ---")
        self.cli_output.display(f"Confidence: {result_data.get('confidence', 0.0):.2f}")
        self.cli_output.display(f"Final Insights ({len(result_data.get('final_insights', []))}):")
        for insight in result_data.get("final_insights", []):
            self.cli_output.display(f"  - {insight}")
        self.cli_output.display(f"Tension Curve: {result_data.get('tension_curve', [])}")
        self.cli_output.display("Funnel Results:")
        for fr in result_data.get("funnel_results", []):
            self.cli_output.display(f"  {fr['stage']}: score={fr['score']:.2f}, tension={fr['tension_value']:.2f}")
    def _show_audit(self) -> None:
        audit = self.agent.get_audit_log()
        self.cli_output.display(f"\nAudit Log ({len(audit)} entries):")
        for entry in audit:
            self.cli_output.display(f"  [{entry.timestamp}] {entry.action} - {entry.metadata}")
def main() -> None:
    config = ReflectionConfig(
        agent_id="reflection_agent_047",
        max_iterations=3,
        confidence_threshold=0.75,
        tension_threshold=0.6
    )
    agent = ReflectionAgent(config)
    cli = CLIInterface(agent)
    cli.run()
if __name__ == "__main__":
    main()
