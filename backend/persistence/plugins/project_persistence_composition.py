from __future__ import annotations

from backend.persistence.plugins.project_persistence_plugin import (
    ProjectPersistencePlugin,
)
from backend.persistence.plugins.project_persistence_runtime import (
    ProjectPersistenceRuntime,
)


class ProjectPersistenceComposition:
    VERSION = "1.0"

    def __init__(
        self,
        runtime: ProjectPersistenceRuntime,
    ) -> None:
        self.runtime = runtime

    @property
    def plugin(
        self,
    ) -> ProjectPersistencePlugin:
        return self.runtime.plugin

    @property
    def repository(self):
        return self.plugin.repository

    def start(self) -> None:
        self.runtime.start()

    def stop(self) -> None:
        self.runtime.stop()

    def ready(self) -> bool:
        return self.runtime.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "runtime": self.runtime.dump(),
        }


__all__ = [
    "ProjectPersistenceComposition",
]
