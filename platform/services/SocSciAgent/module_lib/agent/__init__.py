"""
module_lib.agent — PT-047 智能体基础设施
-stub骨架，agent_id/接口定义，无实际LLM调用
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable, Generic, TypeVar, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

T = TypeVar('T')
T2 = TypeVar('T2')

__all__ = [
    "BaseAgent", "AgentConfig", "AgentContext", "AgentMessage",
    "AgentState", "HandoffRequest", "HandoffResponse",
]


# ── 枚举 ────────────────────────────────────────────────
class AgentState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"


# ── 数据类 ──────────────────────────────────────────────
class AgentConfig:
    """Agent 配置。接受任意额外字段。"""
    # 接受任意额外参数，存储为实例属性

    def __init__(self, agent_id: str = "default", name: str = "",
                 tags: List[str] = None, max_retries: int = 3, timeout_sec: int = 300,
                 metadata: Dict[str, Any] = None, version: str = "1.0",
                 chroma_host: str = "localhost", chroma_port: int = 8000,
                 collection_name: str = "pt047_default",
                 funnel_layers: int = None,
                 tension_alpha: float = None,
                 **extra_kwargs):
        # 使用 object.__setattr__ 避免 __setattr__ 递归
        object.__setattr__(self, 'agent_id', agent_id)
        object.__setattr__(self, 'name', name or agent_id)
        object.__setattr__(self, 'tags', tags or [])
        object.__setattr__(self, 'max_retries', max_retries)
        object.__setattr__(self, 'timeout_sec', timeout_sec)
        object.__setattr__(self, 'metadata', metadata or {})
        object.__setattr__(self, 'version', version)
        object.__setattr__(self, 'chroma_host', chroma_host)
        object.__setattr__(self, 'chroma_port', chroma_port)
        object.__setattr__(self, 'collection_name', collection_name)
        if funnel_layers is not None:
            extra_kwargs['funnel_layers'] = funnel_layers
        if tension_alpha is not None:
            extra_kwargs['tension_alpha'] = tension_alpha
        object.__setattr__(self, 'extra', extra_kwargs)

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key)

    def __setitem__(self, key: str, value: Any):
        if hasattr(self, key) and key not in self.extra:
            object.__setattr__(self, key, value)
        else:
            self.extra[key] = value

    def get(self, key: str, default=None) -> Any:
        if hasattr(self, key):
            v = getattr(self, key)
            return v if v is not None else default
        return self.extra.get(key, default)

    def __getattr__(self, key: str) -> Any:
        """支持 extra 中的字段通过属性访问。"""
        if key.startswith('_'):
            raise AttributeError(key)
        try:
            d = object.__getattribute__(self, '__dict__')
        except AttributeError:
            raise AttributeError(key)
        if 'extra' in d and key in d['extra']:
            return d['extra'][key]
        raise AttributeError(key)

    def __setattr__(self, key: str, value: Any):
        KNOWN = {'agent_id', 'name', 'tags', 'max_retries', 'timeout_sec',
                 'metadata', 'version', 'chroma_host', 'chroma_port',
                 'collection_name', 'extra'}
        if key in KNOWN:
            object.__setattr__(self, key, value)
        else:
            # 存到 extra（extra 必须已存在）
            try:
                object.__getattribute__(self, 'extra')[key] = value
            except AttributeError:
                object.__setattr__(self, 'extra', {key: value})

    def __repr__(self):
        return f"AgentConfig(agent_id={self.agent_id!r}, extra_keys={list(self.extra.keys())})"

    def to_dict(self) -> Dict[str, Any]:
        d = {k: getattr(self, k) for k in self.__slots__ if k != 'extra' and hasattr(self, k)}
        d.update(self.extra)
        return d


@dataclass
class AgentContext:
    session_id: str = ""
    user_id: str = ""
    work_id: str = ""
    chapter_id: str = ""
    turn: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = ""  # pipeline request tracking

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "work_id": self.work_id,
            "chapter_id": self.chapter_id,
            "turn": self.turn,
            "metadata": self.metadata,
            "request_id": self.request_id,
        }


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    payload: Dict[str, Any]
    msg_type: str = "generic"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    trace_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "msg_type": self.msg_type,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
        }


@dataclass
class HandoffRequest:
    target_agent: str
    payload: Dict[str, Any]
    priority: int = 0
    reason: str = ""
    sender: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_agent": self.target_agent,
            "payload": self.payload,
            "priority": self.priority,
            "reason": self.reason,
            "sender": self.sender,
        }


@dataclass
class HandoffResponse:
    agent_id: str
    target_agent: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "target_agent": self.target_agent,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "success": self.success,
            "error": self.error,
        }


# ── 基类 ────────────────────────────────────────────────
class BaseAgent(Generic[T, T2]):
    """PT-047 全量 Agent 基类。stub 实现，满足所有导入要求。"""

    agent_id: str = "base_agent"
    agent_type: str = "generic"

    def __init__(self, *args, config: Optional[AgentConfig] = None, agent_id: str = None, **kwargs):
        """兼容性重载: 支持多种调用约定。"""
        # 如果 config 是字符串，说明 caller 搞混了顺序
        if isinstance(config, str):
            # config 实为 agent_id
            actual_aid = config
            actual_cfg = agent_id  # 可能为 AgentConfig 或 None
            config = actual_cfg
            agent_id = actual_aid
        cfg = config
        if cfg is None:
            aid = agent_id or kwargs.get("agent_id", self.agent_id)
            cfg = AgentConfig(agent_id=aid, **kwargs)
        elif isinstance(cfg, str):
            # config 是字符串而非 AgentConfig
            cfg = AgentConfig(agent_id=cfg, **kwargs)
        self.config = cfg
        self.agent_id = self.config.agent_id
        self._state = AgentState.IDLE
        self._audit_log: List[Dict[str, Any]] = []
        self._handlers: Dict[str, Callable] = {}

    @property
    def state(self) -> AgentState:
        return self._state

    @state.setter
    def state(self, value):
        self._set_state(value)

    def _set_state(self, s: AgentState):
        self._state = s

    def log(self, level: str, msg: str, **kwargs):
        entry = {
            "ts": datetime.now().isoformat(),
            "agent": self.agent_id,
            "level": level,
            "msg": msg,
            **kwargs,
        }
        self._audit_log.append(entry)

    def audit_log(self) -> List[Dict[str, Any]]:
        return self._audit_log.copy()

    # ── 标准接口 ──────────────────────────────────────
    def execute(self, input_data: Any) -> Any:
        self._set_state(AgentState.RUNNING)
        self.log("info", f"execute called with {type(input_data)}")
        return {"status": "ok", "agent": self.agent_id}

    def handoff(self, request: HandoffRequest) -> HandoffResponse:
        self.log("info", f"handoff to {request.target_agent}")
        return HandoffResponse(
            agent_id=self.agent_id,
            target_agent=request.target_agent,
            payload=request.payload,
        )

    def receive(self, message: AgentMessage) -> Any:
        self.log("info", f"received from {message.sender}: {message.msg_type}")
        return {"status": "received"}

    def reset(self):
        self._state = AgentState.IDLE
        self._audit_log.clear()
        self._handlers.clear()
