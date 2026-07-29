"""
SmartTextPlatform — Shared Module: Decision Log
所有集群共用 — 工具调用可追溯
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

@dataclass
class DecisionLog:
    """FR: 所有 Agent 工具调用记录"""
    agent_id: str
    cluster_id: str
    action: str
    input_summary: str
    output_summary: str
    timestamp: str = ""
    tools_used: list = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class DecisionLogger:
    """集群级决策日志记录器"""
    
    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        self._entries: list[DecisionLog] = []
    
    def log(self, agent_id: str, action: str, 
            input_summary: str, output_summary: str,
            tools: list = None) -> DecisionLog:
        entry = DecisionLog(
            agent_id=agent_id,
            cluster_id=self.cluster_id,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            tools_used=tools or [],
        )
        self._entries.append(entry)
        return entry
    
    def to_list(self) -> list:
        return [asdict(e) for e in self._entries]
    
    def __len__(self):
        return len(self._entries)
