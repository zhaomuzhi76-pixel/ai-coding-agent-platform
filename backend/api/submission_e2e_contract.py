from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.result import ExecutionResult


@runtime_checkable
class APISubmissionE2EProtocol(Protocol):
    """
    Real API Submission end-to-end contract.

    Responsibility:
        - expose the assembled submission HTTP route
        - expose readiness and diagnostics
        - preserve canonical ExecutionResult semantics

    Not Responsible:
        - submission implementation
        - application capability registration
        - Agent construction
        - execution policy
        - queue
        - scheduler
        - dispatch
        - retry
        - budget
        - rate limiting
        - transport result construction
    """

    async def execute(
        self,
        payload: dict[str, object],
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
    "APISubmissionE2EProtocol",
]
