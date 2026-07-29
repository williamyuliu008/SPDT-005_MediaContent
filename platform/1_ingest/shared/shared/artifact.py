"""
SmartTextPlatform — Shared Module: Artifact
Guild 间传递的标准产物格式
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

@dataclass
class Artifact:
    """Guild 间传递的产物"""
    artifact_id: str
    guild_from: str
    guild_to: str
    content: dict
    status: str = "pending"
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def mark_complete(self):
        self.status = "completed"
    
    def mark_failed(self, reason: str = ""):
        self.status = "failed"
        if reason:
            self.content["error"] = reason


class ArtifactBus:
    """产物总线 — 记录所有 Guild 间传递"""
    
    def __init__(self):
        self._artifacts: list[Artifact] = []
    
    def submit(self, guild_from: str, guild_to: str, 
               content: dict) -> Artifact:
        artifact = Artifact(
            artifact_id=f"ART-{guild_from}-{guild_to}-{datetime.now().strftime('%H%M%S')}",
            guild_from=guild_from, guild_to=guild_to,
            content=content, status="submitted",
        )
        self._artifacts.append(artifact)
        return artifact
    
    def get_by_guild(self, guild_id: str) -> list[Artifact]:
        return [a for a in self._artifacts 
                if a.guild_from == guild_id or a.guild_to == guild_id]
    
    def to_list(self) -> list:
        return [asdict(a) for a in self._artifacts]
