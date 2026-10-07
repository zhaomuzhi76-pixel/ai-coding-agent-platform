from __future__ import annotations

from backend.api.project_session.project_session_agent_request_factory import (
    ProjectSessionAgentRequestFactory,
)
from backend.api.project_session.project_session_api_support import (
    ProjectSessionAPISupport,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionAPIRuntimeSubmissionMixin:
    """
    Runtime-submission execution boundary.

    Owns:
        - request normalization
        - session-id extraction
        - AgentRequest construction
        - runtime submission delegation
        - execution counter
    """

    runtime_submission: ApplicationRuntimeSubmissionProtocol

    def _init_runtime_submission(
        self,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
        support: ProjectSessionAPISupport,
        request_factory: ProjectSessionAgentRequestFactory | None,
    ) -> None:
        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime_submission must implement "
                "ApplicationRuntimeSubmissionProtocol"
            )

        if not runtime_submission.ready():
            raise RuntimeError(
                "runtime submission not ready"
            )

        if not support.ready():
            raise RuntimeError(
                "project session API support not ready"
            )

        self.runtime_submission = runtime_submission
        self.request_factory = (
            request_factory
            or ProjectSessionAgentRequestFactory()
        )

        if not self.request_factory.ready():
            raise RuntimeError(
                "project session agent request factory not ready"
            )

        self.execution_count = 0

    async def execute(
        self,
        payload: dict[str, object],
    ) -> object:
        data = self.support.payload(payload)

        session_id = self.support.session_id(
            data.get("session_id")
        )

        request = data.get("request")

        if request is None:
            request = {
                key: value
                for key, value in data.items()
                if key != "session_id"
            }

        if not isinstance(request, dict):
            raise TypeError("request must dict")

        agent_request = self.request_factory.create(
            request,
            session_id,
        )

        result = await self.runtime_submission.execute(
            agent_request,
            session_id,
        )

        self.execution_count += 1
        return result

    def runtime_submission_ready(self) -> bool:
        return (
            isinstance(
                self.runtime_submission,
                ApplicationRuntimeSubmissionProtocol,
            )
            and self.runtime_submission.ready()
            and self.request_factory.ready()
        )

    def runtime_submission_dump(self) -> dict[str, object]:
        return {
            "runtime_submission": type(
                self.runtime_submission
            ).__name__,
            "request_factory": type(
                self.request_factory
            ).__name__,
            "execution_count": self.execution_count,
        }


__all__ = [
    "ProjectSessionAPIRuntimeSubmissionMixin",
]
