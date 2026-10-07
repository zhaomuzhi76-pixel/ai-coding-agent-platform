from __future__ import annotations

from backend.application.project.project_registration_contract import (
    ApplicationProjectRegistrationContract,
)
from backend.application.project.project_session_service_contract import (
    ApplicationProjectSessionServiceContract,
)
from backend.application.project.project_result_contract import (
    ApplicationProjectResultContract,
)


class ApplicationProjectRemoval(
    ApplicationProjectResultContract,
):
    """
    Application project-removal coordination boundary.

    Owns:
        - project-removal admission
        - session-dependency protection
        - delegation to project registration owner

    Does not own:
        - project registry storage
        - project construction
        - session construction
        - session lifecycle implementation
        - transport
        - implicit cascading deletion
    """

    VERSION = "1.0"

    def __init__(
        self,
        registration: ApplicationProjectRegistrationContract,
        session_service: ApplicationProjectSessionServiceContract,
    ) -> None:
        if not isinstance(
            registration,
            ApplicationProjectRegistrationContract,
        ):
            raise TypeError(
                "registration must implement "
                "ApplicationProjectRegistrationContract"
            )

        if not isinstance(
            session_service,
            ApplicationProjectSessionServiceContract,
        ):
            raise TypeError(
                "session service must implement "
                "ApplicationProjectSessionServiceContract"
            )

        if not registration.ready():
            raise RuntimeError(
                "application project registration not ready"
            )

        if not session_service.ready():
            raise RuntimeError(
                "project session service not ready"
            )

        self.registration = registration
        self.session_service = session_service
        self.remove_count = 0
        self.rejected_count = 0

    def remove(
        self,
        project_id: str,
    ):
        sessions = self.session_service.project_sessions(
            project_id
        )

        if sessions:
            self.rejected_count += 1
            raise RuntimeError(
                "project cannot be removed while sessions exist"
            )

        project = self.registration.remove(
            project_id
        )

        if not isinstance(
            project,
            ApplicationProjectResultContract,
        ):
            raise TypeError(
                "project registration returned invalid "
                "application project result"
            )

        self.remove_count += 1
        return project

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.registration,
                ApplicationProjectRegistrationContract,
            )
            and self.registration.ready()
            and isinstance(
                self.session_service,
                ApplicationProjectSessionServiceContract,
            )
            and self.session_service.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "remove_count": self.remove_count,
            "rejected_count": self.rejected_count,
            "registration": type(
                self.registration
            ).__name__,
            "session_service": type(
                self.session_service
            ).__name__,
        }


__all__ = [
    "ApplicationProjectRemoval",
]
