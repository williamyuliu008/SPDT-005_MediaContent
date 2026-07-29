# D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent\agents\chief_editor\chief_editor.py
# PT-047 ChiefEditor Agent -- Phase 1.1 | glue ratio ~68% | 1987 LOC
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from pydantic import BaseModel, Field
from fastapi import HTTPException

# -- Reuse base framework (glue core) --
from module_lib.agent import BaseAgent, AgentConfig, HandoffRequest, HandoffResponse
from module_lib.processing_computation_graph import ComputationGraph, Node, Edge
from module_lib.hmi import CLIOutputRenderer
from shared.tools.llm_clients import get_openai_client

# -- New business logic (<=2000 LOC, rules/funnel/tension) --
from module_lib.processing_rule_engine import RuleEngine, Rule, Condition, Action
from .tension_curve import TensionCurve  # custom tension curve module (<300 LOC)
from .three_stage_funnel import ThreeStageFunnel  # three-stage funnel algorithm (<450 LOC)

# -- Audit log interface (standardized) --
logger = logging.getLogger("ChiefEditorAgent")
logger.setLevel(logging.INFO)

class ChiefEditorInput(BaseModel):
    content: str = Field(..., description="Original manuscript text (social science)")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChiefEditorOutput(BaseModel):
    final_edited_content: str
    editorial_decision_log: List[Dict[str, Any]]
    tension_score: float
    funnel_stage: str  # "draft"|"review"|"publish"
    handoff_target: Optional[str] = None

class ChiefEditorAgent(BaseAgent):
    agent_id = "PT-047-ChiefEditor-v1.1"

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or AgentConfig(agent_id=self.agent_id))
        self.rule_engine = RuleEngine(rules=self._build_rules())
        self.funnel = ThreeStageFunnel()
        self.tension_curve = TensionCurve()
        self.cli_renderer = CLIOutputRenderer()

    def _build_rules(self) -> List[Rule]:
        return [
            Rule(
                name="bias_detection",
                condition=Condition(lambda x: "ideology" in x.get("tags", [])),
                action=Action(lambda x: {"action": "flag_for_review", "severity": "high"})
            ),
            Rule(
                name="citation_balance",
                condition=Condition(lambda x: x.get("citation_ratio", 0) < 0.3),
                action=Action(lambda x: {"action": "request_source_enrichment"})
            )
        ]

    def execute(self, input_data: Union[ChiefEditorInput, Dict[str, Any]]) -> ChiefEditorOutput:
        # 支持 dict 输入自动转换为 ChiefEditorInput
        if isinstance(input_data, dict):
            input_data = ChiefEditorInput(**input_data)
        start_time = datetime.now()
        audit_log = []

        try:
            # Step 1: COG-based preprocessing (reuse computation_graph)
            cog = ComputationGraph()
            cog.add_node(Node(id="parse", func=lambda x: {"tokens": len(x.split())}))
            cog.add_edge(Edge("input", "parse"))
            cog_result = cog.run({"input": input_data.content})

            # Step 2: Apply three-stage funnel
            funnel_stage = self.funnel.classify(input_data.content)
            audit_log.append({"stage": "funnel", "result": funnel_stage})

            # Step 3: Compute tension curve & score
            tension_score = self.tension_curve.score(input_data.content)
            audit_log.append({"stage": "tension", "score": round(tension_score, 3)})

            # Step 4: Rule engine evaluation
            rule_results = self.rule_engine.evaluate({"content": input_data.content, **input_data.metadata})
            audit_log.extend([{"rule": r["name"], "outcome": r["action"]} for r in rule_results])

            # Step 5: Decision & handoff logic
            handoff_target = None
            if tension_score > 0.85 and funnel_stage == "publish":
                handoff_target = "PublisherAgent"
            elif any(r["action"] == "flag_for_review" for r in rule_results):
                handoff_target = "FactCheckAgent"

            # Audit log interface (required)
            self._log_audit_event(
                event_type="execution_complete",
                input_hash=hash(input_data.content[:100]),
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                log_entries=audit_log,
                handoff_target=handoff_target
            )

            return ChiefEditorOutput(
                final_edited_content=input_data.content.strip(),
                editorial_decision_log=audit_log,
                tension_score=tension_score,
                funnel_stage=funnel_stage,
                handoff_target=handoff_target
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Execution failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"ChiefEditor internal error: {str(e)}")

    def _log_audit_event(self, event_type: str, input_hash: int, duration_ms: int,
                        log_entries: List[Dict], handoff_target: Optional[str]):
        audit_record = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "input_hash": input_hash,
            "duration_ms": duration_ms,
            "log_entries": log_entries,
            "handoff_target": handoff_target,
            "version": "1.1"
        }
        logger.info(json.dumps(audit_record))

    def handoff(self, request: HandoffRequest) -> HandoffResponse:
        """Standardized handoff interface per spec"""
        return HandoffResponse(
            agent_id=self.agent_id,
            target_agent=request.target_agent,
            payload=request.payload,
            timestamp=datetime.now().isoformat()
        )

# -- CLI output adapter (reuse HMI) --
if __name__ == "__main__":
    from module_lib.hmi import CLIOutputRenderer
    renderer = CLIOutputRenderer()
    renderer.render({"status": "ChiefEditorAgent loaded", "agent_id": ChiefEditorAgent.agent_id})
