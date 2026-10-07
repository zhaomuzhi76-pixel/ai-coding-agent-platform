from __future__ import annotations

from backend.persistence.plugins.persistence_plugin_context import (
    PersistencePluginContext,
)
from backend.persistence.plugins.persistence_plugin_runtime import (
    PersistencePluginRuntime,
)
from backend.persistence.plugins.project_persistence_plugin import (
    ProjectPersistencePlugin,
)


class ProjectPersistenceRuntime:
    NAME = "project-persistence"
    VERSION = "1.0"

    def __init__(
        self,
        plugin: ProjectPersistencePlugin,
    ) -> None:
        if not isinstance(
            plugin,
            ProjectPersistencePlugin,
        ):
            raise TypeError(
                "project persistence plugin required"
            )

        self.plugin = plugin
        self.context = PersistencePluginContext(
            plugin_name=self.NAME,
        )
        self.runtime = PersistencePluginRuntime(
            plugin=plugin,
            context=self.context,
        )

    def start(self) -> None:
        self.runtime.initialize()
        self.runtime.activate()

    def stop(self) -> None:
        self.runtime.stop()

    def ready(self) -> bool:
        return self.runtime.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "state": self.runtime.state().value,
            "plugin": self.plugin.dump(),
        }


__all__ = ["ProjectPersistenceRuntime"]
