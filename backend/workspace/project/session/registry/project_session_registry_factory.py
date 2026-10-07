from __future__ import annotations

from backend.workspace.project.session.registry.project_session_registry import (
    ProjectSessionRegistry,
)


class ProjectSessionRegistryFactory:
    """
    Construction boundary for project-session registry.

    Owns:
        - registry construction
        - construction readiness

    Does not own:
        - session construction
        - project construction
        - runtime construction
        - persistence
        - lifecycle orchestration
    """

    VERSION = "1.0"

    def create(
        self,
    ) -> ProjectSessionRegistry:
        if not self.ready():
            raise RuntimeError(
                "project session registry factory unavailable"
            )

        registry = ProjectSessionRegistry()

        if not registry.ready():
            raise RuntimeError(
                "project session registry unavailable"
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
    "ProjectSessionRegistryFactory",
]
