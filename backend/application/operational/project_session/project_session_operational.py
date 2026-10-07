from __future__ import annotations

from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.application.operational.project_session.project_session_operational_support import (
    ProjectSessionOperationalSupport,
)
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.service.project_session_service_contract import (
    ProjectSessionServiceContract,
)


class ProjectSessionOperational(
    ProjectSessionOperationalContract,
):
    """
    Application operational session admission boundary.

    Owns:
        - session admission
        - registered-session resolution
        - active-session enforcement

    Dependency direction:
        operational -> frozen project-session service contract

    Does not own:
        - project/session construction
        - registry storage
        - lifecycle mutation
        - runtime construction
        - workspace construction
        - Agent execution
        - transport
    """

    VERSION = "2.0"

    def __init__(
        self,
        service: ProjectSessionServiceContract,
        support: ProjectSessionOperationalSupport | None = None,
    ) -> None:
        self.support = (
            support
            or ProjectSessionOperationalSupport()
        )
        self.service = self.support.validate_service(
            service
        )
        self.resolve_count = 0
        self.active_count = 0

    def resolve(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        value = self.support.validate_session_id(
            session_id
        )

        session = self.service.get_session(
            value
        )

        session = self.support.validate_session(
            session
        )

        self.resolve_count += 1
        return session

    def require_registered(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        return self.resolve(
            session_id
        )

    def require_active(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        session = self.resolve(
            session_id
        )

        if getattr(
            session,
            "status",
            None,
        ) != "active":
            raise RuntimeError(
                "project session is not active"
            )

        self.active_count += 1
        return session

    def ready(
        self,
    ) -> bool:
        return (
            self.support.ready()
            and self.service.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "resolve_count": self.resolve_count,
            "active_count": self.active_count,
            "service": type(
                self.service
            ).__name__,
            "support": self.support.dump(),
        }


__all__ = [
    "ProjectSessionOperational",
]
