from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.persistence.contracts.project_persistence import (
    ProjectPersistenceContract,
)
from backend.persistence.plugins.persistence_sync_bridge import (
    PersistenceSyncBridge,
)
from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)


@runtime_checkable
class PersistenceProjectRegistrationProtocol(Protocol):
    def register(
        self,
        name: str,
        root_path: str,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> object:
        ...

    def get(self, project_id: str) -> object:
        ...

    def contains(self, project_id: str) -> bool:
        ...

    def remove(self, project_id: str) -> object:
        ...

    def ready(self) -> bool:
        ...


@runtime_checkable
class PersistenceProjectFactoryProtocol(Protocol):
    def ready(self) -> bool:
        ...


class ProjectRegistrationPersistenceAdapter:
    VERSION = "1.1"

    def __init__(
        self,
        registration: PersistenceProjectRegistrationProtocol,
        persistence: ProjectPersistenceContract,
        project_registry: ProjectRegistryContract,
        project_factory: PersistenceProjectFactoryProtocol,
        bridge: PersistenceSyncBridge | None = None,
    ) -> None:
        if not isinstance(
            registration,
            PersistenceProjectRegistrationProtocol,
        ):
            raise TypeError(
                "project registration protocol required"
            )
        if not persistence.ready():
            raise RuntimeError(
                "project persistence not ready"
            )
        if not isinstance(
            project_registry,
            ProjectRegistryContract,
        ):
            raise TypeError(
                "project registry contract required"
            )
        if not project_registry.ready():
            raise RuntimeError(
                "project registry not ready"
            )
        if not isinstance(
            project_factory,
            PersistenceProjectFactoryProtocol,
        ):
            raise TypeError(
                "project factory protocol required"
            )
        if not project_factory.ready():
            raise RuntimeError(
                "project factory not ready"
            )

        self.registration = registration
        self.persistence = persistence
        self.project_registry = project_registry
        self.project_factory = project_factory
        self.bridge = bridge or PersistenceSyncBridge()

    def register(
        self,
        name: str,
        root_path: str,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> object:
        project = self.registration.register(
            name=name,
            root_path=root_path,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        try:
            self.bridge.run(
                self.persistence.save(project)
            )
        except Exception:
            self.registration.remove(
                project.project_id
            )
            raise

        return project

    def get(
        self,
        project_id: str,
    ) -> object:
        if self.registration.contains(project_id):
            return self.registration.get(project_id)

        project = self.bridge.run(
            self.persistence.get(project_id)
        )
        if project is None:
            raise KeyError(
                f"project not registered: {project_id}"
            )

        if not self.project_registry.contains(
            project.project_id
        ):
            self.project_registry.register(project)

        return project

    def contains(
        self,
        project_id: str,
    ) -> bool:
        return (
            self.registration.contains(project_id)
            or self.bridge.run(
                self.persistence.get(project_id)
            )
            is not None
        )

    def remove(
        self,
        project_id: str,
    ) -> object:
        project = self.registration.get(project_id)
        removed = self.registration.remove(project_id)

        try:
            deleted = self.bridge.run(
                self.persistence.delete(project_id)
            )
            if not deleted:
                self.project_registry.register(project)
                raise RuntimeError(
                    "project persistence delete failed"
                )
        except Exception:
            if not self.project_registry.contains(
                project.project_id
            ):
                self.project_registry.register(project)
            raise

        return removed

    def ready(self) -> bool:
        return (
            self.registration.ready()
            and self.persistence.ready()
            and self.project_registry.ready()
            and self.project_factory.ready()
            and self.bridge.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registration": type(
                self.registration
            ).__name__,
            "persistence": type(
                self.persistence
            ).__name__,
            "project_registry": type(
                self.project_registry
            ).__name__,
        }


__all__ = [
    "PersistenceProjectRegistrationProtocol",
    "PersistenceProjectFactoryProtocol",
    "ProjectRegistrationPersistenceAdapter",
]
