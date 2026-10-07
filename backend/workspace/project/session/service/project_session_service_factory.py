from __future__ import annotations

from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)
from backend.workspace.project.session.contracts.project_session_registry_contract import (
    ProjectSessionRegistryContract,
)
from backend.workspace.project.session.lifecycle.project_session_lifecycle_contract import (
    ProjectSessionLifecycleContract,
)
from backend.workspace.project.session.project_session_model_factory import (
    ProjectSessionModelFactory,
)
from backend.workspace.project.session.service.project_session_service import (
    ProjectSessionService,
)
from backend.workspace.project.session.service.project_session_service_support import (
    ProjectSessionServiceSupport,
)


class ProjectSessionServiceFactory:
    """
    Project-session service construction boundary.

    Owns:
        - dependency validation
        - service construction

    Does not own:
        - project construction
        - session construction
        - registry construction
        - lifecycle state
        - runtime
        - workspace
        - persistence
    """

    VERSION = "1.2"

    def create(
        self,
        project_registry: ProjectRegistryContract,
        session_registry: ProjectSessionRegistryContract,
        lifecycle: ProjectSessionLifecycleContract,
        session_factory: ProjectSessionModelFactory,
    ) -> ProjectSessionService:
        if not self.ready():
            raise RuntimeError(
                "project session service "
                "factory unavailable"
            )

        service = ProjectSessionService(
            project_registry=project_registry,
            session_registry=session_registry,
            lifecycle=lifecycle,
            session_factory=session_factory,
            support=ProjectSessionServiceSupport(),
        )

        if not service.ready():
            raise RuntimeError(
                "project session service unavailable"
            )

        return service

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
    "ProjectSessionServiceFactory",
]
