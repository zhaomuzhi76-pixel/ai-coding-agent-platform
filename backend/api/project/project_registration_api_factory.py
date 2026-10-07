from __future__ import annotations

from backend.api.project.project_registration_api import (
    ProjectRegistrationAPI,
)
from backend.api.project.project_registration_api_support import (
    ProjectRegistrationAPISupport,
)
from backend.application.project.project_registration_contract import (
    ApplicationProjectRegistrationContract,
)
from backend.application.project.project_removal_contract import (
    ApplicationProjectRemovalContract,
)


class ProjectRegistrationAPIFactory:
    """
    Sole construction owner for ProjectRegistrationAPI.

    Owns:
        - project-registration API construction
        - API dependency validation

    Does not own:
        - project construction
        - project removal construction
        - route construction
        - route registration
        - application lifecycle
    """

    VERSION = "2.0"

    def create(
        self,
        registration: ApplicationProjectRegistrationContract,
        removal: ApplicationProjectRemovalContract,
        support: ProjectRegistrationAPISupport | None = None,
    ) -> ProjectRegistrationAPI:
        if not self.ready():
            raise RuntimeError(
                "project registration API factory unavailable"
            )

        self._validate_ready(
            registration,
            "project registration",
        )
        self._validate_ready(
            removal,
            "project removal",
        )

        if (
            removal.registration
            is not registration
        ):
            raise ValueError(
                "project removal must use the same "
                "project registration owner"
            )

        active_support = (
            support
            or ProjectRegistrationAPISupport()
        )

        if not active_support.ready():
            raise RuntimeError(
                "project registration API support unavailable"
            )

        api = ProjectRegistrationAPI(
            registration=registration,
            removal=removal,
            support=active_support,
        )

        if not api.ready():
            raise RuntimeError(
                "project registration API unavailable"
            )

        return api

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

    @staticmethod
    def _validate_ready(
        component: object,
        name: str,
    ) -> None:
        if component is None:
            raise ValueError(
                f"{name} required"
            )

        ready = getattr(
            component,
            "ready",
            None,
        )

        if not callable(ready):
            raise TypeError(
                f"{name} must expose ready()"
            )

        if not ready():
            raise RuntimeError(
                f"{name} not ready"
            )


__all__ = [
    "ProjectRegistrationAPIFactory",
]
