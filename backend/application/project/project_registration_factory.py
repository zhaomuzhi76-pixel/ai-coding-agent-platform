from __future__ import annotations

from backend.application.project.project_registration import (
    ApplicationProjectRegistration,
)
from backend.application.project.project_registration_contract import (
    ProjectModelFactoryProtocol,
)
from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)


class ApplicationProjectRegistrationFactory:
    """
    Construction boundary for application project registration.

    Concrete ProjectModelFactory is supplied by assembly root.
    """

    VERSION = "2.0"

    def create(
        self,
        project_registry: ProjectRegistryContract,
        project_factory: ProjectModelFactoryProtocol,
    ) -> ApplicationProjectRegistration:
        if not self.ready():
            raise RuntimeError(
                "application project registration factory unavailable"
            )

        if not isinstance(
            project_registry,
            ProjectRegistryContract,
        ):
            raise TypeError(
                "project registry contract required"
            )

        if not isinstance(
            project_factory,
            ProjectModelFactoryProtocol,
        ):
            raise TypeError(
                "project model factory contract required"
            )

        owner = ApplicationProjectRegistration(
            project_registry=project_registry,
            project_factory=project_factory,
        )

        if not owner.ready():
            raise RuntimeError(
                "application project registration unavailable"
            )

        return owner

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationProjectRegistrationFactory",
]
