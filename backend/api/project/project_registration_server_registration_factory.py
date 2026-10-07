from __future__ import annotations

from backend.api.project.project_registration_router_factory import (
    ProjectRegistrationRouterFactory,
)
from backend.api.project.project_registration_server_registration import (
    ProjectRegistrationServerRegistration,
)
from backend.api.project.project_registration_server_registration_support import (
    ProjectRegistrationServerRegistrationSupport,
)


class ProjectRegistrationServerRegistrationFactory:
    """
    Construction boundary for project-registration server registration.

    The Application project-removal dependency is resolved from the
    already assembled startup graph and is never constructed here.
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        router_factory: ProjectRegistrationRouterFactory | None = None,
        support: ProjectRegistrationServerRegistrationSupport
        | None = None,
    ) -> ProjectRegistrationServerRegistration:
        if not self.ready():
            raise RuntimeError(
                "project registration server registration "
                "factory unavailable"
            )

        registration = ProjectRegistrationServerRegistration(
            router_factory=(
                router_factory
                or ProjectRegistrationRouterFactory()
            ),
            support=(
                support
                or ProjectRegistrationServerRegistrationSupport()
            ),
        )

        if not registration.ready():
            raise RuntimeError(
                "project registration server registration "
                "unavailable"
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
    "ProjectRegistrationServerRegistrationFactory",
]
