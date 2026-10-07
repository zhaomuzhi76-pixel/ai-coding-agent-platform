from __future__ import annotations

from backend.api.project.project_registration_api import (
    ProjectRegistrationAPI,
)
from backend.api.project.project_registration_router import (
    ProjectRegistrationRouter,
)


class ProjectRegistrationRouterFactory:
    """
    Construction boundary for project registration Router.

    Owns:
        - Router construction
        - Router readiness validation

    Does not own:
        - API implementation
        - project registry construction
        - project business logic
        - server registration
        - application lifecycle
    """

    VERSION = "1.0"

    def create(
        self,
        api: ProjectRegistrationAPI,
    ) -> ProjectRegistrationRouter:
        if not self.ready():
            raise RuntimeError(
                "project registration router "
                "factory unavailable"
            )

        router = ProjectRegistrationRouter(
            api
        )

        if not router.ready():
            raise RuntimeError(
                "project registration router unavailable"
            )

        return router

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
    "ProjectRegistrationRouterFactory",
]
