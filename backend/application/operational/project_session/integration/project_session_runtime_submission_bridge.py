from __future__ import annotations

from backend.application.operational.project_session.integration.project_session_integration_contract import (
    ProjectSessionIntegrationBridgeContract,
)
from backend.application.operational.project_session.integration.project_session_integration_support import (
    ProjectSessionIntegrationSupport,
)
from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)
from backend.core.result import ExecutionResult


class ProjectSessionRuntimeSubmissionBridge(
    ProjectSessionIntegrationBridgeContract,
):
    """
    Active-session gate for runtime-facing submission.

    Owns:
        - active-session admission
        - runtime submission delegation
        - session_id preservation
    """

    VERSION = "1.0"

    def __init__(
        self,
        operational: ProjectSessionOperationalContract,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
        support: ProjectSessionIntegrationSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProjectSessionIntegrationSupport()
        )
        self.operational = (
            self.support.validate_operational(
                operational
            )
        )

        self.runtime_submission = (
            self.support.validate_target(
                runtime_submission,
                "runtime submission",
            )
        )

        if not isinstance(
            self.runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime submission must implement "
                "ApplicationRuntimeSubmissionProtocol"
            )

        self.execution_count = 0

    async def execute(
        self,
        request: object,
        session_id: str,
    ) -> ExecutionResult:
        value = self.support.validate_session(
            session_id
        )

        self.operational.require_active(
            value
        )

        result = await self.runtime_submission.execute(
            request,
            value,
        )

        result = self.support.validate_result(
            result
        )

        self.execution_count += 1
        return result

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.operational.ready()
            and self.runtime_submission.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "runtime_submission": type(
                self.runtime_submission
            ).__name__,
            "operational": type(
                self.operational
            ).__name__,
        }


__all__ = [
    "ProjectSessionRuntimeSubmissionBridge",
]
