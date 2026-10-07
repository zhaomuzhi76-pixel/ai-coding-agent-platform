from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_decision import AgentDecision
from backend.core.agent.agent_request import AgentRequest
from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.core.result import ExecutionResult


@runtime_checkable
class AgentOrchestrationProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical Core contract for task-level Agent orchestration.
    """

    async def execute(
        self,
        *,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        ...

    def decide(
        self,
        *,
        request: AgentRequest,
        result: ExecutionResult,
    ) -> AgentDecision:
        ...


__all__ = [
    "AgentOrchestrationProtocol",
]
