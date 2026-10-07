from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_decision import (
    AgentDecision,
)
from backend.core.agent.agent_orchestration_loop_state import (
    AgentOrchestrationLoopState,
)


@runtime_checkable
class AgentOrchestrationLoopProtocol(Protocol):
    """
    Core contract for bounded task orchestration loops.

    Owns:
        - loop-state transition
        - continue/replan admission
        - terminal boundary

    Does not own:
        - planning implementation
        - runtime execution implementation
        - transport
        - persistence
    """

    def state(
        self,
    ) -> AgentOrchestrationLoopState:
        ...

    def transition(
        self,
        *,
        decision: AgentDecision,
    ) -> AgentOrchestrationLoopState:
        ...

    def terminal(
        self,
    ) -> bool:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "AgentOrchestrationLoopProtocol",
]
