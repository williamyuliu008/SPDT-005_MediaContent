"""
module_lib.processing_rule_engine — PT-047 规则引擎模块
-stub: RuleEngine / Rule / Condition / Action / ProcessingRule / RuleContext
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

__all__ = [
    "RuleEngine", "Rule", "Condition", "Action",
    "ProcessingRule", "RuleContext",
]


@dataclass
class Condition:
    """规则条件。接受 lambda 或函数。"""
    func: Callable[[Any], bool]

    def evaluate(self, ctx: Dict[str, Any]) -> bool:
        try:
            return bool(self.func(ctx))
        except Exception:
            return False

    @classmethod
    def always_true(cls) -> "Condition":
        return cls(func=lambda _: True)


@dataclass
class Action:
    """规则动作。执行副作用，返回结果字典。"""
    func: Callable[[Any], Dict[str, Any]]

    def execute(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.func(ctx)
        except Exception as ex:
            return {"_error": str(ex), "_action": "failed"}


@dataclass
class Rule:
    name: str = ""
    condition: Condition = None
    action: Action = None
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 别名
    rule_id: str = ""

    def __post_init__(self):
        if not self.name and self.rule_id:
            self.name = self.rule_id
    """PT-047 规则定义。"""
    name: str
    condition: Condition
    action: Action
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def match(self, ctx: Dict[str, Any]) -> bool:
        return self.enabled and self.condition.evaluate(ctx)

    def apply(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        result = self.action.execute(ctx) if self.match(ctx) else None
        return {
            "rule": self.name,
            "name": self.name,
            "condition_met": self.match(ctx),
            "action_result": result,
            "action": result,  # 兼容 agent 期望的键名
            "timestamp": datetime.now().isoformat(),
        }


@dataclass
class ProcessingRule:
    """处理规则（别名，含额外元数据）。"""
    rule_id: str = ""
    name: str = ""
    condition: Callable[[Any], bool] = None
    action: Callable[[Any], Any] = None
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self):
        if not self.rule_id and self.name:
            self.rule_id = self.name

    def apply(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        try:
            matched = bool(self.condition(ctx)) if self.condition else False
            result = self.action(ctx) if matched and self.action else None
            return {"rule_id": self.rule_id, "matched": matched, "result": result}
        except Exception as ex:
            return {"rule_id": self.rule_id, "matched": False, "error": str(ex)}


@dataclass
class RuleContext:
    """规则执行上下文容器。"""
    context_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_result(self, result: Dict[str, Any]):
        self.results.append(result)


class RuleEngine:
    """PT-047 规则引擎。按优先级执行规则。"""

    def __init__(self, rules: Optional[List[Rule]] = None, **kwargs):
        self._rules: List[Rule] = rules or []
        self._extra = kwargs

    def add_rule(self, rule: Rule) -> "RuleEngine":
        self._rules.append(rule)
        self._rules.sort(key=lambda r: -r.priority)
        return self

    def evaluate(self, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for rule in self._rules:
            if rule.match(ctx):
                results.append(rule.apply(ctx))
        return results

    def apply_rules(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"results": self.evaluate(ctx), "ctx": ctx}

    def match(self, ctx: Dict[str, Any]) -> List[str]:
        return [r.name for r in self._rules if r.match(ctx)]
