"""工具强制触发契约。职责：只描述规则与匹配结果。
不匹配（matcher 管）、不执行（prefetch/loop 管）、不持状态。
与 chat_loop 边界：本层不改 chat_loop；loop.py 是外层包装。"""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

def _freeze(m: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(m))

@dataclass(frozen=True)
class TriggerRule:
    """一条触发规则。arg_map：正则组号 → 工具参数名。"""
    id: str
    pattern: str
    tool: str
    arg_map: Mapping[str, Any] = field(default_factory=dict)
    priority: int = 100
    enabled: bool = True
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "arg_map", _freeze(self.arg_map))
        object.__setattr__(self, "meta", _freeze(self.meta))
        if not self.id.strip(): raise ValueError("TriggerRule.id required")
        if not self.pattern.strip(): raise ValueError("TriggerRule.pattern required")
        if not self.tool.strip(): raise ValueError("TriggerRule.tool required")

@dataclass(frozen=True)
class TriggerMatch:
    rule_id: str
    tool: str
    arguments: Mapping[str, Any] = field(default_factory=dict)
    matched_text: str = ""
    priority: int = 100

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", _freeze(self.arguments))

__all__ = ["TriggerRule", "TriggerMatch"]
