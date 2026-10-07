from __future__ import annotations

from backend.assembly.startup_module import (
    ApplicationStartupModule,
)
from backend.persistence.plugins.persistence_startup_assembly_adapter import (
    PersistenceStartupAssemblyAdapter,
)
from backend.persistence.plugins.project_persistence_composition_factory import (
    ProjectPersistenceCompositionFactory,
)
from backend.persistence.plugins.project_registration_persistence_adapter import (
    ProjectRegistrationPersistenceAdapter,
)


class ProjectPersistenceStartupFactory:
    VERSION = "1.0"

    def create(
        self,
        startup: object,
    ) -> ApplicationStartupModule:
        if not isinstance(
            startup,
            object,
        ):
            raise TypeError(
                "startup required"
            )

        registration = getattr(
            startup,
            "project_registration",
            None,
        )
        registry = getattr(
            startup,
            "project_registry",
            None,
        )

        if registration is None or registry is None:
            raise RuntimeError(
                "application project persistence owners unavailable"
            )

        persistence = (
            ProjectPersistenceCompositionFactory()
            .create()
        )

        persistent_registration = (
            ProjectRegistrationPersistenceAdapter(
                registration=registration,
                persistence=persistence.repository,
                project_registry=registry,
                project_factory=(
                    registration.project_factory
                ),
            )
        )

        startup.project_registration = (
            persistent_registration
        )

        module = ApplicationStartupModule(
            startup
        )

        return PersistenceStartupAssemblyAdapter(
            startup_module=module,
            persistence=persistence,
        )


    def ready(self) -> bool:
        return True


__all__ = [
    "ProjectPersistenceStartupFactory",
]
