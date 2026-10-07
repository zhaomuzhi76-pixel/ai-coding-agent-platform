from __future__ import annotations

from backend.assembly.startup_module import (
    ApplicationStartupModule,
)
from backend.persistence.plugins.project_session_persistence_composition import (
    ProjectSessionPersistenceComposition,
)
from backend.persistence.plugins.project_session_persistence_composition_factory import (
    ProjectSessionPersistenceCompositionFactory,
)
from backend.persistence.plugins.project_session_persistence_adapter import (
    ProjectSessionPersistenceAdapter,
)
from backend.persistence.plugins.project_session_registry_restore import (
    ProjectSessionRegistryRestore,
)


class ProjectSessionPersistenceStartupFactory:
    VERSION = "1.0"

    def create(
        self,
        startup: object,
    ) -> ApplicationStartupModule:
        startup_module = startup
        if not isinstance(
            startup_module,
            ApplicationStartupModule,
        ):
            raise TypeError(
                "application startup module required"
            )

        application_startup = startup_module.startup
        composition = (
            application_startup.project_session_composition
        )
        assembly = composition.current()

        persistence = (
            assembly.get("session_persistence")
        )
        session_adapter = (
            assembly.get("session_service")
        )

        if not isinstance(
            persistence,
            ProjectSessionPersistenceComposition,
        ):
            raise RuntimeError(
                "project session persistence composition unavailable"
            )

        if not isinstance(
            session_adapter,
            ProjectSessionPersistenceAdapter,
        ):
            raise RuntimeError(
                "project session persistence adapter unavailable"
            )

        return ProjectSessionPersistenceStartupModule(
            startup_module=startup_module,
            persistence=persistence,
            adapter=session_adapter,
        )


class ProjectSessionPersistenceStartupModule(
    ApplicationStartupModule,
):
    VERSION = "1.0"
    NAME = "application.startup.project-session-persistence"

    def __init__(
        self,
        *,
        startup_module: ApplicationStartupModule,
        persistence: ProjectSessionPersistenceComposition,
        adapter: ProjectSessionPersistenceAdapter,
    ) -> None:
        super().__init__(
            startup_module.startup
        )
        self.startup_module = startup_module
        self.persistence = persistence
        self.adapter = adapter
        self._started = False
        self._restored = 0

    def build(
        self,
        context=None,
    ):
        self.persistence.start()

        try:
            result = self.startup_module.build(
                context
            )

            startup = self.startup_module.startup
            composition = (
                startup.project_session_composition
            )
            assembly = composition.current()

            registry = assembly[
                "project_registry"
            ]
            sessions = assembly[
                "session_registry"
            ]

            self._restored = (
                ProjectSessionRegistryRestore(
                    persistence=self.persistence.repository,
                    project_registry=registry,
                    session_registry=sessions,
                ).restore()
            )

            self._started = True

            if not self.ready():
                raise RuntimeError(
                    "project session persistence "
                    "startup unavailable"
                )

            return dict(result)

        except Exception:
            self.persistence.stop()
            raise

    def shutdown(self) -> None:
        if not self._started:
            return

        try:
            self.startup_module.shutdown()
        finally:
            self.persistence.stop()
            self._started = False

    def ready(self) -> bool:
        return (
            self._started
            and self.persistence.ready()
            and self.startup_module.ready()
            and self.adapter.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.NAME,
            "version": self.VERSION,
            "ready": self.ready(),
            "started": self._started,
            "restored_sessions": self._restored,
            "persistence": self.persistence.dump(),
        }


__all__ = [
    "ProjectSessionPersistenceStartupFactory",
    "ProjectSessionPersistenceStartupModule",
]
