from __future__ import annotations

from backend.application.operational.project_session.integration.project_session_integration_support import (
    ProjectSessionIntegrationSupport,
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


class ProjectSessionIntegrationFactory:
    """
    Sole construction owner for the project-session runtime
    submission integration bridge.

    Owns:
        - runtime-submission bridge construction
        - dependency validation

    Does not own:
        - execution implementation
        - runtime construction
        - lifecycle mutation
        - transport
    """

    VERSION = "3.0"

    def __init__(
        self,
        support: ProjectSessionIntegrationSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProjectSessionIntegrationSupport()
        )

    def create_runtime_submission(
        self,
        operational: ProjectSessionOperationalContract,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
    ) -> ProjectSessionRuntimeSubmissionBridge:
        bridge = ProjectSessionRuntimeSubmissionBridge(
            operational,
            runtime_submission,
            self.support,
        )
        self._require_ready(
            bridge,
            "runtime submission integration bridge",
        )
        return bridge

    def ready(self) -> bool:
        return self.support.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "bridge": (
                "ProjectSessionRuntimeSubmissionBridge"
            ),
        }

    @staticmethod
    def _require_ready(
        bridge: object,
        name: str,
    ) -> None:
        ready = getattr(
            bridge,
            "ready",
            None,
        )

        if not callable(ready) or not ready():
            raise RuntimeError(
                f"{name} unavailable"
            )


__all__ = [
    "ProjectSessionIntegrationFactory",
]
