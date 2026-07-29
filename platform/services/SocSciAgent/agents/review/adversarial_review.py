import json
import uuid
import datetime
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from module_lib.agent import BaseAgent, AgentConfig, AgentMessage
from module_lib.processing_computation_graph import ComputationGraph, ComputationNode, ComputationEdge
from module_lib.hmi import CLIOutput, CLIMenu, CLIInput
from shared.tools.llm_clients import LLMClient, LLMConfig, LLMResponse
class AdversarialReviewConfig(BaseModel):
    agent_id: str = "adversarial_review_agent_v1"
    max_review_depth: int = 3
    tension_threshold: float = 0.7
    funnel_stages: List[str] = ["surface", "structural", "deep"]
    llm_model: str = "gpt-4"
    temperature: float = 0.3
class ReviewInput(BaseModel):
    content_id: str
    content_text: str
    content_type: str = "text"
    metadata: Dict[str, Any] = Field(default_factory=dict)
class ReviewOutput(BaseModel):
    review_id: str
    content_id: str
    overall_score: float
    tension_score: float
    funnel_results: Dict[str, Any]
    adversarial_findings: List[Dict[str, Any]]
    recommendation: str
    audit_trail: List[Dict[str, Any]]
class FunnelResult(BaseModel):
    stage: str
    score: float
    findings: List[str]
    passed: bool
class TensionCurvePoint(BaseModel):
    position: float
    tension_value: float
    gradient: float
class AdversarialReviewAgent(BaseAgent):
    def __init__(self, config: Optional[AdversarialReviewConfig] = None):
        # Store Pydantic review config separately to avoid conflict with BaseAgent.config
        _review_cfg = config or AdversarialReviewConfig()
        super().__init__(AgentConfig(
            agent_id=_review_cfg.agent_id,
            agent_type="adversarial_review",
            capabilities=["adversarial_analysis", "tension_measurement", "funnel_filtering"]
        ))
        self._review_config = _review_cfg  # Pydantic config (avoids naming conflict)
        self.llm_client = LLMClient(LLMConfig(
            model=_review_cfg.llm_model,
            temperature=_review_cfg.temperature
        ))
        self.computation_graph = ComputationGraph()
        self._initialize_computation_graph()
        self.audit_log: List[Dict[str, Any]] = []
        self.cli_output = CLIOutput()
        self.cli_menu = CLIMenu(title="Adversarial Review Agent Control")
        self._setup_cli()

    def execute(self, input_data: Any) -> Dict[str, Any]:
        """Pipeline-compatible execute interface."""
        try:
            ri = ReviewInput(**input_data) if isinstance(input_data, dict) else input_data
        except Exception:
            # fallback: wrap whatever we got
            ri = ReviewInput(
                content_id=str(hash(str(input_data)))[:12],
                content_text=str(input_data)
            )
        try:
            result = self.process_review(ri)
            return result.model_dump()
        except Exception as e:
            return {"error": str(e), "agent_id": self._review_config.agent_id}
    def _initialize_computation_graph(self):
        node_surface = ComputationNode(
            node_id="surface_funnel",
            node_type="filter",
            config={"stage": "surface", "threshold": 0.3}
        )
        node_structural = ComputationNode(
            node_id="structural_funnel",
            node_type="filter",
            config={"stage": "structural", "threshold": 0.5}
        )
        node_deep = ComputationNode(
            node_id="deep_funnel",
            node_type="filter",
            config={"stage": "deep", "threshold": 0.7}
        )
        node_tension = ComputationNode(
            node_id="tension_analyzer",
            node_type="analyzer",
            config={"method": "gradient_descent"}
        )
        node_aggregator = ComputationNode(
            node_id="result_aggregator",
            node_type="aggregator",
            config={"aggregation_method": "weighted_average"}
        )
        self.computation_graph.add_node(node_surface)
        self.computation_graph.add_node(node_structural)
        self.computation_graph.add_node(node_deep)
        self.computation_graph.add_node(node_tension)
        self.computation_graph.add_node(node_aggregator)
        edge1 = ComputationEdge(source_id="surface_funnel", target_id="structural_funnel", weight=0.3)
        edge2 = ComputationEdge(source_id="structural_funnel", target_id="deep_funnel", weight=0.5)
        edge3 = ComputationEdge(source_id="deep_funnel", target_id="tension_analyzer", weight=0.7)
        edge4 = ComputationEdge(source_id="tension_analyzer", target_id="result_aggregator", weight=1.0)
        self.computation_graph.add_edge(edge1)
        self.computation_graph.add_edge(edge2)
        self.computation_graph.add_edge(edge3)
        self.computation_graph.add_edge(edge4)
    def _setup_cli(self):
        self.cli_menu.add("Run adversarial review", str(self._cli_run_review), "1")
        self.cli_menu.add("View audit log", str(self._cli_view_audit), "2")
        self.cli_menu.add("Configure agent", str(self._cli_configure), "3")
        self.cli_menu.add("Exit", "exit", "4")
    def _log_audit(self, action: str, details: Dict[str, Any]):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "agent_id": self._review_config.agent_id
        }
        self.audit_log.append(entry)
        self.cli_output.log(f"Audit: {action} - {json.dumps(details)[:100]}")
    def handoff(self, target_agent_id: str, message: AgentMessage) -> AgentMessage:
        self._log_audit("handoff_initiated", {"target": target_agent_id, "message_type": message.message_type})
        response = AgentMessage(
            sender=self._review_config.agent_id,
            recipient=target_agent_id,
            payload={"status": "handoff_complete", "original_message": message.payload},
            msg_type="handoff_response"
        )
        self._log_audit("handoff_completed", {"target": target_agent_id, "response_id": response.message_id})
        return response
    def _surface_funnel(self, content: str) -> FunnelResult:
        findings = []
        score = 0.0
        prompt = f"Analyze the surface level adversarial patterns in this content. Identify obvious biases, logical fallacies, or manipulative language:\n\n{content[:500]}"
        llm_response = self.llm_client.chat(prompt)
        if llm_response and llm_response.content:
            analysis = llm_response.content.lower()
            if "bias" in analysis or "fallacy" in analysis:
                findings.append("Surface level adversarial patterns detected")
                score = 0.4
            else:
                findings.append("No obvious surface level issues")
                score = 0.1
        else:
            findings.append("LLM analysis failed, using heuristic fallback")
            score = 0.2
        passed = score < 0.3
        return FunnelResult(stage="surface", score=score, findings=findings, passed=passed)
    def _structural_funnel(self, content: str) -> FunnelResult:
        findings = []
        score = 0.0
        prompt = f"Analyze the structural adversarial patterns. Look for argument framing, narrative manipulation, and structural biases:\n\n{content[:1000]}"
        llm_response = self.llm_client.chat(prompt)
        if llm_response and llm_response.content:
            analysis = llm_response.content.lower()
            if "framing" in analysis or "narrative" in analysis:
                findings.append("Structural adversarial patterns detected")
                score = 0.6
            elif "manipulation" in analysis:
                findings.append("Potential structural manipulation")
                score = 0.5
            else:
                findings.append("No structural issues found")
                score = 0.2
        else:
            findings.append("Structural analysis fallback")
            score = 0.3
        passed = score < 0.5
        return FunnelResult(stage="structural", score=score, findings=findings, passed=passed)
    def _deep_funnel(self, content: str) -> FunnelResult:
        findings = []
        score = 0.0
        prompt = f"Perform deep adversarial analysis. Identify subtle biases, implicit assumptions, and hidden agendas:\n\n{content[:2000]}"
        llm_response = self.llm_client.chat(prompt)
        if llm_response and llm_response.content:
            analysis = llm_response.content.lower()
            if "implicit" in analysis or "hidden" in analysis:
                findings.append("Deep adversarial patterns detected")
                score = 0.8
            elif "subtle" in analysis:
                findings.append("Subtle adversarial elements found")
                score = 0.7
            else:
                findings.append("No deep adversarial issues")
                score = 0.3
        else:
            findings.append("Deep analysis fallback")
            score = 0.4
        passed = score < 0.7
        return FunnelResult(stage="deep", score=score, findings=findings, passed=passed)
    def _calculate_tension_curve(self, content: str) -> Tuple[List[TensionCurvePoint], float]:
        points = []
        segments = content.split(".")
        segment_count = max(len(segments), 1)
        for i in range(min(segment_count, 10)):
            position = (i + 1) / min(segment_count, 10)
            segment_text = segments[i] if i < len(segments) else ""
            prompt = f"Rate the adversarial tension (0-1) in this text segment:\n{segment_text}"
            llm_response = self.llm_client.chat(prompt)
            tension_value = 0.5
            if llm_response and llm_response.content:
                try:
                    rating_text = llm_response.content.strip()
                    for word in rating_text.split():
                        try:
                            tension_value = float(word)
                            break
                        except ValueError:
                            continue
                except:
                    tension_value = 0.5
            gradient = 0.0
            if points:
                gradient = tension_value - points[-1].tension_value
            points.append(TensionCurvePoint(
                position=position,
                tension_value=min(max(tension_value, 0.0), 1.0),
                gradient=gradient
            ))
        overall_tension = sum(p.tension_value for p in points) / len(points) if points else 0.0
        return points, overall_tension
    def _generate_adversarial_findings(self, content: str, funnel_results: Dict[str, FunnelResult], tension_score: float) -> List[Dict[str, Any]]:
        findings = []
        for stage, result in funnel_results.items():
            if not result.passed:
                findings.append({
                    "stage": stage,
                    "severity": "high" if result.score > 0.7 else "medium",
                    "description": "; ".join(result.findings),
                    "score": result.score
                })
        if tension_score > self._review_config.tension_threshold:
            findings.append({
                "stage": "tension",
                "severity": "critical",
                "description": f"High tension score detected: {tension_score:.2f}",
                "score": tension_score
            })
        if not findings:
            findings.append({
                "stage": "overall",
                "severity": "low",
                "description": "No significant adversarial patterns detected",
                "score": 0.0
            })
        return findings
    def _generate_recommendation(self, findings: List[Dict[str, Any]], tension_score: float) -> str:
        if tension_score > 0.8:
            return "REJECT: Content contains critical adversarial patterns"
        elif tension_score > 0.6:
            return "REVIEW: Content requires human review for potential adversarial elements"
        elif any(f["severity"] == "high" for f in findings):
            return "FLAG: Content flagged for adversarial patterns, recommend modification"
        elif any(f["severity"] == "medium" for f in findings):
            return "CAUTION: Minor adversarial elements detected, proceed with awareness"
        else:
            return "ACCEPT: Content appears free of significant adversarial patterns"
    def process_review(self, review_input: ReviewInput) -> ReviewOutput:
        review_id = str(uuid.uuid4())
        self._log_audit("review_started", {"content_id": review_input.content_id, "review_id": review_id})
        surface_result = self._surface_funnel(review_input.content_text)
        self._log_audit("surface_funnel_complete", {"score": surface_result.score, "passed": surface_result.passed})
        structural_result = self._structural_funnel(review_input.content_text)
        self._log_audit("structural_funnel_complete", {"score": structural_result.score, "passed": structural_result.passed})
        deep_result = self._deep_funnel(review_input.content_text)
        self._log_audit("deep_funnel_complete", {"score": deep_result.score, "passed": deep_result.passed})
        funnel_results = {
            "surface": surface_result,
            "structural": structural_result,
            "deep": deep_result
        }
        tension_points, tension_score = self._calculate_tension_curve(review_input.content_text)
        self._log_audit("tension_analysis_complete", {"tension_score": tension_score, "points_count": len(tension_points)})
        adversarial_findings = self._generate_adversarial_findings(
            review_input.content_text, funnel_results, tension_score
        )
        recommendation = self._generate_recommendation(adversarial_findings, tension_score)
        overall_score = 1.0 - tension_score
        audit_trail = list(self.audit_log[-10:])
        output = ReviewOutput(
            review_id=review_id,
            content_id=review_input.content_id,
            overall_score=overall_score,
            tension_score=tension_score,
            funnel_results={k: v.dict() for k, v in funnel_results.items()},
            adversarial_findings=adversarial_findings,
            recommendation=recommendation,
            audit_trail=audit_trail
        )
        self._log_audit("review_completed", {"review_id": review_id, "recommendation": recommendation})
        return output
    def _cli_run_review(self):
        cli_input = CLIInput(prompt="Enter content text for adversarial review")
        content_text = cli_input.get_input()
        if not content_text:
            self.cli_output.error("No content provided")
            return
        review_input = ReviewInput(
            content_id=str(uuid.uuid4()),
            content_text=content_text,
            content_type="text"
        )
        result = self.process_review(review_input)
        self.cli_output.display_json(result.dict())
    def _cli_view_audit(self):
        self.cli_output.display_json(self.audit_log[-20:])
    def _cli_configure(self):
        cli_input = CLIInput(prompt="Enter new tension threshold (0.0-1.0)")
        threshold_str = cli_input.get_input()
        try:
            new_threshold = float(threshold_str)
            if 0.0 <= new_threshold <= 1.0:
                self._review_config.tension_threshold = new_threshold
                self.cli_output.log(f"Tension threshold updated to {new_threshold}")
            else:
                self.cli_output.error("Threshold must be between 0.0 and 1.0")
        except ValueError:
            self.cli_output.error("Invalid threshold value")
    def run_cli(self):
        self.cli_output.display("Adversarial Review Agent initialized")
        self.cli_menu.run()
if __name__ == "__main__":
    agent = AdversarialReviewAgent()
    agent.run_cli()
