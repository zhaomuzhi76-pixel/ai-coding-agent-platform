from __future__ import annotations

from backend.api.submission_contract import (
    APISubmissionProtocol,
)
from backend.api.submission_service import (
    APISubmissionService,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class APISubmissionBinding(APISubmissionProtocol):
    """
    API submission binding root.

    Owns:
        - API submission service construction
        - application submission handoff
        - readiness projection

    Does not own:
        - runtime gateway construction
        - capability registration
        - runtime execution
        - submission lifecycle
        - transport routing
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
        self.service = APISubmissionService(
            runtime_submission
        )

    async def execute(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        return await self.service.execute(
            request=request,
            session_id=session_id,
        )

    def ready(self) -> bool:
        return self.service.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "runtime_submission": (
                type(
                    self.runtime_submission
                ).__name__
            ),
            "service": self.service.dump(),
        }


__all__ = [
    "APISubmissionBinding",
]
