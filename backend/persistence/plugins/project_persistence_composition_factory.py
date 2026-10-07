from __future__ import annotations

from backend.persistence.plugins.project_persistence_composition import (
    ProjectPersistenceComposition,
)
from backend.persistence.plugins.project_persistence_plugin import (
    ProjectPersistencePlugin,
)
from backend.persistence.plugins.project_persistence_runtime import (
    ProjectPersistenceRuntime,
)


class ProjectPersistenceCompositionFactory:
    VERSION = "1.0"

    def create(self) -> ProjectPersistenceComposition:
        plugin = ProjectPersistencePlugin()
        runtime = ProjectPersistenceRuntime(
            plugin
        )
        return ProjectPersistenceComposition(
            runtime
        )

    def ready(self) -> bool:
        return True


__all__ = [
    "ProjectPersistenceCompositionFactory",
]
