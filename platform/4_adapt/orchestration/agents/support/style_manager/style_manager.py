import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from module_lib.agent import BaseAgent, AgentConfig, AgentMessage
from module_lib.processing_computation_graph import ComputationGraph, GraphNode, GraphEdge
from module_lib.hmi import CLIOutput, StructuredOutput
from module_lib.processing_rule_engine import RuleEngine, Rule
from shared.tools.llm_clients import LLMClient
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class StyleProfile(BaseModel):
    style_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    tone: str = "neutral"
    formality: float = 0.5
    complexity: float = 0.5
    creativity: float = 0.5
    constraints: List[str] = []
    metadata: Dict[str, Any] = {}
class StyleEvaluation(BaseModel):
    evaluation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    style_id: str
    score: float
    confidence: float
    details: Dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
class TensionCurvePoint(BaseModel):
    position: float
    tension: float
    label: Optional[str] = None
class TensionCurve(BaseModel):
    curve_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    points: List[TensionCurvePoint] = []
    metadata: Dict[str, Any] = {}
class AuditLogEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    action: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Dict[str, Any] = {}
class StyleManagerConfig(AgentConfig):
    agent_id: str = "style_manager_001"
    name: str = "StyleManager"
    version: str = "1.0.0"
    max_styles: int = 100
    default_formality: float = 0.5
    default_complexity: float = 0.5
    default_creativity: float = 0.5
class StyleManagerAgent(BaseAgent):
    def __init__(self, config: StyleManagerConfig):
        super().__init__(config)
        self.config = config
        self.styles: Dict[str, StyleProfile] = {}
        self.evaluations: Dict[str, StyleEvaluation] = {}
        self.tension_curves: Dict[str, TensionCurve] = {}
        self.audit_log: List[AuditLogEntry] = []
        self.rule_engine = RuleEngine()
        self.computation_graph = ComputationGraph()
        self.llm_client = LLMClient()
        self.cli_output = CLIOutput()
        self.structured_output = StructuredOutput()
        self._initialize_rules()
        self._initialize_graph()
    def _initialize_rules(self):
        formality_rule = Rule(
            rule_id="formality_check",
            condition=lambda style: 0.0 <= style.formality <= 1.0,
            action=lambda style: logger.info(f"Formality check passed for {style.name}")
        )
        self.rule_engine.add_rule(formality_rule)
        complexity_rule = Rule(
            rule_id="complexity_check",
            condition=lambda style: 0.0 <= style.complexity <= 1.0,
            action=lambda style: logger.info(f"Complexity check passed for {style.name}")
        )
        self.rule_engine.add_rule(complexity_rule)
        creativity_rule = Rule(
            rule_id="creativity_check",
            condition=lambda style: 0.0 <= style.creativity <= 1.0,
            action=lambda style: logger.info(f"Creativity check passed for {style.name}")
        )
        self.rule_engine.add_rule(creativity_rule)
    def _initialize_graph(self):
        input_node = GraphNode(node_id="input", node_type="input", config={})
        process_node = GraphNode(node_id="process", node_type="process", config={"function": "style_processing"})
        output_node = GraphNode(node_id="output", node_type="output", config={})
        self.computation_graph.add_node(input_node)
        self.computation_graph.add_node(process_node)
        self.computation_graph.add_node(output_node)
        self.computation_graph.add_edge(GraphEdge(source_id="input", target_id="process"))
        self.computation_graph.add_edge(GraphEdge(source_id="process", target_id="output"))
    def _log_audit(self, action: str, details: Dict[str, Any] = None):
        entry = AuditLogEntry(
            agent_id=self.config.agent_id,
            action=action,
            details=details or {}
        )
        self.audit_log.append(entry)
        logger.info(f"Audit: {action} - {details}")
    def _three_layer_funnel(self, style: StyleProfile) -> Tuple[bool, float, Dict[str, Any]]:
        layer1_score = self._layer1_basic_validation(style)
        if layer1_score < 0.3:
            return False, layer1_score, {"layer": 1, "reason": "Basic validation failed"}
        layer2_score = self._layer2_consistency_check(style)
        if layer2_score < 0.5:
            return False, layer2_score, {"layer": 2, "reason": "Consistency check failed"}
        layer3_score = self._layer3_quality_assessment(style)
        if layer3_score < 0.7:
            return False, layer3_score, {"layer": 3, "reason": "Quality assessment failed"}
        final_score = (layer1_score + layer2_score + layer3_score) / 3.0
        return True, final_score, {"layer1": layer1_score, "layer2": layer2_score, "layer3": layer3_score}
    def _layer1_basic_validation(self, style: StyleProfile) -> float:
        score = 1.0
        if not style.name or len(style.name.strip()) == 0:
            score -= 0.3
        if not style.description or len(style.description.strip()) < 10:
            score -= 0.2
        if style.formality < 0.0 or style.formality > 1.0:
            score -= 0.2
        if style.complexity < 0.0 or style.complexity > 1.0:
            score -= 0.2
        if style.creativity < 0.0 or style.creativity > 1.0:
            score -= 0.1
        return max(0.0, score)
    def _layer2_consistency_check(self, style: StyleProfile) -> float:
        score = 1.0
        if abs(style.formality - style.complexity) > 0.7:
            score -= 0.2
        if style.formality > 0.8 and style.creativity > 0.8:
            score -= 0.2
        if style.complexity < 0.2 and style.creativity > 0.8:
            score -= 0.1
        if len(style.constraints) > 5:
            score -= 0.1
        return max(0.0, score)
    def _layer3_quality_assessment(self, style: StyleProfile) -> float:
        score = 0.7
        if style.formality > 0.3 and style.formality < 0.7:
            score += 0.1
        if style.complexity > 0.3 and style.complexity < 0.7:
            score += 0.1
        if style.creativity > 0.3 and style.creativity < 0.7:
            score += 0.1
        if len(style.description) > 50:
            score += 0.05
        if len(style.constraints) > 0:
            score += 0.05
        return min(1.0, score)
    def _generate_tension_curve(self, style: StyleProfile) -> TensionCurve:
        points = []
        for i in range(11):
            position = i / 10.0
            tension = style.formality * (1 - position) + style.creativity * position
            tension = tension * (1 + style.complexity * 0.2)
            tension = min(1.0, max(0.0, tension))
            label = f"Point_{i}" if i % 2 == 0 else None
            points.append(TensionCurvePoint(position=position, tension=tension, label=label))
        curve = TensionCurve(points=points, metadata={"style_id": style.style_id, "style_name": style.name})
        self.tension_curves[curve.curve_id] = curve
        return curve
    def create_style(self, name: str, description: str, tone: str = "neutral",
                     formality: float = None, complexity: float = None,
                     creativity: float = None, constraints: List[str] = None) -> StyleProfile:
        if len(self.styles) >= self.config.max_styles:
            raise HTTPException(status_code=400, detail="Maximum styles reached")
        style = StyleProfile(
            name=name,
            description=description,
            tone=tone,
            formality=formality or self.config.default_formality,
            complexity=complexity or self.config.default_complexity,
            creativity=creativity or self.config.default_creativity,
            constraints=constraints or []
        )
        for rule in self.rule_engine.rules:
            rule.execute(style)
        passed, score, details = self._three_layer_funnel(style)
        if not passed:
            raise HTTPException(status_code=400, detail=f"Style validation failed: {details}")
        self.styles[style.style_id] = style
        evaluation = StyleEvaluation(style_id=style.style_id, score=score, confidence=0.8, details=details)
        self.evaluations[evaluation.evaluation_id] = evaluation
        curve = self._generate_tension_curve(style)
        self._log_audit("create_style", {"style_id": style.style_id, "name": name, "score": score})
        return style
    def get_style(self, style_id: str) -> Optional[StyleProfile]:
        style = self.styles.get(style_id)
        if style:
            self._log_audit("get_style", {"style_id": style_id})
        return style
    def update_style(self, style_id: str, updates: Dict[str, Any]) -> Optional[StyleProfile]:
        style = self.styles.get(style_id)
        if not style:
            return None
        for key, value in updates.items():
            if hasattr(style, key):
                setattr(style, key, value)
        for rule in self.rule_engine.rules:
            rule.execute(style)
        passed, score, details = self._three_layer_funnel(style)
        if not passed:
            raise HTTPException(status_code=400, detail=f"Style update validation failed: {details}")
        evaluation = StyleEvaluation(style_id=style.style_id, score=score, confidence=0.8, details=details)
        self.evaluations[evaluation.evaluation_id] = evaluation
        curve = self._generate_tension_curve(style)
        self._log_audit("update_style", {"style_id": style_id, "updates": updates, "score": score})
        return style
    def delete_style(self, style_id: str) -> bool:
        if style_id in self.styles:
            del self.styles[style_id]
            self._log_audit("delete_style", {"style_id": style_id})
            return True
        return False
    def list_styles(self) -> List[StyleProfile]:
        self._log_audit("list_styles", {"count": len(self.styles)})
        return list(self.styles.values())
    def evaluate_style(self, style_id: str) -> Optional[StyleEvaluation]:
        style = self.styles.get(style_id)
        if not style:
            return None
        passed, score, details = self._three_layer_funnel(style)
        evaluation = StyleEvaluation(style_id=style.style_id, score=score, confidence=0.8, details=details)
        self.evaluations[evaluation.evaluation_id] = evaluation
        self._log_audit("evaluate_style", {"style_id": style_id, "score": score})
        return evaluation
    def get_tension_curve(self, style_id: str) -> Optional[TensionCurve]:
        for curve in self.tension_curves.values():
            if curve.metadata.get("style_id") == style_id:
                self._log_audit("get_tension_curve", {"style_id": style_id})
                return curve
        return None
    def handoff(self, target_agent_id: str, message: AgentMessage) -> Dict[str, Any]:
        self._log_audit("handoff", {"target_agent_id": target_agent_id, "message_type": message.message_type})
        return {
            "status": "handoff_initiated",
            "target_agent_id": target_agent_id,
            "message_id": message.message_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        self._log_audit("process_message", {"message_id": message.message_id, "message_type": message.message_type})
        if message.message_type == "create_style":
            return self.create_style(**message.payload).dict()
        elif message.message_type == "get_style":
            style = self.get_style(message.payload.get("style_id"))
            return style.dict() if style else {"error": "Style not found"}
        elif message.message_type == "list_styles":
            return {"styles": [s.dict() for s in self.list_styles()]}
        elif message.message_type == "evaluate_style":
            evaluation = self.evaluate_style(message.payload.get("style_id"))
            return evaluation.dict() if evaluation else {"error": "Style not found"}
        elif message.message_type == "get_tension_curve":
            curve = self.get_tension_curve(message.payload.get("style_id"))
            return curve.dict() if curve else {"error": "Curve not found"}
        else:
            return {"error": f"Unknown message type: {message.message_type}"}
    def get_audit_log(self, limit: int = 10) -> List[AuditLogEntry]:
        return self.audit_log[-limit:]
    def clear_audit_log(self):
        self.audit_log.clear()
        self._log_audit("clear_audit_log", {})
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_styles": len(self.styles),
            "total_evaluations": len(self.evaluations),
            "total_tension_curves": len(self.tension_curves),
            "total_audit_entries": len(self.audit_log),
            "average_formality": sum(s.formality for s in self.styles.values()) / max(len(self.styles), 1),
            "average_complexity": sum(s.complexity for s in self.styles.values()) / max(len(self.styles), 1),
            "average_creativity": sum(s.creativity for s in self.styles.values()) / max(len(self.styles), 1)
        }
    def export_styles(self, format: str = "json") -> str:
        data = {
            "styles": [s.dict() for s in self.styles.values()],
            "evaluations": [e.dict() for e in self.evaluations.values()],
            "tension_curves": [c.dict() for c in self.tension_curves.values()],
            "statistics": self.get_statistics()
        }
        if format == "json":
            return json.dumps(data, indent=2)
        else:
            return str(data)
    def import_styles(self, data: str, format: str = "json") -> int:
        if format == "json":
            parsed = json.loads(data)
        else:
            parsed = eval(data)
        count = 0
        for style_data in parsed.get("styles", []):
            style = StyleProfile(**style_data)
            if style.style_id not in self.styles:
                self.styles[style.style_id] = style
                count += 1
        self._log_audit("import_styles", {"imported_count": count})
        return count
    def run_computation_graph(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self._log_audit("run_computation_graph", {"input_keys": list(input_data.keys())})
        result = self.computation_graph.execute(input_data)
        return result
    def display_cli_output(self, data: Any, format_type: str = "table"):
        self.cli_output.display(data, format_type)
    def display_structured_output(self, data: Any, output_format: str = "json"):
        self.structured_output.display(data, output_format)
    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "agent_id": self.config.agent_id,
            "name": self.config.name,
            "version": self.config.version,
            "max_styles": self.config.max_styles,
            "current_styles": len(self.styles),
            "rules_count": len(self.rule_engine.rules),
            "graph_nodes": len(self.computation_graph.nodes),
            "graph_edges": len(self.computation_graph.edges)
        }
config = StyleManagerConfig()
style_manager = StyleManagerAgent(config)
