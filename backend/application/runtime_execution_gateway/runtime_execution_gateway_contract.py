from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


@runtime_checkable
class ApplicationRuntimeExecutionGatewayContract(
    Protocol,
):
    """
    Canonical Application-to-Runtime execution gateway contract.

    Owns:
        - request-scoped runtime execution admission
        - runtime execution delegation
        - canonical execution result boundary
        - execution readiness projection

    Does not own:
        - transport
        - Agent construction
        - ProjectSession lifecycle implementation
        - runtime flow construction
        - startup orchestration
    """

    async def execute(
        self,
        *,
        request: AgentRequest,
        session_id: str,
        stream_callback: object | None = None,
    ) -> ExecutionResult:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def execution_ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationRuntimeExecutionGatewayContract",
]
