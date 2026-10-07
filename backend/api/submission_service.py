from __future__ import annotations

from backend.api.submission_contract import (
    APISubmissionProtocol,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class APISubmissionService(APISubmissionProtocol):
    """
    API submission facade over the canonical application
    runtime submission boundary.

    Owns:
        - API admission validation
        - ApplicationRuntimeSubmission delegation
        - API-facing readiness projection

    Does not own:
        - runtime gateway
        - execution construction
        - queue
        - scheduler
        - dispatch
        - retry
        - budget
        - rate limiting
        - result creation
        - transport serialization
    """

    VERSION = "3.0"

    def __init__(
        self,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
    ) -> None:
        if runtime_submission is None:
            raise ValueError(
                "application runtime submission required"
            )

        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime_submission must implement "
                "ApplicationRuntimeSubmissionProtocol"
            )

        self.runtime_submission = runtime_submission
        self.submission_count = 0
        self.failure_count = 0

    async def execute(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        self._validate(
            request=request,
            session_id=session_id,
        )

        try:
            result = await self.runtime_submission.execute(
                request=request,
                session_id=session_id,
            )

            if not isinstance(
                result,
                ExecutionResult,
            ):
                raise TypeError(
                    "application runtime submission must return "
                    "ExecutionResult"
                )

            self.submission_count += 1
            return result

        except Exception:
            self.failure_count += 1
            raise

    def ready(self) -> bool:
        return bool(
            self.runtime_submission is not None
            and self.runtime_submission.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "submission_count": self.submission_count,
            "failure_count": self.failure_count,
            "runtime_submission": (
                type(
                    self.runtime_submission
                ).__name__
            ),
        }

    @staticmethod
    def _validate(
        *,
        request: AgentRequest,
        session_id: str,
    ) -> None:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must AgentRequest"
            )

        if not request.ready():
            raise ValueError(
                "request not ready"
            )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session id required"
            )


__all__ = [
    "APISubmissionService",
]
