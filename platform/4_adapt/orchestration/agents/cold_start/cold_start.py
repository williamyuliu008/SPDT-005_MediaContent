import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from module_lib.agent import BaseAgent, AgentConfig, AgentMessage, AgentState
from module_lib.processing_computation_graph import ComputationGraph, GraphNode, GraphEdge
from module_lib.hmi import CLIInterface, StructuredOutput
from shared.tools.llm_clients import LLMClient, LLMResponse
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ColdStartAgent")
app = FastAPI(title="ColdStart Agent", version="1.0.0")
class ColdStartConfig(BaseModel):
    agent_id: str = "cold_start_agent_v1"
    max_iterations: int = 10
    convergence_threshold: float = 0.85
    funnel_stages: List[str] = ["broad_filter", "mid_filter", "narrow_filter"]
    tension_curve_params: Dict[str, float] = Field(default_factory=lambda: {"alpha": 0.3, "beta": 0.7})
class AuditLogEntry(BaseModel):
    timestamp: str
    agent_id: str
    action: str
    details: Dict[str, Any]
    result: Optional[str] = None
class ColdStartAgent(BaseAgent):
    def __init__(self, config: ColdStartConfig):
        super().__init__(AgentConfig(agent_id=config.agent_id))
        self.config = config
        self.audit_log: List[AuditLogEntry] = []
        self.computation_graph = ComputationGraph()
        self.llm_client = LLMClient()
        self.cli = CLIInterface()
        self.state = AgentState.IDLE
        self._init_computation_graph()
    def _init_computation_graph(self):
        nodes = [
            GraphNode(node_id="input", node_type="source", config={}),
            GraphNode(node_id="broad_filter", node_type="processor", config={"stage": "broad"}),
            GraphNode(node_id="mid_filter", node_type="processor", config={"stage": "mid"}),
            GraphNode(node_id="narrow_filter", node_type="processor", config={"stage": "narrow"}),
            GraphNode(node_id="tension_curve", node_type="analyzer", config={"params": self.config.tension_curve_params}),
            GraphNode(node_id="output", node_type="sink", config={}),
        ]
        edges = [
            GraphEdge(source_id="input", target_id="broad_filter", weight=1.0),
            GraphEdge(source_id="broad_filter", target_id="mid_filter", weight=0.8),
            GraphEdge(source_id="mid_filter", target_id="narrow_filter", weight=0.6),
            GraphEdge(source_id="narrow_filter", target_id="tension_curve", weight=0.5),
            GraphEdge(source_id="tension_curve", target_id="output", weight=1.0),
        ]
        for node in nodes:
            self.computation_graph.add_node(node)
        for edge in edges:
            self.computation_graph.add_edge(edge)
    def _log_audit(self, action: str, details: Dict[str, Any], result: Optional[str] = None):
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=self.config.agent_id,
            action=action,
            details=details,
            result=result,
        )
        self.audit_log.append(entry)
        logger.info(f"Audit: {action} - {json.dumps(details)}")
    def handoff(self, target_agent_id: str, message: AgentMessage) -> AgentMessage:
        self._log_audit("handoff", {"from": self.config.agent_id, "to": target_agent_id, "message_id": message.message_id})
        response = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.config.agent_id,
            receiver_id=target_agent_id,
            content={"status": "handoff_complete", "original_message": message.content},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return response
    def process_message(self, message: AgentMessage) -> AgentMessage:
        self._log_audit("process_message", {"message_id": message.message_id, "content_preview": str(message.content)[:100]})
        self.state = AgentState.BUSY
        try:
            result = self._run_cold_start_pipeline(message.content)
            response = AgentMessage(
                message_id=str(uuid.uuid4()),
                sender_id=self.config.agent_id,
                receiver_id=message.sender_id,
                content=result,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self.state = AgentState.IDLE
            self._log_audit("pipeline_complete", {"input": str(message.content)[:100], "output": str(result)[:100]}, "success")
            return response
        except Exception as e:
            self.state = AgentState.ERROR
            self._log_audit("pipeline_error", {"error": str(e)}, "failure")
            raise
    def _run_cold_start_pipeline(self, input_data: Any) -> Dict[str, Any]:
        self._log_audit("pipeline_start", {"input_type": type(input_data).__name__})
        broad_result = self._broad_filter(input_data)
        mid_result = self._mid_filter(broad_result)
        narrow_result = self._narrow_filter(mid_result)
        tension_result = self._compute_tension_curve(narrow_result)
        final_output = self._generate_output(tension_result)
        self._log_audit("pipeline_end", {"output_summary": str(final_output)[:100]})
        return final_output
    def _broad_filter(self, data: Any) -> List[Dict[str, Any]]:
        self._log_audit("broad_filter_start", {"data_size": len(str(data))})
        if isinstance(data, str):
            items = [{"text": data, "score": 1.0}]
        elif isinstance(data, list):
            items = [{"text": str(item), "score": 1.0} for item in data]
        elif isinstance(data, dict):
            items = [{"text": str(v), "score": 1.0} for v in data.values()]
        else:
            items = [{"text": str(data), "score": 1.0}]
        filtered = [item for item in items if len(item["text"]) > 10]
        self._log_audit("broad_filter_end", {"input_count": len(items), "output_count": len(filtered)})
        return filtered
    def _mid_filter(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self._log_audit("mid_filter_start", {"input_count": len(data)})
        filtered = []
        for item in data:
            llm_response = self.llm_client.analyze(item["text"])
            relevance_score = self._calculate_relevance(llm_response)
            if relevance_score > 0.5:
                item["relevance"] = relevance_score
                filtered.append(item)
        self._log_audit("mid_filter_end", {"input_count": len(data), "output_count": len(filtered)})
        return filtered
    def _narrow_filter(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self._log_audit("narrow_filter_start", {"input_count": len(data)})
        sorted_data = sorted(data, key=lambda x: x.get("relevance", 0), reverse=True)
        top_k = max(1, len(sorted_data) // 2)
        filtered = sorted_data[:top_k]
        self._log_audit("narrow_filter_end", {"input_count": len(data), "output_count": len(filtered)})
        return filtered
    def _compute_tension_curve(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._log_audit("tension_curve_start", {"input_count": len(data)})
        if not data:
            return {"tension_points": [], "curve_type": "flat", "summary": "No data"}
        alpha = self.config.tension_curve_params.get("alpha", 0.3)
        beta = self.config.tension_curve_params.get("beta", 0.7)
        tension_points = []
        for i, item in enumerate(data):
            position = i / max(1, len(data) - 1)
            tension = alpha * (1 - position) + beta * item.get("relevance", 0.5)
            tension_points.append({"position": position, "tension": tension, "text_preview": item["text"][:50]})
        curve_type = "increasing" if tension_points[-1]["tension"] > tension_points[0]["tension"] else "decreasing"
        summary = f"Tension curve with {len(tension_points)} points, type: {curve_type}"
        result = {"tension_points": tension_points, "curve_type": curve_type, "summary": summary}
        self._log_audit("tension_curve_end", {"curve_type": curve_type, "point_count": len(tension_points)})
        return result
    def _generate_output(self, tension_result: Dict[str, Any]) -> Dict[str, Any]:
        output = {
            "agent_id": self.config.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tension_analysis": tension_result,
            "audit_log_count": len(self.audit_log),
            "status": "completed",
        }
        return output
    def _calculate_relevance(self, llm_response: LLMResponse) -> float:
        if llm_response and llm_response.confidence:
            return min(1.0, max(0.0, llm_response.confidence))
        return 0.5
    def get_audit_log(self) -> List[AuditLogEntry]:
        return self.audit_log
    def reset(self):
        self.audit_log.clear()
        self.state = AgentState.IDLE
        self._log_audit("agent_reset", {"reason": "manual_reset"})
class RuleEngine:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = rules
        self.evaluation_count = 0
    def evaluate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.evaluation_count += 1
        triggered = []
        for rule in self.rules:
            if self._match_rule(rule, context):
                triggered.append(rule)
        return triggered
    def _match_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        conditions = rule.get("conditions", [])
        for cond in conditions:
            field = cond.get("field")
            operator = cond.get("operator", "eq")
            value = cond.get("value")
            actual = context.get(field)
            if operator == "eq" and actual != value:
                return False
            elif operator == "gt" and not (actual > value):
                return False
            elif operator == "lt" and not (actual < value):
                return False
            elif operator == "contains" and value not in str(actual):
                return False
        return True
class ThreeLayerFunnel:
    def __init__(self, config: ColdStartConfig):
        self.config = config
        self.stages = config.funnel_stages
        self.stage_stats = {stage: {"input": 0, "output": 0} for stage in self.stages}
    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        current_data = data
        for stage in self.stages:
            self.stage_stats[stage]["input"] = len(current_data)
            if stage == "broad_filter":
                current_data = self._broad_filter_stage(current_data)
            elif stage == "mid_filter":
                current_data = self._mid_filter_stage(current_data)
            elif stage == "narrow_filter":
                current_data = self._narrow_filter_stage(current_data)
            self.stage_stats[stage]["output"] = len(current_data)
        return current_data
    def _broad_filter_stage(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [item for item in data if item.get("score", 0) > 0.3]
    def _mid_filter_stage(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [item for item in data if item.get("relevance", 0) > 0.5]
    def _narrow_filter_stage(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sorted_data = sorted(data, key=lambda x: x.get("priority", 0), reverse=True)
        return sorted_data[:max(1, len(sorted_data) // 2)]
    def get_stats(self) -> Dict[str, Dict[str, int]]:
        return self.stage_stats
class TensionCurveAnalyzer:
    def __init__(self, alpha: float = 0.3, beta: float = 0.7):
        self.alpha = alpha
        self.beta = beta
    def compute(self, data_points: List[float]) -> List[float]:
        if not data_points:
            return []
        n = len(data_points)
        tensions = []
        for i, value in enumerate(data_points):
            position = i / max(1, n - 1)
            tension = self.alpha * (1 - position) + self.beta * value
            tensions.append(tension)
        return tensions
    def classify_curve(self, tensions: List[float]) -> str:
        if len(tensions) < 2:
            return "flat"
        if tensions[-1] > tensions[0]:
            return "increasing"
        elif tensions[-1] < tensions[0]:
            return "decreasing"
        else:
            return "stable"
agent_instance = ColdStartAgent(ColdStartConfig())
@app.post("/process")
async def process_request(payload: Dict[str, Any]):
    try:
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id="api",
            receiver_id=agent_instance.config.agent_id,
            content=payload.get("data", {}),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        response = agent_instance.process_message(message)
        return {"status": "success", "data": response.content, "audit_count": len(agent_instance.audit_log)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/audit")
async def get_audit_log():
    return {"audit_log": [entry.dict() for entry in agent_instance.audit_log]}
@app.post("/reset")
async def reset_agent():
    agent_instance.reset()
    return {"status": "reset_complete"}
@app.get("/health")
async def health_check():
    return {"agent_id": agent_instance.config.agent_id, "state": agent_instance.state.value}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
