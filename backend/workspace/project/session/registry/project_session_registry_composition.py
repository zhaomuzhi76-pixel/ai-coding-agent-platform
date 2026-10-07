from __future__ import annotations

from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)
from backend.workspace.project.registry.project_registry_factory import (
    ProjectRegistryFactory,
)
from backend.workspace.project.session.registry.project_session_registry import (
    ProjectSessionRegistry,
)
from backend.workspace.project.session.registry.project_session_registry_binding import (
    ProjectSessionRegistryBinding,
)
from backend.workspace.project.session.registry.project_session_registry_factory import (
    ProjectSessionRegistryFactory,
)


class ProjectSessionRegistryComposition:
    """
    Registry-layer construction and binding boundary.

    Owns:
        - project registry acquisition
        - session registry construction
        - registry binding construction

    Does not own:
        - project construction
        - session construction
        - runtime execution
        - workspace
        - persistence
    """

    VERSION = "1.0"

    def __init__(
        self,
        project_registry_factory: ProjectRegistryFactory | None = None,
        session_registry_factory: ProjectSessionRegistryFactory | None = None,
    ) -> None:
        self.project_registry_factory = (
            project_registry_factory
            or ProjectRegistryFactory()
        )
        self.session_registry_factory = (
            session_registry_factory
            or ProjectSessionRegistryFactory()
        )

    def create(
        self,
        project_registry: ProjectRegistryContract | None = None,
    ) -> ProjectSessionRegistryBinding:
        if not self.ready():
            raise RuntimeError(
                "project session registry composition unavailable"
            )

        registry = (
            project_registry
            if project_registry is not None
            else self.project_registry_factory.create()
        )

        session_registry = (
            self.session_registry_factory.create()
        )

        binding = ProjectSessionRegistryBinding(
            project_registry=registry,
            session_registry=session_registry,
        )

        if not binding.ready():
            raise RuntimeError(
                "project session registry binding unavailable"
            )

        return binding

    def create_registry(
        self,
    ) -> ProjectSessionRegistry:
        if not self.session_registry_factory.ready():
            raise RuntimeError(
                "project session registry factory unavailable"
            )

        return self.session_registry_factory.create()

    def ready(
        self,
    ) -> bool:
        return (
            self.project_registry_factory.ready()
            and self.session_registry_factory.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "project_registry_factory": (
                self.project_registry_factory.dump()
            ),
            "session_registry_factory": (
                self.session_registry_factory.dump()
            ),
        }


__all__ = [
    "ProjectSessionRegistryComposition",
]
