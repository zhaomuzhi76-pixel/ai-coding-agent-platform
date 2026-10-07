from __future__ import annotations

from backend.workspace.project.session.contracts.project_session_registry_contract import (
    ProjectSessionRegistryContract,
)
from backend.workspace.project.session.lifecycle.project_session_lifecycle import (
    ProjectSessionLifecycle,
)


class ProjectSessionLifecycleFactory:
    """
    Project-session lifecycle construction boundary.

    Owns:
        - lifecycle coordinator construction
        - dependency validation
        - readiness validation

    Does not own:
        - registry construction
        - session construction
        - lifecycle state storage
        - workspace
        - runtime
        - external storage
        - execution
    """

    VERSION = "1.1"

    def create(
        self,
        registry: ProjectSessionRegistryContract,
    ) -> ProjectSessionLifecycle:
        if not self.ready():
            raise RuntimeError(
                "project session lifecycle "
                "factory unavailable"
            )

        if not isinstance(
            registry,
            ProjectSessionRegistryContract,
        ):
            raise TypeError(
                "registry must "
                "ProjectSessionRegistryContract"
            )

        if not registry.ready():
            raise RuntimeError(
                "project session registry unavailable"
            )

        lifecycle = ProjectSessionLifecycle(
            registry
        )

        if not lifecycle.ready():
            raise RuntimeError(
                "project session lifecycle "
                "unavailable"
            )

        return lifecycle

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
    "ProjectSessionLifecycleFactory",
]
