from __future__ import annotations

from backend.application.project_session.project_session_adapter import (
    ProjectSessionApplicationAdapter,
)
from backend.workspace.project.session.service.project_session_service_contract import (
    ProjectSessionServiceContract,
)


class ProjectSessionApplicationAdapterFactory:
    """
    Application adapter construction boundary.

    Owns:
        - adapter construction
        - dependency validation
        - readiness validation

    Does not own:
        - project construction
        - session construction
        - registry construction
        - lifecycle orchestration
        - runtime construction
        - workspace construction
        - persistence
    """

    VERSION = "1.0"

    def create(
        self,
        service: ProjectSessionServiceContract,
    ) -> ProjectSessionApplicationAdapter:
        if not self.ready():
            raise RuntimeError(
                "project session adapter factory unavailable"
            )

        if not isinstance(
            service,
            ProjectSessionServiceContract,
        ):
            raise TypeError(
                "service must "
                "ProjectSessionServiceContract"
            )

        adapter = ProjectSessionApplicationAdapter(
            service
        )

        if not adapter.ready():
            raise RuntimeError(
                "project session application adapter unavailable"
            )

        return adapter

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionApplicationAdapterFactory",
]
