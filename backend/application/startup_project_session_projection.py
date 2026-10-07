from __future__ import annotations

from typing import Any

from backend.application.composition.project_session import (
    ApplicationProjectSessionComposition,
)
from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)


class ApplicationStartupProjectSessionProjection:
    """
    Project/session assembly projection for Application startup.

    Construction has already been completed by Assembly.
    This class only validates and projects the result.
    """

    VERSION = "2.0"

    def project(
        self,
        composition: ApplicationProjectSessionComposition,
        project_registry: ProjectRegistryContract,
        context: dict[str, Any],
    ) -> dict[str, object]:
        if not isinstance(
            composition,
            ApplicationProjectSessionComposition,
        ):
            raise TypeError(
                "project-session composition invalid"
            )

        if not isinstance(
            project_registry,
            ProjectRegistryContract,
        ):
            raise TypeError(
                "project registry invalid"
            )

        if not composition.ready():
            raise RuntimeError(
                "project-session composition not ready"
            )

        assembled = composition.create()
        assembled_registry = assembled.get(
            "project_registry"
        )

        if assembled_registry is not project_registry:
            raise RuntimeError(
                "project registry projection mismatch"
            )

        service = assembled.get(
            "session_service"
        )
        if service is None:
            raise RuntimeError(
                "project-session service unavailable"
            )

        context["project_session_composition"] = (
            composition
        )
        context["project_session_assembly"] = dict(
            assembled
        )
        context["project_session_service"] = service

        return dict(assembled)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationStartupProjectSessionProjection",
]
