from __future__ import annotations

from backend.persistence.contracts.project_session_persistence import (
    ProjectSessionPersistenceContract,
)
from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)
from backend.workspace.project.session.contracts.project_session_registry_contract import (
    ProjectSessionRegistryContract,
)
from backend.workspace.project.session.registry.project_session_registry_support import (
    ProjectSessionRegistrySupport,
)


class ProjectSessionRegistryRestore:
    VERSION = "1.0"

    def __init__(
        self,
        persistence: ProjectSessionPersistenceContract,
        project_registry: ProjectRegistryContract,
        session_registry: ProjectSessionRegistryContract,
        support: ProjectSessionRegistrySupport | None = None,
    ) -> None:
        self.persistence = persistence
        self.project_registry = project_registry
        self.session_registry = session_registry
        self.support = (
            support
            or ProjectSessionRegistrySupport()
        )

    def restore(self) -> int:
        restored = 0

        sessions = self._load()

        for session in sessions:
            if not self.project_registry.contains(
                session.project_id
            ):
                continue

            if self.session_registry.contains(
                session.session_id
            ):
                continue

            self.support.validate_session(session)
            self.session_registry.register(session)
            restored += 1

        return restored

    def _load(self):
        from backend.persistence.plugins.persistence_sync_bridge import (
            PersistenceSyncBridge,
        )

        return PersistenceSyncBridge().run(
            self.persistence.list()
        )

    def ready(self) -> bool:
        return (
            self.persistence.ready()
            and self.project_registry.ready()
            and self.session_registry.ready()
            and self.support.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionRegistryRestore",
]
