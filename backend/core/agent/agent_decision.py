from __future__ import annotations

from dataclasses import dataclass, field

from backend.core.agent.agent_orchestration_status import (
    AgentOrchestrationStatus,
)


@dataclass(frozen=True)
class AgentDecision:
    """
    Core-owned task-level orchestration decision.

    Owns:
        - terminal/continuation decision
        - decision reason
        - optional metadata

    Does not own:
        - planning
        - runtime execution
        - result construction
        - transport
        - persistence
    """

    status: AgentOrchestrationStatus
    reason: str = ""
    metadata: dict[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            AgentOrchestrationStatus,
        ):
            raise TypeError(
                "status must AgentOrchestrationStatus"
            )

        if not isinstance(self.reason, str):
            raise TypeError(
                "reason must str"
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def terminal(self) -> bool:
        return self.status in (
            AgentOrchestrationStatus.COMPLETED,
            AgentOrchestrationStatus.FAILED,
        )

    @property
    def continue_running(self) -> bool:
        return self.status in (
            AgentOrchestrationStatus.CONTINUE,
            AgentOrchestrationStatus.REPLAN,
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "status": self.status.value,
            "reason": self.reason,
            "metadata": dict(self.metadata),
            "terminal": self.terminal,
            "continue_running": self.continue_running,
            "ready": self.ready(),
        }


__all__ = [
    "AgentDecision",
]
