import json
import uuid
import datetime
from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from module_lib.agent import BaseAgent, AgentConfig, AgentMessage, AgentContext
from module_lib.processing_computation_graph import ComputationGraph, GraphNode, GraphEdge
from module_lib.hmi import CLIInterface, MenuItem, OutputFormatter
from shared.tools.llm_clients import LLMClient, LLMConfig
class HistorianConfig(BaseModel):
    agent_id: str = "historio_manager_001"
    version: str = "3.0.0"
    max_history_depth: int = 1000
    enable_audit: bool = True
    funnel_tiers: List[int] = Field(default=[100, 50, 10])
class AuditEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    agent_id: str
    action: str
    source: str
    target: str
    payload: Optional[Dict[str, Any]] = None
    result: Optional[str] = None
class FunnelStage(BaseModel):
    stage_id: int
    input_count: int
    output_count: int
    threshold: float
    filter_criteria: Dict[str, Any]
class TensionCurvePoint(BaseModel):
    timestamp: str
    tension_value: float
    source_agent: str
    context: Dict[str, Any]
class RuleEngine(BaseModel):
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    def add_rule(self, rule: Dict[str, Any]) -> None:
        self.rules.append(rule)
    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        triggered = []
        for rule in self.rules:
            if self._match_condition(rule.get("condition", {}), data):
                triggered.append(rule)
        return triggered
    def _match_condition(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        field = condition.get("field")
        operator = condition.get("operator", "eq")
        value = condition.get("value")
        if field not in data:
            return False
        actual = data[field]
        if operator == "eq":
            return actual == value
        elif operator == "gt":
            return actual > value
        elif operator == "lt":
            return actual < value
        elif operator == "gte":
            return actual >= value
        elif operator == "lte":
            return actual <= value
        elif operator == "in":
            return actual in value
        return False
class ThreeTierFunnel(BaseModel):
    tiers: List[FunnelStage] = Field(default_factory=list)
    def __init__(self, **data):
        super().__init__(**data)
        if not self.tiers:
            self.tiers = [
                FunnelStage(stage_id=1, input_count=0, output_count=0, threshold=0.7, filter_criteria={"relevance": "high"}),
                FunnelStage(stage_id=2, input_count=0, output_count=0, threshold=0.5, filter_criteria={"accuracy": "medium"}),
                FunnelStage(stage_id=3, input_count=0, output_count=0, threshold=0.3, filter_criteria={"completeness": "low"})
            ]
    def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        current_items = items
        for tier in self.tiers:
            tier.input_count = len(current_items)
            filtered = [item for item in current_items if self._passes_tier(item, tier)]
            tier.output_count = len(filtered)
            current_items = filtered
        return current_items
    def _passes_tier(self, item: Dict[str, Any], tier: FunnelStage) -> bool:
        score = 0.0
        total_weight = 0.0
        for criterion, weight in tier.filter_criteria.items():
            if criterion in item:
                score += item[criterion] * 1.0
                total_weight += 1.0
        if total_weight == 0:
            return False
        avg_score = score / total_weight
        return avg_score >= tier.threshold
class TensionCurveAnalyzer(BaseModel):
    points: List[TensionCurvePoint] = Field(default_factory=list)
    max_points: int = 1000
    def add_point(self, point: TensionCurvePoint) -> None:
        self.points.append(point)
        if len(self.points) > self.max_points:
            self.points = self.points[-self.max_points:]
    def get_trend(self, window: int = 10) -> float:
        if len(self.points) < 2:
            return 0.0
        recent = self.points[-window:] if len(self.points) >= window else self.points
        values = [p.tension_value for p in recent]
        if len(values) < 2:
            return 0.0
        return (values[-1] - values[0]) / len(values)
    def get_volatility(self, window: int = 10) -> float:
        if len(self.points) < 2:
            return 0.0
        recent = self.points[-window:] if len(self.points) >= window else self.points
        values = [p.tension_value for p in recent]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5
class HistorioManagerAgent(BaseAgent):
    def __init__(self, config: Optional[HistorianConfig] = None):
        if config is None:
            config = HistorianConfig()
        agent_config = AgentConfig(
            agent_id=config.agent_id,
            version=config.version,
            capabilities=["history_management", "funnel_processing", "tension_analysis", "audit_logging"]
        )
        super().__init__(agent_config)
        self.historian_config = config
        self.audit_log: List[AuditEntry] = []
        self.rule_engine = RuleEngine()
        self.funnel = ThreeTierFunnel()
        self.tension_analyzer = TensionCurveAnalyzer()
        self.computation_graph = ComputationGraph()
        self.cli = CLIInterface()
        self.llm_client = LLMClient(LLMConfig(model_name="gpt-4"))
        self._initialize_default_rules()
        self._initialize_computation_graph()
    def _initialize_default_rules(self) -> None:
        self.rule_engine.add_rule({
            "rule_id": "high_tension_alert",
            "condition": {"field": "tension_value", "operator": "gt", "value": 0.8},
            "action": "alert",
            "priority": 1
        })
        self.rule_engine.add_rule({
            "rule_id": "low_relevance_filter",
            "condition": {"field": "relevance", "operator": "lt", "value": 0.3},
            "action": "discard",
            "priority": 2
        })
        self.rule_engine.add_rule({
            "rule_id": "audit_required",
            "condition": {"field": "source", "operator": "eq", "value": "external"},
            "action": "log_audit",
            "priority": 3
        })
    def _initialize_computation_graph(self) -> None:
        node_input = GraphNode(node_id="input", node_type="source", config={"handler": "receive_data"})
        node_funnel = GraphNode(node_id="funnel", node_type="processor", config={"handler": "apply_funnel"})
        node_tension = GraphNode(node_id="tension", node_type="analyzer", config={"handler": "analyze_tension"})
        node_rules = GraphNode(node_id="rules", node_type="evaluator", config={"handler": "evaluate_rules"})
        node_output = GraphNode(node_id="output", node_type="sink", config={"handler": "produce_result"})
        self.computation_graph.add_node(node_input)
        self.computation_graph.add_node(node_funnel)
        self.computation_graph.add_node(node_tension)
        self.computation_graph.add_node(node_rules)
        self.computation_graph.add_node(node_output)
        self.computation_graph.add_edge(GraphEdge(source_id="input", target_id="funnel"))
        self.computation_graph.add_edge(GraphEdge(source_id="funnel", target_id="tension"))
        self.computation_graph.add_edge(GraphEdge(source_id="tension", target_id="rules"))
        self.computation_graph.add_edge(GraphEdge(source_id="rules", target_id="output"))
    def handoff(self, target_agent_id: str, message: AgentMessage) -> AgentMessage:
        audit_entry = AuditEntry(
            agent_id=self.config.agent_id,
            action="handoff",
            source=self.config.agent_id,
            target=target_agent_id,
            payload={"message_id": message.message_id}
        )
        self.audit_log.append(audit_entry)
        response = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.config.agent_id,
            receiver_id=target_agent_id,
            content=message.content,
            message_type="handoff_response"
        )
        return response
    def receive_message(self, message: AgentMessage) -> AgentMessage:
        audit_entry = AuditEntry(
            agent_id=self.config.agent_id,
            action="receive",
            source=message.sender_id,
            target=self.config.agent_id,
            payload={"message_type": message.message_type}
        )
        self.audit_log.append(audit_entry)
        if message.message_type == "process_history":
            result = self._process_history_data(message.content)
        elif message.message_type == "analyze_tension":
            result = self._analyze_tension_request(message.content)
        elif message.message_type == "apply_funnel":
            result = self._apply_funnel_request(message.content)
        else:
            result = {"status": "unknown_message_type", "original": message.content}
        return AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.config.agent_id,
            receiver_id=message.sender_id,
            content=result,
            message_type="response"
        )
    def _process_history_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        items = data.get("items", [])
        funnel_result = self.funnel.process(items)
        tension_point = TensionCurvePoint(
            timestamp=datetime.datetime.utcnow().isoformat(),
            tension_value=data.get("tension_value", 0.5),
            source_agent=data.get("source_agent", "unknown"),
            context={"funnel_output_count": len(funnel_result)}
        )
        self.tension_analyzer.add_point(tension_point)
        rule_results = self.rule_engine.evaluate({"tension_value": tension_point.tension_value, "source": data.get("source_agent", "unknown")})
        result = {
            "funnel_output": funnel_result,
            "tension_trend": self.tension_analyzer.get_trend(),
            "tension_volatility": self.tension_analyzer.get_volatility(),
            "triggered_rules": [r["rule_id"] for r in rule_results],
            "processed_at": datetime.datetime.utcnow().isoformat()
        }
        audit_entry = AuditEntry(
            agent_id=self.config.agent_id,
            action="process_history",
            source="internal",
            target="self",
            payload={"input_count": len(items), "output_count": len(funnel_result)},
            result=json.dumps(result)
        )
        self.audit_log.append(audit_entry)
        return result
    def _analyze_tension_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        point = TensionCurvePoint(
            timestamp=data.get("timestamp", datetime.datetime.utcnow().isoformat()),
            tension_value=data.get("tension_value", 0.0),
            source_agent=data.get("source_agent", "unknown"),
            context=data.get("context", {})
        )
        self.tension_analyzer.add_point(point)
        return {
            "trend": self.tension_analyzer.get_trend(),
            "volatility": self.tension_analyzer.get_volatility(),
            "point_count": len(self.tension_analyzer.points)
        }
    def _apply_funnel_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        items = data.get("items", [])
        result = self.funnel.process(items)
        return {
            "filtered_items": result,
            "input_count": len(items),
            "output_count": len(result),
            "tier_stats": [{"stage": t.stage_id, "input": t.input_count, "output": t.output_count} for t in self.funnel.tiers]
        }
    def get_audit_log(self, limit: int = 100) -> List[AuditEntry]:
        return self.audit_log[-limit:]
    def clear_audit_log(self) -> None:
        self.audit_log.clear()
    def run_cli(self) -> None:
        def show_status():
            return {
                "agent_id": self.config.agent_id,
                "version": self.config.version,
                "audit_count": len(self.audit_log),
                "tension_points": len(self.tension_analyzer.points),
                "funnel_tiers": [t.stage_id for t in self.funnel.tiers]
            }
        def process_data():
            data = {"items": [{"relevance": 0.9, "accuracy": 0.8, "completeness": 0.7}, {"relevance": 0.4, "accuracy": 0.3, "completeness": 0.2}], "tension_value": 0.6, "source_agent": "test"}
            return self._process_history_data(data)
        def show_audit():
            return self.get_audit_log(10)
        menu = MenuItem("historio_manager", [
            MenuItem("status", show_status),
            MenuItem("process_data", process_data),
            MenuItem("audit_log", show_audit),
            MenuItem("exit", lambda: {"action": "exit"})
        ])
        self.cli.run(menu)
    def execute_computation_graph(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        context = {"input": input_data}
        for node in self.computation_graph.nodes:
            if node.node_id == "input":
                context["current_data"] = input_data
            elif node.node_id == "funnel":
                context["current_data"] = self.funnel.process(context.get("current_data", []))
            elif node.node_id == "tension":
                point = TensionCurvePoint(
                    timestamp=datetime.datetime.utcnow().isoformat(),
                    tension_value=input_data.get("tension_value", 0.5),
                    source_agent=self.config.agent_id,
                    context={"data_size": len(context.get("current_data", []))}
                )
                self.tension_analyzer.add_point(point)
                context["tension_analysis"] = {"trend": self.tension_analyzer.get_trend(), "volatility": self.tension_analyzer.get_volatility()}
            elif node.node_id == "rules":
                context["rule_results"] = self.rule_engine.evaluate({"tension_value": input_data.get("tension_value", 0.5), "source": "graph"})
            elif node.node_id == "output":
                context["output"] = {
                    "data": context.get("current_data", []),
                    "tension": context.get("tension_analysis", {}),
                    "rules": context.get("rule_results", [])
                }
        return context.get("output", {})
def create_agent() -> HistorioManagerAgent:
    config = HistorianConfig()
    agent = HistorioManagerAgent(config)
    return agent
if __name__ == "__main__":
    agent = create_agent()
    agent.run_cli()
