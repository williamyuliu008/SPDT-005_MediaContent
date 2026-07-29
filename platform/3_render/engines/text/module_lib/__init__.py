"""
PT-047 module_lib — 智能体基础设施库
"""
from .agent import (
    BaseAgent, AgentConfig, AgentContext, AgentMessage,
    AgentState, HandoffRequest, HandoffResponse,
)
from .processing_computation_graph import (
    ComputationGraph, Node, Edge, GraphNode, GraphEdge,
    COGGenerator, ComputationGraphOrchestrator,
    ComputationNode, ComputationEdge,
)
from .processing_rule_engine import (
    RuleEngine, Rule, Condition, Action,
    ProcessingRule, RuleContext,
)
from .hmi import (
    CLIOutput, CLIOutputRenderer, CLIOutputFormatter,
    CLIInterface, CLIStructuredOutput, StructuredOutput,
    CLIInput, CLIMenu, MenuItem, OutputFormatter,
)

__version__ = "0.1.0-stub"

__all__ = [
    "BaseAgent", "AgentConfig", "AgentContext", "AgentMessage",
    "AgentState", "HandoffRequest", "HandoffResponse",
    "ComputationGraph", "Node", "Edge", "GraphNode", "GraphEdge",
    "COGGenerator", "ComputationGraphOrchestrator",
    "ComputationNode", "ComputationEdge",
    "RuleEngine", "Rule", "Condition", "Action",
    "ProcessingRule", "RuleContext",
    "CLIOutput", "CLIOutputRenderer", "CLIOutputFormatter",
    "CLIInterface", "CLIStructuredOutput", "StructuredOutput",
    "CLIInput", "CLIMenu", "MenuItem", "OutputFormatter",
]
