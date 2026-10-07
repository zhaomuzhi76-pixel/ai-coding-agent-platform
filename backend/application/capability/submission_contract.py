from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import AgentRequest
from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.core.result import ExecutionResult


@runtime_checkable
class ApplicationSubmissionProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Application Submission capability boundary.

    Responsibility:
        - expose application-level submission admission
        - consume AgentRequest
        - delegate to execution submission integration
        - expose capability readiness

    Not Responsible:
        - submission storage
        - submission lifecycle
        - queue
        - scheduler
        - dispatch
        - retry
        - budget
        - rate limiting
        - result ownership
        - execution
        - transport
    """

    async def submit(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        ...

__all__ = [
    "ApplicationSubmissionProtocol",
]
