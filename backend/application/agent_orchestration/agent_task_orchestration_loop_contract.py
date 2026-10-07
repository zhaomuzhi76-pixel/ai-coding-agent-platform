from __future__ import annotations

from typing import Protocol

from backend.core.agent.agent_decision import AgentDecision
from backend.core.agent.agent_orchestration_loop_protocol import (
    AgentOrchestrationLoopProtocol,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class AgentTaskOrchestrationLoopContract(
    AgentOrchestrationLoopProtocol,
    Protocol,
):
    """
    Application contract for bounded autonomous task execution.

    Owns:
        - repeated task execution
        - decision-driven iteration transition
        - bounded termination

    Does not own:
        - planning implementation
        - runtime implementation
        - decision policy implementation
        - transport
    """

    async def execute(
        self,
        *,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        ...

    def last_decision(
        self,
    ) -> AgentDecision | None:
        ...


__all__ = [
    "AgentTaskOrchestrationLoopContract",
]
