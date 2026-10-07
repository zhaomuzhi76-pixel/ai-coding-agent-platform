from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.result import ExecutionResult


@runtime_checkable
class APISubmissionRouteProtocol(Protocol):
    """
    HTTP/WebSocket-neutral submission route contract.

    Responsibility:
        - accept transport-neutral request data
        - invoke the canonical API submission binding
        - return ExecutionResult

    Not Responsible:
        - submission implementation
        - application capability resolution
        - submission lifecycle
        - queue
        - scheduler
        - dispatch
        - retry
        - budget
        - rate limiting
        - transport serialization
    """

    async def execute(
        self,
        payload: dict[str, object],
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
    "APISubmissionRouteProtocol",
]
