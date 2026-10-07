from __future__ import annotations

from backend.application.operational.project_session.composition.project_session_composition_integration import (
    ProjectSessionCompositionIntegration,
)
from backend.application.operational.project_session.composition.project_session_composition_integration_support import (
    ProjectSessionCompositionIntegrationSupport,
)
from backend.application.operational.project_session.integration.project_session_integration_factory import (
    ProjectSessionIntegrationFactory,
)
from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionCompositionIntegrationFactory:
    """
    Sole construction owner for project-session runtime-submission
    composition integration.
    """

    VERSION = "3.0"

    def create(
        self,
        operational: ProjectSessionOperationalContract,
        *,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
    ) -> ProjectSessionCompositionIntegration:
        if not self.ready():
            raise RuntimeError(
                "project session composition integration "
                "factory unavailable"
            )

        integration = ProjectSessionCompositionIntegration(
            operational=operational,
            integration_factory=ProjectSessionIntegrationFactory(),
            support=ProjectSessionCompositionIntegrationSupport(),
        )

        integration.build(
            runtime_submission=runtime_submission,
        )

        if not integration.ready():
            raise RuntimeError(
                "project session composition integration unavailable"
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
    "ProjectSessionCompositionIntegrationFactory",
]
