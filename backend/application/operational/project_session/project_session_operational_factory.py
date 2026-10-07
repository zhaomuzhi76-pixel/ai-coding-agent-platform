from __future__ import annotations

from backend.application.operational.project_session.project_session_operational import (
    ProjectSessionOperational,
)
from backend.application.operational.project_session.project_session_operational_support import (
    ProjectSessionOperationalSupport,
)
from backend.workspace.project.session.service.project_session_service_contract import (
    ProjectSessionServiceContract,
)


class ProjectSessionOperationalFactory:
    """
    Construction boundary for operational session admission.

    Owns:
        - operational object construction
        - readiness validation

    Does not own:
        - service construction
        - session construction
        - registry construction
        - lifecycle implementation
        - runtime construction
    """

    VERSION = "2.0"

    def create(
        self,
        service: ProjectSessionServiceContract,
    ) -> ProjectSessionOperational:
        if not self.ready():
            raise RuntimeError(
                "project session operational factory unavailable"
            )

        operational = ProjectSessionOperational(
            service=service,
            support=ProjectSessionOperationalSupport(),
        )

        if not operational.ready():
            raise RuntimeError(
                "project session operational unavailable"
            )

        return operational

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
    "ProjectSessionOperationalFactory",
]
