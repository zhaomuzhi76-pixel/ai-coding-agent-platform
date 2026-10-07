"""L4 · Agent Handoff（A 完成 → B 接管 · 单一职责）。

职责：
  · HandoffRule：声明式规则 (from_role → to_role, 触发条件)
  · HandoffManager：A → B 转交，携带 context
  · 通过 MessageBus 派发 handoff 事件

不做：路由（TaskRouter 管）、图执行（GraphExecutor 管）。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from backend.application.multi_agent.agent_registry import (
    AgentRegistry, get_default_registry,
)
from backend.application.multi_agent.message_bus import (
    MessageBus, get_default_bus,
)


@dataclass(frozen=True)
class HandoffRule:
    """转交规则（声明式）。"""
    from_role: str            # coder
    to_role: str              # reviewer
    condition: str = "always" # always / on_success / on_failure / on_review
    description: str = ""


# 内置默认规则（coder 完成后自动转 reviewer）
_DEFAULT_RULES: Tuple[HandoffRule, ...] = (
    HandoffRule("coder", "reviewer", "on_success",
                "编码完成 → 自动转审核"),
    HandoffRule("planner", "coder", "on_success",
                "规划完成 → 派发给编码"),
)


@dataclass
class HandoffRecord:
    """一次交接记录。"""
    record_id: str
    from_agent: str
    to_agent: str
    reason: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    ts: float = 0.0


class HandoffManager:
    """转交管理器。"""

    def __init__(self,
                 registry: Optional[AgentRegistry] = None,
                 bus: Optional[MessageBus] = None) -> None:
        self._reg = registry or get_default_registry()
        self._bus = bus or get_default_bus()
        self._rules: List[HandoffRule] = list(_DEFAULT_RULES)
        self._records: List[HandoffRecord] = []

    def add_rule(self, rule: HandoffRule) -> None:
        self._rules.append(rule)

    def find_target_role(self, from_agent_id: str,
                         condition: str = "on_success") -> Optional[str]:
        """按 from_agent 的 role + condition 查目标 role。"""
        src = self._reg.get(from_agent_id)
        if not src:
            return None
        for r in self._rules:
            if r.from_role == src.role and r.condition == condition:
                return r.to_role
        return None

    def handoff(self, from_agent_id: str, context: Dict[str, Any],
                condition: str = "on_success",
                reason: str = "") -> Optional[HandoffRecord]:
        """执行一次转交。无匹配规则返回 None。"""
        to_role = self.find_target_role(from_agent_id, condition)
        if not to_role:
            return None
        targets = self._reg.find_by_role(to_role)
        if not targets:
            return None
        target = targets[0]
        import time as _t
        rec = HandoffRecord(
            record_id="h-{}-{}".format(from_agent_id, int(_t.time()*1000)),
            from_agent=from_agent_id,
            to_agent=target.agent_id,
            reason=reason or condition,
            payload=dict(context or {}),
            ts=_t.time(),
        )
        self._records.append(rec)
        self._bus.emit_to_agent(
            target.agent_id,
            topic="agent.handoff",
            payload={"from": from_agent_id,
                     "reason": rec.reason,
                     "context": rec.payload},
            sender=from_agent_id,
        )
        return rec

    def recent(self, n: int = 10) -> List[HandoffRecord]:
        return self._records[-n:]

    def stats(self) -> Dict[str, Any]:
        return {
            "rules": len(self._rules),
            "records": len(self._records),
        }


_DEFAULT: Optional[HandoffManager] = None


def get_default_handoff() -> HandoffManager:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = HandoffManager()
    return _DEFAULT


__all__ = ["HandoffRule", "HandoffRecord", "HandoffManager",
           "get_default_handoff"]
