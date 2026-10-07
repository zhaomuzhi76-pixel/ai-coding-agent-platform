from __future__ import annotations

from backend.application.operational.project_session.composition.project_session_composition_integration import (
    ProjectSessionCompositionIntegration,
)
from backend.application.operational.project_session.composition.project_session_composition_integration_factory import (
    ProjectSessionCompositionIntegrationFactory,
)
from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.application.operational.project_session.startup.project_session_startup_binding_contract import (
    ProjectSessionStartupBindingContract,
)
from backend.application.operational.project_session.startup.project_session_startup_binding_support import (
    ProjectSessionStartupBindingSupport,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionStartupBinding(
    ProjectSessionStartupBindingContract,
):
    """
    Startup binding for the project-session runtime-submission stack.
    """

    VERSION = "4.0"

    def __init__(
        self,
        operational: ProjectSessionOperationalContract,
        integration_factory: (
            ProjectSessionCompositionIntegrationFactory | None
        ) = None,
        support: ProjectSessionStartupBindingSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProjectSessionStartupBindingSupport()
        )

        if not isinstance(
            operational,
            ProjectSessionOperationalContract,
        ):
            raise TypeError(
                "project session operational contract required"
            )

        if not operational.ready():
            raise RuntimeError(
                "project session operational unavailable"
            )

        self.operational = operational
        self.integration_factory = (
            integration_factory
            or ProjectSessionCompositionIntegrationFactory()
        )
        self.integration: (
            ProjectSessionCompositionIntegration | None
        ) = None
        self.started = False

    def start(
        self,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
    ) -> ProjectSessionCompositionIntegration:
        if self.started and self.integration is not None:
            return self.integration

        runtime_submission = (
            self.support.validate_runtime_submission(
                runtime_submission
            )
        )

        if not self.operational.ready():
            raise RuntimeError(
                "project session operational unavailable"
            )

        integration = self.integration_factory.create(
            self.operational,
            runtime_submission=runtime_submission,
        )

        self.integration = (
            self.support.validate_integration(
                integration
            )
        )
        self.started = True
        return self.integration

    def stop(self) -> None:
        self.integration = None
        self.started = False

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.operational.ready()
            and self.integration_factory.ready()
            and (
                not self.started
                or (
                    self.integration is not None
                    and self.integration.ready()
                )
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "started": self.started,
            "integration": (
                self.integration.dump()
                if self.integration is not None
                else None
            ),
            "operational": self.operational.dump(),
        }


__all__ = [
    "ProjectSessionStartupBinding",
]
