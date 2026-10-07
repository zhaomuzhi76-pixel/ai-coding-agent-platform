from __future__ import annotations

from backend.api.project_session.project_session_api_factory import (
    ProjectSessionAPIFactory,
)
from backend.api.project_session.server.project_session_api_server_registration import (
    ProjectSessionAPIServerRegistration,
)


class ProjectSessionAPIServerRegistrationFactory:
    """
    Construction boundary for project-session API server registration.

    Application dependencies are supplied by the startup graph at
    registration time. This factory constructs only the API registrar.
    """

    VERSION = "3.0"

    def create(
        self,
        api_factory: ProjectSessionAPIFactory | None = None,
    ) -> ProjectSessionAPIServerRegistration:
        if not self.ready():
            raise RuntimeError(
                "project session api server "
                "registration factory unavailable"
            )

        registration = (
            ProjectSessionAPIServerRegistration(
                api_factory=api_factory,
            )
        )

        if not registration.ready():
            raise RuntimeError(
                "project session api server "
                "registration unavailable"
            )

        return registration

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
    "ProjectSessionAPIServerRegistrationFactory",
]
