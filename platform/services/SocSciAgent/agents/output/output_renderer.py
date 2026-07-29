import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from module_lib.agent import BaseAgent, AgentConfig, AgentMessage
from module_lib.processing_computation_graph import ComputationGraph, GraphNode, GraphEdge
from module_lib.hmi import CLIOutputFormatter, StructuredOutput
from shared.tools.llm_clients import LLMClient, LLMResponse
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class OutputRendererConfig(BaseModel):
    agent_id: str = "output_renderer_agent"
    version: str = "2.4.0"
    max_output_length: int = 10000
    supported_formats: List[str] = ["json", "text", "html", "markdown"]
    enable_audit: bool = True
    tension_curve_enabled: bool = True
    funnel_layers: int = 3
class AuditEntry(BaseModel):
    timestamp: str
    agent_id: str
    action: str
    input_summary: str
    output_summary: str
    status: str
    details: Optional[Dict[str, Any]] = None
class TensionCurvePoint(BaseModel):
    x: float
    y: float
    label: Optional[str] = None
    tension_value: float = 0.0
class FunnelResult(BaseModel):
    layer: int
    input_count: int
    output_count: int
    filter_ratio: float
    tension_score: float
    details: Optional[Dict[str, Any]] = None
class OutputRendererAgent(BaseAgent):
    def __init__(self, config: Optional[OutputRendererConfig] = None):
        _cfg = config or OutputRendererConfig()
        super().__init__(AgentConfig(agent_id=_cfg.agent_id, version=_cfg.version))
        self._output_cfg = _cfg  # Pydantic config (avoids conflict with BaseAgent.config)
        self.audit_log: List[AuditEntry] = []
        self.computation_graph = ComputationGraph()
        self.cli_formatter = CLIOutputFormatter()
        self.llm_client = LLMClient()
        self._initialize_computation_graph()
        logger.info(f"OutputRendererAgent initialized with id={self._output_cfg.agent_id}")
    def _initialize_computation_graph(self) -> None:
        node_input = GraphNode(
            node_id="input_parser",
            node_type="input",
            config={"format": "raw"}
        )
        node_funnel = GraphNode(
            node_id="funnel_processor",
            node_type="processing",
            config={"layers": self._output_cfg.funnel_layers}
        )
        node_tension = GraphNode(
            node_id="tension_curve_generator",
            node_type="analysis",
            config={"enabled": self._output_cfg.tension_curve_enabled}
        )
        node_render = GraphNode(
            node_id="output_renderer",
            node_type="output",
            config={"formats": self._output_cfg.supported_formats}
        )
        node_audit = GraphNode(
            node_id="audit_logger",
            node_type="audit",
            config={"enabled": self._output_cfg.enable_audit}
        )
        self.computation_graph.add_node(node_input)
        self.computation_graph.add_node(node_funnel)
        self.computation_graph.add_node(node_tension)
        self.computation_graph.add_node(node_render)
        self.computation_graph.add_node(node_audit)
        self.computation_graph.add_edge(GraphEdge(source="input_parser", target="funnel_processor"))
        self.computation_graph.add_edge(GraphEdge(source="funnel_processor", target="tension_curve_generator"))
        self.computation_graph.add_edge(GraphEdge(source="tension_curve_generator", target="output_renderer"))
        self.computation_graph.add_edge(GraphEdge(source="output_renderer", target="audit_logger"))
    def handoff(self, target_agent_id: str, message: AgentMessage) -> AgentMessage:
        logger.info(f"Handoff from {self._output_cfg.agent_id} to {target_agent_id}")
        handoff_message = AgentMessage(
            sender=self._output_cfg.agent_id,
            recipient=target_agent_id,
            payload={
                "handoff_timestamp": datetime.now(timezone.utc).isoformat(),
                "original_message": message.payload
            },
            msg_type="handoff_response"
        )
        self._log_audit("handoff", str(message.payload)[:100], "success")
        return handoff_message
    def _log_audit(self, action: str, input_summary: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        if not self._output_cfg.enable_audit:
            return
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=self._output_cfg.agent_id,
            action=action,
            input_summary=input_summary[:200] if input_summary else "",
            output_summary="",
            status=status,
            details=details
        )
        self.audit_log.append(entry)
        logger.debug(f"Audit: {action} | {status}")
    def get_audit_log(self, limit: int = 100) -> List[AuditEntry]:
        return self.audit_log[-limit:]

    def execute(self, input_data: Any) -> Dict[str, Any]:
        """Pipeline-compatible execute interface."""
        try:
            return self.process_input(input_data)
        except Exception as e:
            return {"error": str(e), "agent_id": self._output_cfg.agent_id}

    def process_input(self, raw_input: Any) -> Dict[str, Any]:
        self._log_audit("process_input", str(raw_input)[:100], "started")
        try:
            parsed = self._parse_input(raw_input)
            funnel_result = self._apply_funnel(parsed)
            tension_curve = self._generate_tension_curve(funnel_result)
            rendered_output = self._render_output(tension_curve)
            self._log_audit("process_input", str(raw_input)[:100], "success")
            return rendered_output
        except Exception as e:
            self._log_audit("process_input", str(raw_input)[:100], "failed", {"error": str(e)})
            raise
    def _parse_input(self, raw_input: Any) -> Dict[str, Any]:
        if isinstance(raw_input, str):
            try:
                return json.loads(raw_input)
            except json.JSONDecodeError:
                return {"text": raw_input, "type": "plain_text"}
        elif isinstance(raw_input, dict):
            return raw_input
        else:
            return {"data": raw_input, "type": type(raw_input).__name__}
    def _apply_funnel(self, data: Dict[str, Any]) -> FunnelResult:
        items = data.get("items", data.get("data", []))
        if not isinstance(items, list):
            items = [items]
        current_items = items
        for layer in range(1, self._output_cfg.funnel_layers + 1):
            filtered = self._funnel_layer_filter(current_items, layer)
            ratio = len(filtered) / max(len(current_items), 1)
            tension = self._calculate_layer_tension(current_items, filtered, layer)
            logger.info(f"Funnel layer {layer}: {len(current_items)} -> {len(filtered)} (ratio={ratio:.2f}, tension={tension:.2f})")
            current_items = filtered
        result = FunnelResult(
            layer=self._output_cfg.funnel_layers,
            input_count=len(items),
            output_count=len(current_items),
            filter_ratio=len(current_items) / max(len(items), 1),
            tension_score=self._calculate_total_tension(items, current_items),
            details={"layers_applied": self._output_cfg.funnel_layers}
        )
        return result
    def _funnel_layer_filter(self, items: List[Any], layer: int) -> List[Any]:
        if not items:
            return []
        threshold = 1.0 - (layer * 0.25)
        filtered = []
        for item in items:
            score = self._score_item(item, layer)
            if score >= threshold:
                filtered.append(item)
        return filtered if filtered else items[:max(1, len(items)//2)]
    def _score_item(self, item: Any, layer: int) -> float:
        if isinstance(item, dict):
            relevance = item.get("relevance", item.get("score", 0.5))
            if isinstance(relevance, (int, float)):
                return min(1.0, max(0.0, relevance))
        return 0.5
    def _calculate_layer_tension(self, before: List[Any], after: List[Any], layer: int) -> float:
        if not before:
            return 0.0
        reduction = 1.0 - (len(after) / len(before))
        layer_factor = 1.0 + (layer * 0.1)
        return reduction * layer_factor
    def _calculate_total_tension(self, original: List[Any], final: List[Any]) -> float:
        if not original:
            return 0.0
        return 1.0 - (len(final) / len(original))
    def _generate_tension_curve(self, funnel_result: FunnelResult) -> List[TensionCurvePoint]:
        if not self._output_cfg.tension_curve_enabled:
            return []
        points = []
        for i in range(10):
            x = i / 10.0
            base_tension = funnel_result.tension_score
            variation = 0.1 * (1 - abs(x - 0.5) * 2)
            tension_value = min(1.0, max(0.0, base_tension + variation))
            point = TensionCurvePoint(
                x=x,
                y=tension_value,
                label=f"Point_{i}",
                tension_value=tension_value
            )
            points.append(point)
        logger.info(f"Generated tension curve with {len(points)} points")
        return points
    def _render_output(self, tension_curve: List[TensionCurvePoint]) -> Dict[str, Any]:
        output = {
            "agent_id": self._output_cfg.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tension_curve": [p.dict() for p in tension_curve],
            "summary": {
                "total_points": len(tension_curve),
                "max_tension": max((p.tension_value for p in tension_curve), default=0.0),
                "min_tension": min((p.tension_value for p in tension_curve), default=0.0),
                "avg_tension": sum(p.tension_value for p in tension_curve) / max(len(tension_curve), 1)
            },
            "format": "json"
        }
        structured = StructuredOutput()
        structured.add("output", output)
        self.cli_formatter.render(structured.output())
        return output
    def process_with_llm(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        self._log_audit("llm_process", prompt[:100], "started")
        try:
            response = self.llm_client.chat(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            self._log_audit("llm_process", prompt[:100], content[:100], "success")
            return content
        except Exception as e:
            self._log_audit("llm_process", prompt[:100], str(e)[:100], "failed")
            return f"Error: {str(e)}"
    def run_pipeline(self, input_data: Any) -> Dict[str, Any]:
        self._log_audit("pipeline_start", str(input_data)[:100], "", "started")
        try:
            result = self.process_input(input_data)
            self._log_audit("pipeline_end", str(input_data)[:100], str(result)[:100], "success")
            return result
        except Exception as e:
            self._log_audit("pipeline_end", str(input_data)[:100], str(e)[:100], "failed")
            return {"error": str(e), "status": "failed"}
app = FastAPI(title="OutputRenderer Agent API", version="2.4.0")
agent_instance = None  # removed: was instantiated at module load, causing init errors
# agent_instance = OutputRendererAgent()  # disabled: instantiate via PipelineRunner
@app.post("/process")
async def process_endpoint(data: Dict[str, Any]):
    try:
        result = agent_instance.run_pipeline(data)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/audit")
async def get_audit(limit: int = 100):
    return {"audit_log": [entry.dict() for entry in agent_instance.get_audit_log(limit)]}
@app.post("/handoff")
async def handoff_endpoint(target: str, message: Dict[str, Any]):
    msg = AgentMessage(
        sender=agent_instance.config.agent_id,
        receiver=target,
        content=message,
        metadata={"timestamp": datetime.now(timezone.utc).isoformat()}
    )
    response = agent_instance.handoff(target, msg)
    return {"handoff_response": response.dict()}
@app.get("/health")
async def health_check():
    return {
        "agent_id": agent_instance.config.agent_id,
        "status": "healthy",
        "audit_count": len(agent_instance.audit_log),
        "version": agent_instance.config.version
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8047)
