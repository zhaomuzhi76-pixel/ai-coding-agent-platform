from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import AgentRequest
from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.core.result import ExecutionResult


@runtime_checkable
class ApplicationRuntimeSubmissionProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Application runtime submission contract.

    Responsibility:
        - expose the canonical runtime-level submission execution
        - consume the already assembled application submission entry
        - preserve canonical ExecutionResult semantics

    Not Responsible:
        - submission implementation
        - capability registration
        - submission lifecycle
        - queue
        - scheduler
        - dispatch
        - retry
        - budget
        - rate limiting
        - result construction
        - HTTP transport
    """

    async def execute(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
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
    "ApplicationRuntimeSubmissionProtocol",
]
