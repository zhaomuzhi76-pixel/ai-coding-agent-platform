from __future__ import annotations

from backend.workspace.project.registry.project_registry import (
    ProjectRegistry,
)


class ProjectRegistryFactory:
    """
    Project registry construction boundary.

    Owns:
        - ProjectRegistry construction
        - registry readiness validation

    Does not own:
        - project creation
        - workspace construction
        - persistence
        - project execution
        - agent orchestration
    """

    VERSION = "1.0"

    def create(
        self,
    ) -> ProjectRegistry:
        if not self.ready():
            raise RuntimeError(
                "project registry factory unavailable"
            )

        registry = ProjectRegistry()

        if not registry.ready():
            raise RuntimeError(
                "project registry unavailable"
            )

        return registry

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
    "ProjectRegistryFactory",
]
