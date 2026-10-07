from __future__ import annotations

from backend.application.project.project_registration_contract import (
    ApplicationProjectRegistrationContract,
)
from backend.application.project.project_removal import (
    ApplicationProjectRemoval,
)
from backend.application.project.project_session_service_contract import (
    ApplicationProjectSessionServiceContract,
)


class ApplicationProjectRemovalFactory:
    """
    Construction boundary for application project removal.
    """

    VERSION = "1.1"

    def create(
        self,
        registration: ApplicationProjectRegistrationContract,
        session_service: ApplicationProjectSessionServiceContract,
    ) -> ApplicationProjectRemoval:
        if not self.ready():
            raise RuntimeError(
                "application project removal factory unavailable"
            )

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

        owner = ApplicationProjectRemoval(
            registration=registration,
            session_service=session_service,
        )

        if not owner.ready():
            raise RuntimeError(
                "application project removal unavailable"
            )

        return owner

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
    "ApplicationProjectRemovalFactory",
]
