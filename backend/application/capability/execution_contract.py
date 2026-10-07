from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.capability.contracts import (
    ApplicationCapabilityProtocol,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


@runtime_checkable
class AgentExecutionCapabilityProtocol(
    ApplicationCapabilityProtocol,
    Protocol,
):
    """
    Application Agent execution capability contract.

    Ownership:
        - define the transport-visible Agent execution capability
        - return canonical ExecutionResult

    Not Responsible:
        - AgentService implementation
        - Agent construction
        - runtime construction
        - transport orchestration
        - serialization
    """

    async def execute(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        ...


__all__ = [
    "AgentExecutionCapabilityProtocol",
]
