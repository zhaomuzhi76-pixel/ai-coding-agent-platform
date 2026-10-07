from __future__ import annotations

from backend.application.operational.project_session.composition.project_session_composition_integration import (
    ProjectSessionCompositionIntegration,
)
from backend.application.runtime_execution_gateway import (
    ApplicationRuntimeExecutionGatewayContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionStartupBindingSupport:
    VERSION = "3.1"

    @staticmethod
    def validate_execution_gateway(
        gateway: object,
    ) -> ApplicationRuntimeExecutionGatewayContract:
        if not isinstance(
            gateway,
            ApplicationRuntimeExecutionGatewayContract,
        ):
            raise TypeError(
                "execution gateway invalid"
            )

        if not gateway.ready():
            raise RuntimeError(
                "execution gateway not ready"
            )

        return gateway

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
    def validate_integration(
        integration: object,
    ) -> ProjectSessionCompositionIntegration:
        if not isinstance(
            integration,
            ProjectSessionCompositionIntegration,
        ):
            raise TypeError(
                "project session integration invalid"
            )

        if not integration.ready():
            raise RuntimeError(
                "project session integration not ready"
            )

        return integration

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
    "ProjectSessionStartupBindingSupport",
]
