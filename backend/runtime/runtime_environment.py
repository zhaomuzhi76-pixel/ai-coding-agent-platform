from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.core.agent.agent_request import AgentRequest


@dataclass(slots=True)
class RuntimeEnvironment:
    """
    Runtime execution environment container.

    Responsibility:
        - hold runtime dependencies
        - provide runtime snapshot

    Not Responsible:
        - execution
        - persistence
        - serialization
        - monitoring
    """

    request: AgentRequest | None = None
    workspace: Any = None
    memory: Any = None
    planner: Any = None
    session: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def dump(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "workspace": self.workspace,
            "memory": self.memory,
            "planner": self.planner,
            "session": self.session,
            "metadata": self.metadata,
        }


__all__ = [
    "RuntimeEnvironment",
]
