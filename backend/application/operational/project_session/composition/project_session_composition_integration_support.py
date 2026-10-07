from __future__ import annotations

from backend.application.operational.project_session.integration.project_session_runtime_submission_bridge import (
    ProjectSessionRuntimeSubmissionBridge,
)
from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionCompositionIntegrationSupport:
    VERSION = "3.0"

    @staticmethod
    def validate_operational(
        operational: object,
    ) -> ProjectSessionOperationalContract:
        if not isinstance(
            operational,
            ProjectSessionOperationalContract,
        ):
            raise TypeError(
                "operational must ProjectSessionOperationalContract"
            )

        if not operational.ready():
            raise RuntimeError(
                "project session operational not ready"
            )

        return operational

    @staticmethod
    def validate_runtime_submission(
        runtime_submission: object,
    ) -> ApplicationRuntimeSubmissionProtocol:
        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime submission invalid"
            )

        if not runtime_submission.ready():
            raise RuntimeError(
                "runtime submission not ready"
            )

        return runtime_submission

    @staticmethod
    def validate_runtime(
        bridge: object,
    ) -> ProjectSessionRuntimeSubmissionBridge:
        if not isinstance(
            bridge,
            ProjectSessionRuntimeSubmissionBridge,
        ):
            raise TypeError(
                "runtime submission bridge invalid"
            )

        if not bridge.ready():
            raise RuntimeError(
                "runtime submission bridge not ready"
            )

        return bridge

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionCompositionIntegrationSupport",
]
