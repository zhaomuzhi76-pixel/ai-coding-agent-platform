from __future__ import annotations

from backend.workspace.workspace_path import (
    normalize_only,
)
from backend.api.project.project_registration_api_contract import (
    ProjectRegistrationAPIContract,
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
from backend.application.project.project_result_contract import (
    ApplicationProjectResultContract,
)


class ProjectRegistrationAPI(
    ProjectRegistrationAPIContract,
):
    """
    Application-facing project registration API facade.

    Owns:
        - project registration delegation
        - project lookup delegation
        - project removal delegation

    Does not own:
        - project registry construction
        - registry storage
        - project model construction
        - project removal policy
        - session lifecycle
        - transport route registration
    """

    VERSION = "2.0"

    def __init__(
        self,
        registration: ApplicationProjectRegistrationContract,
        removal: ApplicationProjectRemovalContract,
        support: ProjectRegistrationAPISupport | None = None,
    ) -> None:
        if not isinstance(
            registration,
            ApplicationProjectRegistrationContract,
        ):
            raise TypeError(
                "registration must implement "
                "ApplicationProjectRegistrationContract"
            )

        if not registration.ready():
            raise RuntimeError(
                "application project registration not ready"
            )

        if not isinstance(
            removal,
            ApplicationProjectRemovalContract,
        ):
            raise TypeError(
                "removal must implement "
                "ApplicationProjectRemovalContract"
            )

        if not removal.ready():
            raise RuntimeError(
                "application project removal not ready"
            )

        if removal.registration is not registration:
            raise ValueError(
                "project removal must use the same "
                "project registration owner"
            )

        self.registration = registration
        self.removal = removal
        self.support = (
            support
            or ProjectRegistrationAPISupport()
        )

        if not self.support.ready():
            raise RuntimeError(
                "project registration API support not ready"
            )

        self.request_count = 0
        self.register_count = 0
        self.remove_count = 0

    def register(
        self,
        payload: dict[str, object],
    ) -> ApplicationProjectResultContract:
        data = self.support.payload(payload)

        project = self.registration.register(
            name=self.support.required(
                data.get("name"),
                "name",
            ),
            root_path=normalize_only(
                self.support.required(
                    data.get("root_path"),
                    "root_path",
                )
            ),
            project_id=self.support.optional(
                data.get("project_id")
            ),
            workspace_id=self.support.optional(
                data.get("workspace_id")
            ),
        )

        project = self.support.require_project(
            project
        )

        self.request_count += 1
        self.register_count += 1
        return project

    def get(
        self,
        project_id: str,
    ) -> ApplicationProjectResultContract:
        project = self.registration.get(
            self.support.required(
                project_id,
                "project_id",
            )
        )

        project = self.support.require_project(
            project
        )

        self.request_count += 1
        return project

    def remove(
        self,
        project_id: str,
    ) -> ApplicationProjectResultContract:
        project = self.removal.remove(
            self.support.required(
                project_id,
                "project_id",
            )
        )

        project = self.support.require_project(
            project
        )

        self.request_count += 1
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
                self.removal,
                ApplicationProjectRemovalContract,
            )
            and self.removal.ready()
            and self.removal.registration
            is self.registration
            and self.support.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "request_count": self.request_count,
            "register_count": self.register_count,
            "remove_count": self.remove_count,
            "remove_count_owner": (
                self.removal.remove_count
            ),
            "rejected_remove_count": (
                self.removal.rejected_count
            ),
            "registration": type(
                self.registration
            ).__name__,
            "removal": type(
                self.removal
            ).__name__,
            "support": self.support.dump(),
        }


__all__ = [
    "ProjectRegistrationAPI",
]
