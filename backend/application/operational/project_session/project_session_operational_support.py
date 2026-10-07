from __future__ import annotations

from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.service.project_session_service_contract import (
    ProjectSessionServiceContract,
)


class ProjectSessionOperationalSupport:
    """
    Validation support for operational session admission.

    Ownership:
        - dependency validation
        - session-id validation
        - session-result validation
    """

    VERSION = "2.0"

    def validate_service(
        self,
        service: object,
    ) -> ProjectSessionServiceContract:
        if not isinstance(
            service,
            ProjectSessionServiceContract,
        ):
            raise TypeError(
                "service must implement "
                "ProjectSessionServiceContract"
            )

        if not service.ready():
            raise RuntimeError(
                "project session service not ready"
            )

        return service

    @staticmethod
    def validate_session_id(
        session_id: str,
    ) -> str:
        if not isinstance(
            session_id,
            str,
        ):
            raise TypeError(
                "session id must str"
            )

        value = session_id.strip()

        if not value:
            raise ValueError(
                "session id required"
            )

        return value

    @staticmethod
    def validate_session(
        session: object,
    ) -> ProjectSessionContract:
        if not isinstance(
            session,
            ProjectSessionContract,
        ):
            raise TypeError(
                "resolved session must implement "
                "ProjectSessionContract"
            )

        return session

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
    "ProjectSessionOperationalSupport",
]
