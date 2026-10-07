from __future__ import annotations

from backend.application.operational.project_session.composition.project_session_composition_integration_contract import (
    ProjectSessionCompositionIntegrationContract,
)
from backend.application.operational.project_session.composition.project_session_composition_integration_support import (
    ProjectSessionCompositionIntegrationSupport,
)
from backend.application.operational.project_session.integration.project_session_integration_factory import (
    ProjectSessionIntegrationFactory,
)
from backend.application.operational.project_session.integration.project_session_runtime_submission_bridge import (
    ProjectSessionRuntimeSubmissionBridge,
)
from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionCompositionIntegration(
    ProjectSessionCompositionIntegrationContract,
):
    """
    Final project-session runtime-submission integration boundary.

    Owns:
        - runtime-submission bridge assembly
        - readiness projection

    Does not own:
        - Agent implementation
        - submission execution implementation
        - runtime construction
        - lifecycle mutation
        - transport
        - parallel execution bridge
    """

    VERSION = "3.0"

    def __init__(
        self,
        operational: ProjectSessionOperationalContract,
        integration_factory: ProjectSessionIntegrationFactory | None = None,
        support: ProjectSessionCompositionIntegrationSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProjectSessionCompositionIntegrationSupport()
        )
        self.operational = (
            self.support.validate_operational(
                operational
            )
        )
        self.integration_factory = (
            integration_factory
            or ProjectSessionIntegrationFactory()
        )

        if not self.integration_factory.ready():
            raise RuntimeError(
                "project session integration factory unavailable"
            )

        self._runtime_submission: (
            ProjectSessionRuntimeSubmissionBridge | None
        ) = None
        self._built = False

    def build(
        self,
        *,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
    ) -> dict[str, object]:
        runtime_submission = (
            self.support.validate_runtime_submission(
                runtime_submission
            )
        )

        runtime = (
            self.integration_factory.create_runtime_submission(
                self.operational,
                runtime_submission,
            )
        )

        self._runtime_submission = (
            self.support.validate_runtime(
                runtime
            )
        )
        self._built = True

        return {
            "operational": self.operational,
            "runtime_submission": self._runtime_submission,
        }

    def runtime_submission(
        self,
    ) -> ProjectSessionRuntimeSubmissionBridge:
        self._require_built()
        return self._runtime_submission

    def ready(
        self,
    ) -> bool:
        return (
            self.support.ready()
            and self.operational.ready()
            and self.integration_factory.ready()
            and self._built
            and self._runtime_submission is not None
            and self._runtime_submission.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "built": self._built,
            "operational": self.operational.dump(),
            "runtime_submission": (
                self._runtime_submission.dump()
                if self._runtime_submission is not None
                else None
            ),
        }

    def _require_built(
        self,
    ) -> None:
        if not self._built:
            raise RuntimeError(
                "project session composition integration not built"
            )


__all__ = [
    "ProjectSessionCompositionIntegration",
]
