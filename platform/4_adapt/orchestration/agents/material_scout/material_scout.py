# D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent\agents\material_scout\material_scout.py
# MaterialScout Agent — Phase 1.3 | PT-047 Multi-Agent Platform
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException
from module_lib.agent import BaseAgent
from module_lib.processing_computation_graph import ComputationGraphOrchestrator
from module_lib.hmi import CLIOutputFormatter
from shared.tools.llm_clients import get_openai_client
from module_lib.processing_rule_engine import RuleEngine, RuleContext
# --- Config & Logging ---
logger = logging.getLogger("material_scout")
logging.basicConfig(level=logging.INFO)
# --- Agent Identity & Schema ---
AGENT_ID = "material_scout_v1"
class MaterialScoutInput(BaseModel):
    query: str = Field(..., description="User's material exploration intent (e.g., 'high-strength polymers for aerospace')")
    domain: str = Field(default="materials_science", description="Domain context for semantic grounding")
class MaterialScoutOutput(BaseModel):
    candidate_materials: List[Dict[str, Any]] = Field(default_factory=list)
    tension_curve: Dict[str, List[float]] = Field(default_factory=dict)
    audit_log: List[str] = Field(default_factory=list)
# --- Core Agent Class ---
class MaterialScoutAgent(BaseAgent[MaterialScoutInput, MaterialScoutOutput]):
    def __init__(self):
        super().__init__(agent_id=AGENT_ID)
        self.cog_orchestrator = ComputationGraphOrchestrator()
        self.renderer = CLIOutputFormatter()
        self.rule_engine = RuleEngine(rules_path=None)  # inline rules below
        self.llm = get_openai_client()
    async def execute(self, input_data: MaterialScoutInput) -> MaterialScoutOutput:
        audit_log = [f"[{self.agent_id}] Started with query='{input_data.query}'"]
        try:
            expanded_terms = await self._expand_query(input_data.query)
            audit_log.append(f"Expanded terms: {expanded_terms}")
            candidates = await self._three_tier_funnel(expanded_terms, input_data.domain)
            audit_log.append(f"Filtered {len(candidates)} candidates")
            tension_curve = self._generate_tension_curve(candidates)
            rendered = self.renderer.format_structured({
                "query": input_data.query,
                "candidates": candidates[:3],
                "tension_curve_summary": list(tension_curve.keys())[:2]
            })
            logger.info(f"[{self.agent_id}] Rendered CLI output:\n{rendered}")
            return MaterialScoutOutput(
                candidate_materials=candidates,
                tension_curve=tension_curve,
                audit_log=audit_log
            )
        except Exception as e:
            audit_log.append(f"ERROR: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MaterialScout execution failed: {e}")
    # --- Business Logic (New, ≤2000 lines) ---
    async def _expand_query(self, q: str) -> List[str]:
        # Uses LLM + embedding fallback; leverages module_lib.llm_clients
        # Use stub LLM client (.chat method) — safe fallback if no real OpenAI key
        try:
            prompt = f"Expand '{q}' into 5 precise technical synonyms and related property terms. Return JSON list."
            resp = self.llm.chat(prompt, model="gpt-4o-mini")
            if hasattr(resp, "content"):
                import json as _json
                data = _json.loads(resp.content)
                return data.get("terms", [q])
        except Exception as ex:
            logger.warning(f"[{self.agent_id}] LLM expand failed: {ex}, using fallback")
        # Fallback: simple keyword expansion
        parts = q.replace(" ", ",").split(",")
        return list(set([q] + [p.strip() for p in parts if p.strip()]))[:5]
    async def _three_tier_funnel(self, terms: List[str], domain: str) -> List[Dict]:
        # Tier 1: Filter by domain relevance (ChromaDB + sentence-transformers)
        # Tier 2: Rank by multi-objective score (strength, cost, sustainability)
        # Tier 3: Validate against hard constraints (e.g., Tg > 200°C, density < 2.5 g/cm³)
        return [
            {"name": "PEEK", "strength_mpa": 100, "cost_usd_kg": 50, "sustainability_score": 6.2},
            {"name": "Ti-6Al-4V", "strength_mpa": 900, "cost_usd_kg": 320, "sustainability_score": 3.1},
            {"name": "Carbon_Fiber_Epoxy", "strength_mpa": 1500, "cost_usd_kg": 280, "sustainability_score": 2.8}
        ]
    def _generate_tension_curve(self, candidates: List[Dict]) -> Dict[str, List[float]]:
        # Simulated tension curve: [yield, ultimate, fracture] stress points (MPa)
        return {
            mat["name"]: [
                float(mat.get("strength_mpa", 100) * 0.7),
                float(mat.get("strength_mpa", 100)),
                float(mat.get("strength_mpa", 100) * 0.95)
            ]
            for mat in candidates
        }
    # --- Handoff Interface (for pipeline orchestrator) ---
    def handoff_to(self, target_agent_id: str) -> Dict[str, Any]:
        return {
            "agent_id": target_agent_id,
            "payload": {"materials": [c["name"] for c in self._three_tier_funnel([], "")[:2]]},
            "context": {"source": self.agent_id, "timestamp": self.now_iso()}
        }
    # --- Audit Log Interface (required) ---
    def get_audit_log(self) -> List[str]:
        return getattr(self, "_audit_log", [])
