from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


@runtime_checkable
class APISubmissionProtocol(Protocol):
    """
    API submission binding contract.

    Responsibility:
        - accept an already-built AgentRequest
        - require a session identifier
        - delegate to the Application Submission Execution entry
        - return canonical ExecutionResult

    Not Responsible:
        - submission lifecycle
        - submission state
        - queue
        - scheduler
        - dispatch
        - retry
        - budget
        - rate limiting
        - agent construction
        - result construction
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
    "APISubmissionProtocol",
]
