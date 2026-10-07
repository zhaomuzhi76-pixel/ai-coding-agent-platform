from __future__ import annotations

from typing import Any

from backend.persistence.plugins.project_persistence_composition import (
    ProjectPersistenceComposition,
)
from backend.persistence.plugins.project_registry_restore import (
    ProjectRegistryRestore,
)


class PersistenceStartupModule:
    VERSION = "1.0"

    def __init__(
        self,
        startup_module: Any,
        persistence: ProjectPersistenceComposition,
    ) -> None:
        if startup_module is None:
            raise ValueError(
                "startup module required"
            )

        for method in (
            "start",
            "stop",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(
                    startup_module,
                    method,
                    None,
                )
            ):
                raise TypeError(
                    f"startup module must expose {method}()"
                )

        if not isinstance(
            persistence,
            ProjectPersistenceComposition,
        ):
            raise TypeError(
                "project persistence composition required"
            )

        self.startup_module = startup_module
        self.persistence = persistence
        self._started = False
        self._restored = 0

    @property
    def name(self) -> str:
        return "application.startup.persistence"

    @property
    def version(self) -> str:
        return self.VERSION

    def start(self) -> None:
        if self._started:
            raise RuntimeError(
                "persistence startup already started"
            )

        self.persistence.start()

        try:
            self.startup_module.start()

            startup = getattr(
                self.startup_module,
                "startup",
                None,
            )
            registry = getattr(
                startup,
                "project_registry",
                None,
            )

            if registry is None:
                raise RuntimeError(
                    "application project registry unavailable"
                )

            restore = ProjectRegistryRestore(
                persistence=self.persistence.repository,
                registry=registry,
            )
            self._restored = restore.restore()

            if not self.startup_module.ready():
                raise RuntimeError(
                    "application startup unavailable"
                )

            self._started = True

        except Exception:
            self.persistence.stop()
            raise

    def stop(self) -> None:
        if not self._started:
            return

        try:
            self.persistence.stop()
        finally:
            self.startup_module.stop()
            self._started = False

    def ready(self) -> bool:
        return (
            self._started
            and self.persistence.ready()
            and self.startup_module.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "started": self._started,
            "restored_projects": self._restored,
            "persistence": self.persistence.dump(),
            "startup": self.startup_module.dump(),
        }


__all__ = [
    "PersistenceStartupModule",
]
