"""Agent role protocol + registry."""
from __future__ import annotations

from typing import Dict, List, Protocol, runtime_checkable

from backend.agent.runtime.blackboard import Blackboard
from backend.agent.runtime.message import AgentMessage


@runtime_checkable
class AgentRole(Protocol):
    """A role that can execute a message against the blackboard."""

    name: str

    async def run(
        self, message: AgentMessage, blackboard: Blackboard,
    ) -> AgentMessage: ...

    def ready(self) -> bool: ...


class RoleRegistry:
    """Register + resolve agent roles by name."""

    def __init__(self) -> None:
        self._roles: Dict[str, AgentRole] = {}

    def register(self, role: AgentRole) -> None:
        name = getattr(role, "name", "")
        if not isinstance(name, str) or not name.strip():
            raise TypeError("role.name must be non-empty str")
        self._roles[name.strip()] = role

    def register_all(self, roles: List[AgentRole]) -> None:
        for r in roles:
            self.register(r)

    def get(self, name: str) -> AgentRole:
        if name not in self._roles:
            raise KeyError(f"role not found: {name}")
        return self._roles[name]

    def has(self, name: str) -> bool:
        return name in self._roles

    def names(self) -> List[str]:
        return sorted(self._roles.keys())

    def ready(self) -> bool:
        return all(r.ready() for r in self._roles.values())

    def dump(self) -> dict:
        return {
            "ready": self.ready(),
            "roles": self.names(),
            "count": len(self._roles),
        }
