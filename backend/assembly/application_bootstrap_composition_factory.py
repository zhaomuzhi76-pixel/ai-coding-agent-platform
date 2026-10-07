from __future__ import annotations

from pathlib import Path

from backend.config.settings import settings
from backend.providers.assembly.configuration import (
    ProviderAssemblyConfiguration,
)
from backend.application.composition.execution_dependency_assembly import (
    ApplicationExecutionDependencyAssembly,
)
from backend.providers.assembly.builder import (
    ProviderAssemblyBuilder,
)
from backend.providers.assembly.runtime_factory import (
    ProviderAssemblyRuntimeFactory,
)
from backend.application.startup_factory import (
    ApplicationStartupFactory,
)
from backend.assembly.application_planner_construction import (
    ApplicationPlannerConstruction,
)
from backend.assembly.application_project_session_construction import (
    ApplicationProjectSessionConstruction,
)
from backend.assembly.application_runtime_construction import (
    ApplicationRuntimeConstruction,
)
from backend.assembly.startup_module import (
    ApplicationStartupModule,
)
from backend.application.composition.runtime_construction_port import (
    ApplicationRuntimeConstructionProtocol,
)
from backend.application.composition.project_session_construction_port import (
    ApplicationProjectSessionConstructionProtocol,
)
from backend.core.planning import PlannerPortProtocol
from backend.persistence.plugins.project_persistence_startup_factory import (
    ProjectPersistenceStartupFactory,
)
from backend.persistence.plugins.persistence_startup_assembly_adapter import (
    PersistenceStartupAssemblyAdapter,
)
from backend.persistence.plugins.project_persistence_composition_factory import (
    ProjectPersistenceCompositionFactory,
)
from backend.persistence.plugins.project_session_persistence_startup_factory import (
    ProjectSessionPersistenceStartupFactory,
)


class ApplicationBootstrapCompositionFactory:
    """
    Top-level Application construction composition root.

    Owns:
        - Application construction dependency assembly
        - planner construction
        - project/session construction
        - ApplicationStartup construction
        - startup-module projection

    Does not own:
        - system integration runtime construction
        - process supervision
        - API transport
        - application lifecycle implementation
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        workspace_root: str,
    ) -> ApplicationStartupModule:
        root = self._validate_workspace_root(
            workspace_root
        )

        provider_context = (
            ProviderAssemblyBuilder(
                configuration=ProviderAssemblyConfiguration()
            )
            .build()
        )
        provider_runtime = (
            ProviderAssemblyRuntimeFactory()
            .create(
                provider_context
            )
        )

        runtime_construction = (
            ApplicationRuntimeConstruction(
                workspace_root=root,
                execution_dependency_assembly=(
                    ApplicationExecutionDependencyAssembly(
                        provider_runtime=provider_runtime,
                    )
                ),
            )
        )

        planner = ApplicationPlannerConstruction(
            workspace_root=root,
        ).create()

        project_session_construction = (
            ApplicationProjectSessionConstruction(
                workspace_factory=(
                    runtime_construction.workspace_factory
                ),
            )
        )

        startup = ApplicationStartupFactory(
            runtime_construction=runtime_construction,
            planner=planner,
            project_session_construction=(
                project_session_construction
            ),
        ).create()

        module = (
            ProjectPersistenceStartupFactory()
            .create(startup)
        )
        module = (
            ProjectSessionPersistenceStartupFactory()
            .create(module)
        )

        self._validate_result(
            runtime_construction=runtime_construction,
            planner=planner,
            project_session_construction=(
                project_session_construction
            ),
            module=module,
        )

        return module

    @staticmethod
    def _validate_workspace_root(
        workspace_root: str,
    ) -> str:
        if (
            not isinstance(workspace_root, str)
            or not workspace_root.strip()
        ):
            raise ValueError(
                "workspace root required"
            )

        return str(
            Path(workspace_root)
            .expanduser()
            .resolve()
        )

    @staticmethod
    def _validate_result(
        *,
        runtime_construction: object,
        planner: object,
        project_session_construction: object,
        module: object,
    ) -> None:
        if not isinstance(
            runtime_construction,
            ApplicationRuntimeConstructionProtocol,
        ):
            raise TypeError(
                "runtime construction contract violation"
            )

        if not isinstance(
            planner,
            PlannerPortProtocol,
        ):
            raise TypeError(
                "planner contract violation"
            )

        if not isinstance(
            project_session_construction,
            ApplicationProjectSessionConstructionProtocol,
        ):
            raise TypeError(
                "project session construction contract violation"
            )

        if not isinstance(
            module,
            ApplicationStartupModule,
        ):
            raise TypeError(
                "startup module construction violation"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationBootstrapCompositionFactory",
]
