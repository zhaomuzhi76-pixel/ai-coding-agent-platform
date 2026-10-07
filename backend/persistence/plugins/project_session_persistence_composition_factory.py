from __future__ import annotations

from backend.persistence.plugins.project_session_persistence_composition import (
    ProjectSessionPersistenceComposition,
)
from backend.persistence.plugins.project_session_persistence_plugin import (
    ProjectSessionPersistencePlugin,
)
from backend.persistence.plugins.project_session_persistence_runtime import (
    ProjectSessionPersistenceRuntime,
)


class ProjectSessionPersistenceCompositionFactory:
    VERSION = "1.0"

    def create(
        self,
    ) -> ProjectSessionPersistenceComposition:
        plugin = ProjectSessionPersistencePlugin()
        runtime = ProjectSessionPersistenceRuntime(
            plugin
        )
        return ProjectSessionPersistenceComposition(
            runtime
        )

    def ready(self) -> bool:
        return True


__all__ = [
    "ProjectSessionPersistenceCompositionFactory",
]
