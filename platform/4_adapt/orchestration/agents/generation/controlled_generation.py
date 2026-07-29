import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from module_lib.agent import BaseAgent, AgentConfig, AgentContext
from module_lib.processing_computation_graph import ComputationGraph, Node, Edge
from module_lib.hmi import CLIStructuredOutput
from shared.tools.llm_clients import LLMClient, LLMConfig, LLMResponse
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ControlledGenerationAgent")
class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=4096)
class GenerationResponse(BaseModel):
    agent_id: str
    request_id: str
    generated_text: str
    audit_log: List[Dict[str, Any]]
    tension_curve: List[float]
    funnel_results: Dict[str, Any]
class RuleEngine:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = rules
        self.audit_entries: List[Dict[str, Any]] = []
    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        passed = True
        details = {}
        for rule in self.rules:
            rule_name = rule.get("name", "unknown")
            rule_type = rule.get("type", "regex")
            pattern = rule.get("pattern", "")
            if rule_type == "regex":
                import re
                if re.search(pattern, context.get("text", "")):
                    passed = False
                    details[rule_name] = {"violated": True, "pattern": pattern}
                else:
                    details[rule_name] = {"violated": False}
            elif rule_type == "length":
                max_len = rule.get("max_length", 1000)
                if len(context.get("text", "")) > max_len:
                    passed = False
                    details[rule_name] = {"violated": True, "max_length": max_len}
                else:
                    details[rule_name] = {"violated": False}
            elif rule_type == "keyword":
                keywords = rule.get("keywords", [])
                text_lower = context.get("text", "").lower()
                found = [kw for kw in keywords if kw.lower() in text_lower]
                if found:
                    passed = False
                    details[rule_name] = {"violated": True, "found_keywords": found}
                else:
                    details[rule_name] = {"violated": False}
            self.audit_entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rule": rule_name,
                "passed": not details.get(rule_name, {}).get("violated", False),
                "details": details.get(rule_name, {})
            })
        return passed, details
class ThreeLayerFunnel:
    def __init__(self):
        self.audit_entries: List[Dict[str, Any]] = []
    def apply(self, text: str, constraints: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        layer1_result = self._layer1_safety(text, constraints)
        self.audit_entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": 1,
            "input_length": len(text),
            "output_length": len(layer1_result),
            "action": "filtered" if layer1_result != text else "passed"
        })
        layer2_result = self._layer2_relevance(layer1_result, constraints)
        self.audit_entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": 2,
            "input_length": len(layer1_result),
            "output_length": len(layer2_result),
            "action": "trimmed" if layer2_result != layer1_result else "passed"
        })
        layer3_result = self._layer3_style(layer2_result, constraints)
        self.audit_entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": 3,
            "input_length": len(layer2_result),
            "output_length": len(layer3_result),
            "action": "styled" if layer3_result != layer2_result else "passed"
        })
        return layer3_result, {
            "layer1": {"input": text[:50], "output": layer1_result[:50]},
            "layer2": {"input": layer1_result[:50], "output": layer2_result[:50]},
            "layer3": {"input": layer2_result[:50], "output": layer3_result[:50]}
        }
    def _layer1_safety(self, text: str, constraints: Dict[str, Any]) -> str:
        forbidden = constraints.get("forbidden_words", [])
        if not forbidden:
            return text
        words = text.split()
        filtered = [w for w in words if w.lower() not in [f.lower() for f in forbidden]]
        return " ".join(filtered)
    def _layer2_relevance(self, text: str, constraints: Dict[str, Any]) -> str:
        max_len = constraints.get("max_length", 2000)
        if len(text) <= max_len:
            return text
        return text[:max_len]
    def _layer3_style(self, text: str, constraints: Dict[str, Any]) -> str:
        style = constraints.get("style", "neutral")
        if style == "formal":
            text = text.replace("gonna", "going to").replace("wanna", "want to")
        elif style == "concise":
            sentences = text.split(".")
            text = ". ".join(sentences[:3])
        return text
class TensionCurve:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.audit_entries: List[Dict[str, Any]] = []
    def compute(self, text: str) -> List[float]:
        words = text.split()
        if len(words) < self.window_size:
            return [0.0] * len(words)
        curve = []
        for i in range(len(words) - self.window_size + 1):
            window = words[i:i + self.window_size]
            tension = self._window_tension(window)
            curve.append(tension)
        self.audit_entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "window_size": self.window_size,
            "curve_length": len(curve),
            "max_tension": max(curve) if curve else 0.0,
            "min_tension": min(curve) if curve else 0.0
        })
        return curve
    def _window_tension(self, window: List[str]) -> float:
        tension_keywords = {"conflict", "danger", "urgent", "crisis", "threat", "risk", "war", "attack", "violence", "emergency"}
        count = sum(1 for w in window if w.lower() in tension_keywords)
        return count / len(window)
class ControlledGenerationAgent(BaseAgent):
    def __init__(self, agent_id: str = "controlled_gen_001", config: AgentConfig = None):
        cfg = config or AgentConfig(agent_id=agent_id)
        super().__init__(agent_id=agent_id, config=cfg)
        self.agent_id = agent_id
        self.config = cfg
        self.llm_client = LLMClient(LLMConfig(
            model=cfg.get("llm_model", "deepseek-chat"),
            base_url=cfg.get("llm_endpoint", ""),
            temperature=cfg.get("temperature", 0.7),
            max_tokens=cfg.get("max_tokens", 2048)
        ))
        self.rule_engine = RuleEngine(cfg.get("rules", []))
        self.funnel = ThreeLayerFunnel()
        self.tension_curve = TensionCurve(window_size=cfg.get("tension_window", 5))
        self.computation_graph = ComputationGraph()
        self._build_graph()
        self.audit_log: List[Dict[str, Any]] = []
        self.cli_output = CLIStructuredOutput()
    def _build_graph(self):
        node_generate = Node(id="generate", type="llm_call", config={"model": "gpt-4"})
        node_rule = Node(id="rule_check", type="rule_engine", config={})
        node_funnel = Node(id="funnel", type="three_layer_funnel", config={})
        node_tension = Node(id="tension", type="tension_curve", config={})
        node_output = Node(id="output", type="format", config={})
        self.computation_graph.add_node(node_generate)
        self.computation_graph.add_node(node_rule)
        self.computation_graph.add_node(node_funnel)
        self.computation_graph.add_node(node_tension)
        self.computation_graph.add_node(node_output)
        self.computation_graph.add_edge(Edge(source="generate", target="rule_check"))
        self.computation_graph.add_edge(Edge(source="rule_check", target="funnel"))
        self.computation_graph.add_edge(Edge(source="funnel", target="tension"))
        self.computation_graph.add_edge(Edge(source="tension", target="output"))
    def execute(self, input_data: Any) -> Dict[str, Any]:
        """Pipeline-compatible execute interface. Adapts dict/COG input to GenerationRequest."""
        if isinstance(input_data, GenerationRequest):
            return self.process(input_data).model_dump()

        # Adapt pipeline dict → GenerationRequest
        prompt = ""
        if isinstance(input_data, dict):
            # COG script / orchestration output
            if "cog_script" in input_data:
                prompt = json.dumps(input_data["cog_script"], ensure_ascii=False)
            elif "result" in input_data:
                prompt = json.dumps(input_data["result"], ensure_ascii=False)
            elif "text" in input_data:
                prompt = input_data["text"]
            else:
                prompt = json.dumps(input_data, ensure_ascii=False)

        constraints = {}
        if isinstance(input_data, dict):
            constraints = input_data.get("constraints", {})

        req = GenerationRequest(
            prompt=prompt or "Generate content per pipeline config",
            constraints=constraints,
            temperature=input_data.get("temperature", 0.7) if isinstance(input_data, dict) else 0.7,
            max_tokens=input_data.get("max_tokens", 2048) if isinstance(input_data, dict) else 2048,
        )
        try:
            return self.process(req).model_dump()
        except Exception as e:
            logger.error(f"ControlledGeneration execute failed: {e}")
            return {"error": str(e), "agent_id": self.agent_id}

    def handoff(self, target_agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        handoff_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_agent": self.agent_id,
            "to_agent": target_agent_id,
            "payload_summary": str(payload)[:100]
        }
        self.audit_log.append(handoff_record)
        logger.info(f"Handoff from {self.agent_id} to {target_agent_id}")
        return {"status": "handoff_initiated", "target": target_agent_id, "payload": payload}
    def process(self, request: GenerationRequest) -> GenerationResponse:
        request_id = str(uuid.uuid4())
        context = AgentContext(request_id=request_id, metadata={"request_data": request.dict()})
        self._log_audit("request_received", {"request_id": request_id, "prompt_length": len(request.prompt)})
        generated = self._generate_text(request)
        self._log_audit("generation_complete", {"text_length": len(generated)})
        rule_passed, rule_details = self.rule_engine.evaluate({"text": generated})
        self._log_audit("rule_evaluation", {"passed": rule_passed, "details": rule_details})
        if not rule_passed:
            generated = self._apply_corrections(generated, rule_details)
        funnel_text, funnel_details = self.funnel.apply(generated, request.constraints)
        self._log_audit("funnel_applied", {"details": funnel_details})
        tension_values = self.tension_curve.compute(funnel_text)
        self._log_audit("tension_computed", {"curve_length": len(tension_values)})
        response = GenerationResponse(
            agent_id=self.agent_id,
            request_id=request_id,
            generated_text=funnel_text,
            audit_log=self.audit_log.copy(),
            tension_curve=tension_values,
            funnel_results=funnel_details
        )
        self._log_audit("response_prepared", {"response_length": len(funnel_text)})
        self.cli_output.add("response", response.model_dump())
        logger.info(f"Audit: response_prepared - {response}")
        return response
    def _generate_text(self, request: GenerationRequest) -> str:
        # Use .chat() interface (LLMClient stub method)
        try:
            llm_response = self.llm_client.chat(
                prompt=request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            return llm_response.content
        except Exception as e:
            logger.warning(f"LLM generate failed: {e}, using stub")
            # Fallback: return a stub response
            return f"[Stub Generated] {request.prompt[:200]}"
    def _apply_corrections(self, text: str, rule_details: Dict[str, Any]) -> str:
        for rule_name, detail in rule_details.items():
            if detail.get("violated"):
                if "found_keywords" in detail:
                    for kw in detail["found_keywords"]:
                        text = text.replace(kw, "[REDACTED]")
                if "pattern" in detail:
                    import re
                    text = re.sub(detail["pattern"], "[FILTERED]", text)
        return text
    def _log_audit(self, event: str, details: Dict[str, Any]):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": self.agent_id,
            "event": event,
            "details": details
        }
        self.audit_log.append(entry)
        logger.info(f"Audit: {event} - {details}")
app = FastAPI(title="ControlledGenerationAgent")
agent_instance: Optional[ControlledGenerationAgent] = None
@app.on_event("startup")
def startup():
    global agent_instance
    config = AgentConfig(
        agent_id="controlled_gen_001",
        llm_endpoint="http://localhost:8000/v1",
        rules=[
            {"name": "no_violence", "type": "keyword", "keywords": ["kill", "murder", "attack"]},
            {"name": "max_length_2000", "type": "length", "max_length": 2000}
        ],
        tension_window=5
    )
    agent_instance = ControlledGenerationAgent(agent_id="controlled_gen_001", config=config)
    logger.info("ControlledGenerationAgent started")
@app.post("/generate", response_model=GenerationResponse)
def generate(request: GenerationRequest):
    if agent_instance is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return agent_instance.process(request)
@app.post("/handoff")
def handoff(target_agent_id: str, payload: Dict[str, Any]):
    if agent_instance is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return agent_instance.handoff(target_agent_id, payload)
@app.get("/audit")
def get_audit():
    if agent_instance is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {"audit_log": agent_instance.audit_log}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
