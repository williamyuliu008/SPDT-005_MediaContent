"""
module_lib.processing_computation_graph — PT-047 计算图模块
-stub: ComputationGraph / COGGenerator / ComputationGraphOrchestrator
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

__all__ = [
    "ComputationGraph", "Node", "Edge", "GraphNode", "GraphEdge",
    "COGGenerator", "ComputationGraphOrchestrator",
    "ComputationNode", "ComputationEdge",
]


# ── 节点与边 ─────────────────────────────────────────────
class Node:
    """计算图节点。兼容: Node / ComputationNode / GraphNode。接受任意额外字段。"""
    def __init__(self, id: str = "", func: Optional[Callable] = None,
                 metadata: Dict[str, Any] = None,
                 node_id: str = "", node_type: str = "",
                 config: Dict[str, Any] = None,
                 description: str = "",
                 **extra_kwargs):
        self.id = id or node_id
        self.func = func
        self.metadata = metadata or {}
        self.node_type = node_type
        self.config = config or {}
        self.description = description
        self.extra: Dict[str, Any] = extra_kwargs

    def run(self, input_data: Any) -> Any:
        if self.func:
            return self.func(input_data)
        return input_data

    def __repr__(self):
        return f"Node(id={self.id!r}, type={self.node_type!r})"


# 别名
ComputationNode = Node
GraphNode = Node


@dataclass
class Edge:
    """计算图边。兼容: Edge / ComputationEdge / GraphEdge。"""
    source: str = ""
    target: str = ""
    label: str = ""
    # 别名
    source_id: str = ""
    target_id: str = ""
    edge_id: str = ""
    weight: float = 1.0

    def __post_init__(self):
        if not self.source and self.source_id:
            self.source = self.source_id
        if not self.target and self.target_id:
            self.target = self.target_id

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "target": self.target, "label": self.label,
                "edge_id": self.edge_id, "weight": self.weight}


# 别名
ComputationEdge = Edge
GraphEdge = Edge


# ── 计算图 ────────────────────────────────────────────────
class ComputationGraph:
    """PT-047 计算图引擎。节点注册→边连接→拓扑执行。"""

    def __init__(self, name: str = ""):
        self.name = name or f"graph_{id(self)}"
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._entry_nodes: List[str] = []

    def add_node(self, node: Node) -> "ComputationGraph":
        self.nodes[node.id] = node
        return self

    def add_edge(self, edge: Edge) -> "ComputationGraph":
        self.edges.append(edge)
        return self

    def add_entry(self, node_id: str) -> "ComputationGraph":
        if node_id not in self._entry_nodes:
            self._entry_nodes.append(node_id)
        return self

    def get_candidates(self) -> List[Dict[str, Any]]:
        """返回所有节点的候选数据（供三层漏斗使用）。"""
        return [
            {"node_id": nid, "node": n, "metadata": n.metadata}
            for nid, n in self.nodes.items()
        ]

    def run(self, initial_data: Any = None) -> Dict[str, Any]:
        """拓扑执行。返回 {node_id: result}。"""
        if not self._entry_nodes:
            self._entry_nodes = [nid for nid in self.nodes if
                not any(e.target == nid for e in self.edges)]
        results: Dict[str, Any] = {"_input": initial_data}

        def visit(nid: str, visited: set):
            if nid in visited:
                return results.get(nid)
            visited.add(nid)
            node = self.nodes.get(nid)
            if not node:
                return None
            upstream = {e.source: results[e.source] for e in self.edges
                        if e.target == nid and e.source in results}
            input_val = upstream.get("_input", initial_data)
            for src, val in upstream.items():
                if src != "_input":
                    input_val = val
            try:
                results[nid] = node.run(input_val)
            except Exception as ex:
                results[nid] = {"_error": str(ex)}
            return results[nid]

        visited: set = set()
        for entry in self._entry_nodes:
            visit(entry, visited)
        return results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "nodes": list(self.nodes.keys()),
            "edges": [e.to_dict() for e in self.edges],
            "entry_nodes": self._entry_nodes,
        }


# ── COG 生成器 ───────────────────────────────────────────
class COGGenerator:
    """COG (Chapter-level Orchestration Graph) 生成器。"""

    def __init__(self):
        self.templates: Dict[str, ComputationGraph] = {}

    def build_from_input(self, input_data: Dict[str, Any], routing_rules: Dict[str, Any]) -> ComputationGraph:
        """根据输入和路由规则构建计算图。"""
        graph = ComputationGraph(name="cog_from_input")
        intent = input_data.get("intent", "default")
        graph.add_node(Node(id="input_parse", func=lambda x: {"parsed": str(x)[:100]}))
        graph.add_node(Node(id="intent_classify", func=lambda x: {"intent": intent}))
        graph.add_node(Node(id="candidates", func=lambda x: []))
        graph.add_edge(Edge("input_parse", "intent_classify"))
        graph.add_edge(Edge("intent_classify", "candidates"))
        graph.add_entry("input_parse")
        return graph


# ── 计算图编排器 ─────────────────────────────────────────
class ComputationGraphOrchestrator:
    """多图编排器。"""

    def __init__(self):
        self.graphs: Dict[str, ComputationGraph] = {}

    def register(self, name: str, graph: ComputationGraph):
        self.graphs[name] = graph

    def run(self, graph_name: str, initial_data: Any = None) -> Dict[str, Any]:
        g = self.graphs.get(graph_name)
        if g is None:
            return {"_error": f"Graph '{graph_name}' not found"}
        return g.run(initial_data)

    def run_all(self, initial_data: Any = None) -> Dict[str, Dict[str, Any]]:
        return {name: g.run(initial_data) for name, g in self.graphs.items()}
