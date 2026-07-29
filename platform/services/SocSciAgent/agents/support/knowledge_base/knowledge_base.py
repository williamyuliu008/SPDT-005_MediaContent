import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from module_lib.agent import BaseAgent, AgentConfig, AgentMessage
from module_lib.processing_computation_graph import ComputationGraph, ComputationNode, ComputationEdge
from module_lib.hmi import CLIOutput, StructuredOutput
from shared.tools.llm_clients import LLMClient
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KnowledgeBaseAgent")
class KnowledgeBaseConfig(BaseModel):
    agent_id: str = "knowledge_base_agent_v1"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    collection_name: str = "knowledge_base"
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gpt-4"
    max_context_length: int = 4096
    temperature: float = 0.3
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.7
class KnowledgeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None
    use_llm: bool = True
class QueryResponse(BaseModel):
    results: List[KnowledgeEntry]
    total_found: int
    query_time_ms: float
    llm_enhanced: bool = False
    llm_answer: Optional[str] = None
class AuditLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    action: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = Field(default_factory=dict)
class RuleEngine:
    def __init__(self, rules: List[Dict[str, Any]] = None):
        self.rules = rules or []
        self.audit_log: List[AuditLogEntry] = []
    def add_rule(self, rule: Dict[str, Any]) -> None:
        self.rules.append(rule)
        self._log_action("add_rule", {"rule": rule})
    def evaluate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        triggered = []
        for rule in self.rules:
            if self._match_condition(rule.get("condition", {}), context):
                triggered.append(rule)
                self._log_action("rule_triggered", {"rule": rule, "context": context})
        return triggered
    def _match_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        field = condition.get("field")
        operator = condition.get("operator", "eq")
        value = condition.get("value")
        if field not in context:
            return False
        context_value = context[field]
        if operator == "eq":
            return context_value == value
        elif operator == "gt":
            return context_value > value
        elif operator == "lt":
            return context_value < value
        elif operator == "contains":
            return value in context_value
        elif operator == "in":
            return context_value in value
        return False
    def _log_action(self, action: str, details: Dict[str, Any]) -> None:
        entry = AuditLogEntry(agent_id="rule_engine", action=action, details=details)
        self.audit_log.append(entry)
class ThreeLayerFunnel:
    def __init__(self, thresholds: List[float] = None):
        self.thresholds = thresholds or [0.3, 0.6, 0.9]
        self.audit_log: List[AuditLogEntry] = []
    def process(self, items: List[Tuple[Any, float]]) -> List[Tuple[Any, float, int]]:
        results = []
        for item, score in items:
            layer = self._assign_layer(score)
            results.append((item, score, layer))
            self._log_action("funnel_processed", {"item_id": str(id(item)), "score": score, "layer": layer})
        return results
    def _assign_layer(self, score: float) -> int:
        for i, threshold in enumerate(self.thresholds):
            if score <= threshold:
                return i + 1
        return len(self.thresholds) + 1
    def _log_action(self, action: str, details: Dict[str, Any]) -> None:
        entry = AuditLogEntry(agent_id="three_layer_funnel", action=action, details=details)
        self.audit_log.append(entry)
class TensionCurve:
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.history: List[float] = []
        self.audit_log: List[AuditLogEntry] = []
    def add_point(self, value: float) -> None:
        self.history.append(value)
        if len(self.history) > self.window_size:
            self.history.pop(0)
        self._log_action("point_added", {"value": value, "history_length": len(self.history)})
    def compute_tension(self) -> float:
        if len(self.history) < 2:
            return 0.0
        diffs = [abs(self.history[i] - self.history[i-1]) for i in range(1, len(self.history))]
        tension = sum(diffs) / len(diffs)
        self._log_action("tension_computed", {"tension": tension, "diffs": diffs})
        return tension
    def get_curve_data(self) -> Dict[str, Any]:
        return {
            "history": self.history,
            "tension": self.compute_tension(),
            "window_size": self.window_size
        }
    def _log_action(self, action: str, details: Dict[str, Any]) -> None:
        entry = AuditLogEntry(agent_id="tension_curve", action=action, details=details)
        self.audit_log.append(entry)
class KnowledgeBaseAgent(BaseAgent):
    def __init__(self, config: KnowledgeBaseConfig = None):
        self.config = config or KnowledgeBaseConfig()
        super().__init__(AgentConfig(
            agent_id=config.agent_id if config else "knowledge_base",
            embedding_model=getattr(config, 'embedding_model', 'all-MiniLM-L6-v2') if config else 'all-MiniLM-L6-v2'
        ))
        self.audit_log: List[AuditLogEntry] = []
        self.rule_engine = RuleEngine()
        self.funnel = ThreeLayerFunnel()
        self.tension_curve = TensionCurve()
        self._init_chroma()
        self._init_embedding()
        self._init_llm()
        self._init_computation_graph()
        self._log_action("agent_initialized", {"config": self.config.dict()})
    def _init_chroma(self) -> None:
        try:
            self.chroma_client = chromadb.HttpClient(
                host=self.config.chroma_host,
                port=self.config.chroma_port,
                settings=Settings(allow_reset=True)
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.config.collection_name
            )
            logger.info(f"Connected to ChromaDB collection: {self.config.collection_name}")
        except Exception as e:
            logger.warning(f"ChromaDB not available: {e}. Running in stub mode.")
    def _init_embedding(self) -> None:
        try:
            self.embedding_model = SentenceTransformer(self.config.embedding_model)
            logger.info(f"Loaded embedding model: {self.config.embedding_model}")
        except Exception as e:
            logger.warning(f"Embedding model not available: {e}. Running in stub mode.")
    def _init_llm(self) -> None:
        try:
            self.llm_client = LLMClient(model=self.config.llm_model)
            logger.info(f"Initialized LLM client with model: {self.config.llm_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.llm_client = None
    def _init_computation_graph(self) -> None:
        self.computation_graph = ComputationGraph()
        node_ingest = ComputationNode(id="ingest", type="input", config={"action": "ingest"})
        node_embed = ComputationNode(id="embed", type="process", config={"action": "embed"})
        node_store = ComputationNode(id="store", type="output", config={"action": "store"})
        node_retrieve = ComputationNode(id="retrieve", type="process", config={"action": "retrieve"})
        node_llm = ComputationNode(id="llm_enhance", type="process", config={"action": "llm"})
        node_output = ComputationNode(id="output", type="output", config={"action": "output"})
        self.computation_graph.add_node(node_ingest)
        self.computation_graph.add_node(node_embed)
        self.computation_graph.add_node(node_store)
        self.computation_graph.add_node(node_retrieve)
        self.computation_graph.add_node(node_llm)
        self.computation_graph.add_node(node_output)
        self.computation_graph.add_edge(ComputationEdge(source="ingest", target="embed"))
        self.computation_graph.add_edge(ComputationEdge(source="embed", target="store"))
        self.computation_graph.add_edge(ComputationEdge(source="retrieve", target="llm_enhance"))
        self.computation_graph.add_edge(ComputationEdge(source="llm_enhance", target="output"))
        logger.info("Initialized computation graph")
    def handoff(self, target_agent_id: str, message: AgentMessage) -> AgentMessage:
        self._log_action("handoff_initiated", {"target": target_agent_id, "message": message.dict()})
        response = AgentMessage(
            sender_id=self.config.agent_id,
            receiver_id=target_agent_id,
            content=json.dumps({"handoff": True, "original_message": message.content})
        )
        self._log_action("handoff_completed", {"response": response.dict()})
        return response
    def add_knowledge(self, entry: KnowledgeEntry) -> str:
        self._log_action("add_knowledge_started", {"entry_id": entry.id})
        embedding = self._get_embedding(entry.content)
        entry.embedding = embedding
        self.collection.add(
            ids=[entry.id],
            embeddings=[embedding],
            metadatas=[entry.metadata],
            documents=[entry.content]
        )
        self._log_action("add_knowledge_completed", {"entry_id": entry.id})
        return entry.id
    def batch_add_knowledge(self, entries: List[KnowledgeEntry]) -> List[str]:
        ids = []
        for entry in entries:
            ids.append(self.add_knowledge(entry))
        return ids
    def query_knowledge(self, request: QueryRequest) -> QueryResponse:
        self._log_action("query_started", {"query": request.query})
        start_time = datetime.now(timezone.utc)
        query_embedding = self._get_embedding(request.query)
        where_filter = request.filters if request.filters else None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=request.top_k,
            where=where_filter
        )
        entries = []
        for i in range(len(results["ids"][0])):
            entry = KnowledgeEntry(
                id=results["ids"][0][i],
                content=results["documents"][0][i],
                metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            entries.append(entry)
        funnel_items = [(entry, 1.0 - (i / len(entries))) for i, entry in enumerate(entries)]
        funnel_results = self.funnel.process(funnel_items)
        filtered_entries = [item[0] for item in funnel_results if item[2] <= 2]
        self.tension_curve.add_point(len(filtered_entries))
        tension = self.tension_curve.compute_tension()
        llm_answer = None
        if request.use_llm and self.llm_client and filtered_entries:
            context = "\n".join([e.content for e in filtered_entries])
            prompt = f"Based on the following knowledge base entries, answer the query: {request.query}\n\nContext:\n{context}"
            llm_answer = self.llm_client.generate(prompt, max_tokens=500)
        query_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        response = QueryResponse(
            results=filtered_entries,
            total_found=len(filtered_entries),
            query_time_ms=query_time,
            llm_enhanced=request.use_llm and llm_answer is not None,
            llm_answer=llm_answer
        )
        self._log_action("query_completed", {"response": response.dict()})
        return response
    def delete_knowledge(self, entry_id: str) -> bool:
        self._log_action("delete_started", {"entry_id": entry_id})
        try:
            self.collection.delete(ids=[entry_id])
            self._log_action("delete_completed", {"entry_id": entry_id})
            return True
        except Exception as e:
            logger.error(f"Failed to delete entry {entry_id}: {e}")
            self._log_action("delete_failed", {"entry_id": entry_id, "error": str(e)})
            return False
    def update_knowledge(self, entry_id: str, new_content: str, new_metadata: Dict[str, Any] = None) -> bool:
        self._log_action("update_started", {"entry_id": entry_id})
        try:
            self.delete_knowledge(entry_id)
            new_entry = KnowledgeEntry(
                id=entry_id,
                content=new_content,
                metadata=new_metadata or {}
            )
            self.add_knowledge(new_entry)
            self._log_action("update_completed", {"entry_id": entry_id})
            return True
        except Exception as e:
            logger.error(f"Failed to update entry {entry_id}: {e}")
            self._log_action("update_failed", {"entry_id": entry_id, "error": str(e)})
            return False
    def get_statistics(self) -> Dict[str, Any]:
        count = self.collection.count()
        return {
            "total_entries": count,
            "tension_curve": self.tension_curve.get_curve_data(),
            "rules_count": len(self.rule_engine.rules),
            "audit_log_count": len(self.audit_log)
        }
    def _get_embedding(self, text: str) -> List[float]:
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    def _log_action(self, action: str, details: Dict[str, Any]) -> None:
        entry = AuditLogEntry(
            agent_id=self.config.agent_id,
            action=action,
            details=details
        )
        self.audit_log.append(entry)
        logger.info(f"Audit: {action} - {json.dumps(details, default=str)}")
    def get_audit_log(self, limit: int = 100) -> List[AuditLogEntry]:
        return self.audit_log[-limit:]
app = FastAPI(title="Knowledge Base Agent API")
agent = KnowledgeBaseAgent()
@app.post("/knowledge/add", response_model=Dict[str, str])
async def add_knowledge_endpoint(entry: KnowledgeEntry):
    entry_id = agent.add_knowledge(entry)
    return {"entry_id": entry_id, "status": "success"}
@app.post("/knowledge/batch_add", response_model=Dict[str, List[str]])
async def batch_add_knowledge_endpoint(entries: List[KnowledgeEntry]):
    ids = agent.batch_add_knowledge(entries)
    return {"entry_ids": ids, "status": "success"}
@app.post("/knowledge/query", response_model=QueryResponse)
async def query_knowledge_endpoint(request: QueryRequest):
    return agent.query_knowledge(request)
@app.delete("/knowledge/{entry_id}", response_model=Dict[str, Any])
async def delete_knowledge_endpoint(entry_id: str):
    success = agent.delete_knowledge(entry_id)
    return {"entry_id": entry_id, "deleted": success}
@app.put("/knowledge/{entry_id}", response_model=Dict[str, Any])
async def update_knowledge_endpoint(entry_id: str, content: str, metadata: Dict[str, Any] = None):
    success = agent.update_knowledge(entry_id, content, metadata)
    return {"entry_id": entry_id, "updated": success}
@app.get("/knowledge/statistics", response_model=Dict[str, Any])
async def get_statistics_endpoint():
    return agent.get_statistics()
@app.get("/knowledge/audit_log", response_model=List[AuditLogEntry])
async def get_audit_log_endpoint(limit: int = 100):
    return agent.get_audit_log(limit)
@app.post("/knowledge/handoff")
async def handoff_endpoint(target_agent_id: str, message: AgentMessage):
    response = agent.handoff(target_agent_id, message)
    return response
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
