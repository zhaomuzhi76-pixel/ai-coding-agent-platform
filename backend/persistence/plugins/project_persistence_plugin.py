from __future__ import annotations

from typing import Any

from backend.persistence.mongodb.project_persistence import (
    MongoProjectPersistence,
)
from backend.persistence.plugins.persistence_plugin_contract import (
    PersistencePluginContract,
)
from backend.storage.mongodb_client import MongoDBClient
from backend.storage.mongodb_config import MongoDBConfig


class ProjectPersistencePlugin(PersistencePluginContract):
    NAME = "project-persistence"
    VERSION = "1.0"

    def __init__(
        self,
        client: MongoDBClient | None = None,
    ) -> None:
        self.client = (
            client
            or MongoDBClient(
                MongoDBConfig()
            )
        )
        self.repository = MongoProjectPersistence(
            self.client
        )
        self._initialized = False
        self._active = False

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def version(self) -> str:
        return self.VERSION

    def initialize(self) -> None:
        if not self.client.ping():
            raise RuntimeError(
                "MongoDB unavailable"
            )
        self._initialized = True

    def activate(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "project persistence must initialize first"
            )
        self._active = True

    def stop(self) -> None:
        self._active = False

    def execute(
        self,
        *,
        context: Any,
        payload: dict[str, Any],
    ) -> Any:
        raise RuntimeError(
            "project persistence plugin does not expose "
            "generic execution; use ProjectRegistrationPersistenceAdapter"
        )

    def ready(self) -> bool:
        return (
            self.repository.ready()
            and self.client.ping()
            and self._active
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "initialized": self._initialized,
            "active": self._active,
            "repository": self.repository.dump(),
        }


__all__ = ["ProjectPersistencePlugin"]
