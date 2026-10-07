from __future__ import annotations

from backend.persistence.contracts.project_persistence import (
    ProjectPersistenceContract,
)
from backend.persistence.plugins.persistence_sync_bridge import (
    PersistenceSyncBridge,
)
from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)


class ProjectRegistryRestore:
    VERSION = "1.0"

    def __init__(
        self,
        persistence: ProjectPersistenceContract,
        registry: ProjectRegistryContract,
        bridge: PersistenceSyncBridge | None = None,
    ) -> None:
        self.persistence = persistence
        self.registry = registry
        self.bridge = bridge or PersistenceSyncBridge()

        if not persistence.ready():
            raise RuntimeError(
                "project persistence not ready"
            )
        if not registry.ready():
            raise RuntimeError(
                "project registry not ready"
            )

    def restore(self) -> int:
        projects = self.bridge.run(
            self.persistence.list()
        )

        restored = 0

        for project in projects:
            if self.registry.contains(
                project.project_id
            ):
                continue

            self.registry.register(project)
            restored += 1

        return restored

    def ready(self) -> bool:
        return (
            self.persistence.ready()
            and self.registry.ready()
            and self.bridge.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registry": type(
                self.registry
            ).__name__,
            "persistence": type(
                self.persistence
            ).__name__,
        }


__all__ = [
    "ProjectRegistryRestore",
]
