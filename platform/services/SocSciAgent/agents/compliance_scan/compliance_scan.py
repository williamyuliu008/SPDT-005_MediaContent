import json
import uuid
import datetime
from typing import List, Dict, Optional, Any, Tuple
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from module_lib.agent import BaseAgent, AgentConfig, AgentMessage
from module_lib.processing_computation_graph import ComputationGraph, ComputationNode, ComputationEdge
from module_lib.hmi import CLIOutput, StructuredOutput
from shared.tools.llm_clients import LLMClient, LLMResponse
class ComplianceRule(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    description: str
    category: str
    threshold: float
class ComplianceResult(BaseModel):
    result_id: str
    agent_id: str
    timestamp: str
    content_id: str
    overall_score: float
    rule_violations: List[Dict[str, Any]]
    tension_curve: List[float]
    audit_log: List[Dict[str, Any]]
class ComplianceScanAgent(BaseAgent):
    def __init__(self, agent_id: str, config: AgentConfig):
        super().__init__(agent_id, config)
        self.agent_id = agent_id
        self.audit_log = []
        self.rules: List[ComplianceRule] = []
        self.llm_client = LLMClient()
        self.computation_graph = ComputationGraph()
        self.cli_output = CLIOutput()
        self.structured_output = StructuredOutput()
        self._initialize_default_rules()
        self._build_computation_graph()
    def _initialize_default_rules(self):
        default_rules = [
            ComplianceRule(rule_id="R001", rule_name="ContentSafety", severity="high", description="Check for harmful content", category="safety", threshold=0.7),
            ComplianceRule(rule_id="R002", rule_name="DataPrivacy", severity="high", description="Check for PII leakage", category="privacy", threshold=0.8),
            ComplianceRule(rule_id="R003", rule_name="RegulatoryCompliance", severity="medium", description="Check regulatory adherence", category="regulatory", threshold=0.6),
            ComplianceRule(rule_id="R004", rule_name="EthicalGuidelines", severity="medium", description="Check ethical compliance", category="ethics", threshold=0.5),
            ComplianceRule(rule_id="R005", rule_name="QualityStandards", severity="low", description="Check content quality", category="quality", threshold=0.4)
        ]
        self.rules.extend(default_rules)
    def _build_computation_graph(self):
        node1 = ComputationNode(node_id="N001", node_type="input", description="Content Input")
        node2 = ComputationNode(node_id="N002", node_type="processing", description="Rule Engine")
        node3 = ComputationNode(node_id="N003", node_type="processing", description="Three Layer Funnel")
        node4 = ComputationNode(node_id="N004", node_type="processing", description="Tension Curve Generator")
        node5 = ComputationNode(node_id="N005", node_type="output", description="Compliance Result")
        edge1 = ComputationEdge(edge_id="E001", source_id="N001", target_id="N002")
        edge2 = ComputationEdge(edge_id="E002", source_id="N002", target_id="N003")
        edge3 = ComputationEdge(edge_id="E003", source_id="N003", target_id="N004")
        edge4 = ComputationEdge(edge_id="E004", source_id="N004", target_id="N005")
        self.computation_graph.add_node(node1)
        self.computation_graph.add_node(node2)
        self.computation_graph.add_node(node3)
        self.computation_graph.add_node(node4)
        self.computation_graph.add_node(node5)
        self.computation_graph.add_edge(edge1)
        self.computation_graph.add_edge(edge2)
        self.computation_graph.add_edge(edge3)
        self.computation_graph.add_edge(edge4)
    def _log_audit(self, action: str, details: Dict[str, Any]):
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "action": action,
            "details": details
        }
        self.audit_log.append(log_entry)
    def add_rule(self, rule: ComplianceRule):
        self.rules.append(rule)
        self._log_audit("add_rule", {"rule_id": rule.rule_id, "rule_name": rule.rule_name})
    def remove_rule(self, rule_id: str):
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        self._log_audit("remove_rule", {"rule_id": rule_id})
    def _rule_engine(self, content: str) -> List[Dict[str, Any]]:
        violations = []
        for rule in self.rules:
            prompt = f"Check if the following content violates rule '{rule.rule_name}': {rule.description}. Content: {content}"
            response = self.llm_client.generate(prompt)
            score = self._parse_compliance_score(response)
            if score > rule.threshold:
                violations.append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "severity": rule.severity,
                    "score": score,
                    "threshold": rule.threshold,
                    "violated": True
                })
        self._log_audit("rule_engine", {"content_length": len(content), "violations_found": len(violations)})
        return violations
    def _parse_compliance_score(self, response: LLMResponse) -> float:
        try:
            data = json.loads(response.text)
            return float(data.get("score", 0.0))
        except (json.JSONDecodeError, ValueError, TypeError):
            return 0.0
    def _three_layer_funnel(self, violations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
        layer1 = [v for v in violations if v["severity"] == "high"]
        layer2 = [v for v in violations if v["severity"] == "medium"]
        layer3 = [v for v in violations if v["severity"] == "low"]
        total_violations = len(layer1) + len(layer2) + len(layer3)
        weighted_score = (len(layer1) * 1.0 + len(layer2) * 0.6 + len(layer3) * 0.3) / max(total_violations, 1)
        funnel_result = {
            "layer1_high": len(layer1),
            "layer2_medium": len(layer2),
            "layer3_low": len(layer3),
            "total_violations": total_violations,
            "weighted_score": weighted_score
        }
        self._log_audit("three_layer_funnel", funnel_result)
        return violations, weighted_score
    def _generate_tension_curve(self, violations: List[Dict[str, Any]], base_score: float) -> List[float]:
        curve = []
        if not violations:
            curve = [0.0] * 10
        else:
            severity_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
            for i in range(10):
                tension = base_score
                for v in violations:
                    tension += severity_map.get(v["severity"], 0.0) * (0.1 * (i + 1))
                curve.append(min(tension, 1.0))
        self._log_audit("tension_curve", {"curve_length": len(curve), "curve_values": curve[:5]})
        return curve
    def handoff(self, target_agent_id: str, message: AgentMessage) -> AgentMessage:
        self._log_audit("handoff", {"target_agent_id": target_agent_id, "message_type": message.message_type})
        response_message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            receiver_id=target_agent_id,
            message_type="handoff_response",
            payload={"status": "handoff_completed", "original_message_id": message.message_id}
        )
        return response_message
    def process_content(self, content_id: str, content: str) -> ComplianceResult:
        self._log_audit("process_content_start", {"content_id": content_id, "content_length": len(content)})
        violations = self._rule_engine(content)
        filtered_violations, funnel_score = self._three_layer_funnel(violations)
        tension_curve = self._generate_tension_curve(filtered_violations, funnel_score)
        overall_score = 1.0 - funnel_score
        result = ComplianceResult(
            result_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            timestamp=datetime.datetime.utcnow().isoformat(),
            content_id=content_id,
            overall_score=overall_score,
            rule_violations=filtered_violations,
            tension_curve=tension_curve,
            audit_log=self.audit_log[-10:]
        )
        self._log_audit("process_content_end", {"result_id": result.result_id, "overall_score": overall_score})
        return result
    def get_audit_log(self) -> List[Dict[str, Any]]:
        return self.audit_log
    def clear_audit_log(self):
        self.audit_log = []
        self._log_audit("clear_audit_log", {})
    def to_cli_output(self, result: ComplianceResult) -> str:
        output_lines = []
        output_lines.append("=" * 60)
        output_lines.append(f"Compliance Scan Result - Agent: {self.agent_id}")
        output_lines.append("=" * 60)
        output_lines.append(f"Result ID: {result.result_id}")
        output_lines.append(f"Content ID: {result.content_id}")
        output_lines.append(f"Timestamp: {result.timestamp}")
        output_lines.append(f"Overall Score: {result.overall_score:.4f}")
        output_lines.append("-" * 40)
        output_lines.append("Rule Violations:")
        for v in result.rule_violations:
            output_lines.append(f"  - {v['rule_name']} (Severity: {v['severity']}, Score: {v['score']:.2f})")
        output_lines.append("-" * 40)
        output_lines.append("Tension Curve (first 5 points):")
        for i, val in enumerate(result.tension_curve[:5]):
            output_lines.append(f"  Point {i+1}: {val:.4f}")
        output_lines.append("-" * 40)
        output_lines.append("Recent Audit Log:")
        for entry in result.audit_log[-5:]:
            output_lines.append(f"  [{entry['timestamp']}] {entry['action']}")
        output_lines.append("=" * 60)
        return "\n".join(output_lines)
    def to_structured_output(self, result: ComplianceResult) -> Dict[str, Any]:
        return {
            "result_id": result.result_id,
            "agent_id": result.agent_id,
            "timestamp": result.timestamp,
            "content_id": result.content_id,
            "overall_score": result.overall_score,
            "rule_violations": result.rule_violations,
            "tension_curve": result.tension_curve,
            "audit_log": result.audit_log
        }
app = FastAPI()
agent_instance = ComplianceScanAgent(agent_id="compliance_scan_agent_001", config=AgentConfig(agent_id="compliance_scan_agent_001"))
@app.post("/scan")
async def scan_content(content_id: str, content: str):
    try:
        result = agent_instance.process_content(content_id, content)
        return agent_instance.to_structured_output(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/audit")
async def get_audit():
    return agent_instance.get_audit_log()
@app.post("/handoff")
async def handoff_agent(target_agent_id: str, message: AgentMessage):
    try:
        response = agent_instance.handoff(target_agent_id, message)
        return response.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/cli_output")
async def cli_output(content_id: str, content: str):
    try:
        result = agent_instance.process_content(content_id, content)
        return {"cli_output": agent_instance.to_cli_output(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
