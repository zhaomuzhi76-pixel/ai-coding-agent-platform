from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import AgentRequest
from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.core.result import ExecutionResult


@runtime_checkable
class AgentServiceProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical application Agent service contract.

    Owns:
        - application-level Agent execution surface
        - readiness projection
        - execution-readiness projection
        - diagnostic projection

    Does not own:
        - Agent implementation construction
        - runtime execution construction
        - transport
    """

    async def execute(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        ...

    def execution_ready(
        self,
    ) -> bool:
        ...


__all__ = [
    "AgentServiceProtocol",
]
