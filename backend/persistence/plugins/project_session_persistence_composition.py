from __future__ import annotations

from backend.persistence.plugins.project_session_persistence_plugin import (
    ProjectSessionPersistencePlugin,
)
from backend.persistence.plugins.project_session_persistence_runtime import (
    ProjectSessionPersistenceRuntime,
)


class ProjectSessionPersistenceComposition:
    VERSION = "1.0"

    def __init__(
        self,
        runtime: ProjectSessionPersistenceRuntime,
    ) -> None:
        self.runtime = runtime

    @property
    def plugin(
        self,
    ) -> ProjectSessionPersistencePlugin:
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
    "ProjectSessionPersistenceComposition",
]
