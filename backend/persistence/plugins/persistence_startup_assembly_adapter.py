from __future__ import annotations

from typing import Any

from backend.assembly.startup_module import (
    ApplicationStartupModule,
)
from backend.persistence.plugins.project_persistence_composition import (
    ProjectPersistenceComposition,
)
from backend.persistence.plugins.project_registry_restore import (
    ProjectRegistryRestore,
)


class PersistenceStartupAssemblyAdapter(
    ApplicationStartupModule,
):
    VERSION = "1.1"
    NAME = "application.startup.persistence"

    def __init__(
        self,
        startup_module: ApplicationStartupModule,
        persistence: ProjectPersistenceComposition,
    ) -> None:
        if not isinstance(
            startup_module,
            ApplicationStartupModule,
        ):
            raise TypeError(
                "application startup module required"
            )

        if not isinstance(
            persistence,
            ProjectPersistenceComposition,
        ):
            raise TypeError(
                "project persistence composition required"
            )

        super().__init__(
            startup_module.startup
        )
        self.startup_module = startup_module
        self.persistence = persistence
        self._started = False
        self._restored = 0

    def build(
        self,
        context: Any = None,
    ) -> dict[str, Any]:
        if self._started:
            raise RuntimeError(
                "persistent startup already built"
            )

        self.persistence.start()

        try:
            result = self.startup_module.build(
                context
            )
            registry = getattr(
                self.startup,
                "project_registry",
                None,
            )

            if registry is None:
                raise RuntimeError(
                    "application project registry unavailable"
                )

            self._restored = (
                ProjectRegistryRestore(
                    persistence=self.persistence.repository,
                    registry=registry,
                ).restore()
            )
            self._started = True

            if not self.ready():
                raise RuntimeError(
                    "persistent application startup unavailable"
                )

            return dict(result)
        except Exception:
            self.persistence.stop()
            raise

    def ready(self) -> bool:
        return (
            self._started
            and self.persistence.ready()
            and self.startup_module.ready()
        )

    def shutdown(self) -> None:
        if not self._started:
            return

        try:
            self.startup_module.shutdown()
        finally:
            self.persistence.stop()
            self._started = False

    def dump(self) -> dict[str, object]:
        return {
            "name": self.NAME,
            "version": self.VERSION,
            "ready": self.ready(),
            "started": self._started,
            "restored_projects": self._restored,
            "persistence": self.persistence.dump(),
            "startup": self.startup_module.dump(),
        }


__all__ = [
    "PersistenceStartupAssemblyAdapter",
]
