from __future__ import annotations

from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)
from backend.workspace.project.project_model_factory import (
    ProjectModelFactory,
)
from backend.workspace.project.registry.project_registry_factory import (
    ProjectRegistryFactory,
)
from backend.workspace.project.runtime.project_runtime_factory import (
    ProjectRuntimeFactory,
)
from backend.workspace.project.session.lifecycle.project_session_lifecycle_factory import (
    ProjectSessionLifecycleFactory,
)
from backend.workspace.project.session.project_session_model_factory import (
    ProjectSessionModelFactory,
)
from backend.workspace.project.session.registry.project_session_registry_composition import (
    ProjectSessionRegistryComposition,
)
from backend.workspace.project.session.runtime.project_session_runtime_factory import (
    ProjectSessionRuntimeFactory,
)
from backend.workspace.project.session.service.project_session_service_factory import (
    ProjectSessionServiceFactory,
)


class ApplicationProjectSessionGraph:
    """Assembly-owned lower-layer project/session graph."""

    VERSION = "1.1"

    def __init__(
        self,
        *,
        workspace_factory: WorkspaceRuntimeFactoryContract,
    ) -> None:
        if not isinstance(
            workspace_factory,
            WorkspaceRuntimeFactoryContract,
        ):
            raise TypeError(
                "workspace factory contract required"
            )

        if not workspace_factory.ready():
            raise RuntimeError(
                "workspace runtime factory unavailable"
            )

        self.workspace_factory = workspace_factory

    def create(self) -> dict[str, object]:
        project_registry = (
            ProjectRegistryFactory().create()
        )
        project_factory = ProjectModelFactory()

        project_runtime_factory = ProjectRuntimeFactory(
            project_factory=project_factory,
            workspace_factory=self.workspace_factory,
        )

        session_factory = ProjectSessionModelFactory()

        session_runtime_factory = (
            ProjectSessionRuntimeFactory(
                session_factory=session_factory,
                project_runtime_factory=(
                    project_runtime_factory
                ),
            )
        )

        registry_composition = (
            ProjectSessionRegistryComposition()
        )
        binding = registry_composition.create(
            project_registry=project_registry,
        )

        lifecycle = ProjectSessionLifecycleFactory().create(
            binding.session_registry,
        )

        service = ProjectSessionServiceFactory().create(
            project_registry=project_registry,
            session_registry=binding.session_registry,
            lifecycle=lifecycle,
            session_factory=session_factory,
        )

        result = {
            "project_registry": project_registry,
            "registry_composition": registry_composition,
            "session_registry": binding.session_registry,
            "session_registry_binding": binding,
            "session_lifecycle": lifecycle,
            "session_service": service,
            "session_model_factory": session_factory,
            "session_runtime_factory": (
                session_runtime_factory
            ),
            "project_factory": project_factory,
            "project_runtime_factory": (
                project_runtime_factory
            ),
        }

        self._validate(result)
        return result

    def ready(self) -> bool:
        return self.workspace_factory.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate(
        assembly: dict[str, object],
    ) -> None:
        required = (
            "project_registry",
            "registry_composition",
            "session_registry",
            "session_registry_binding",
            "session_lifecycle",
            "session_service",
            "session_model_factory",
            "session_runtime_factory",
            "project_factory",
            "project_runtime_factory",
        )

        missing = tuple(
            key
            for key in required
            if assembly.get(key) is None
        )

        if missing:
            raise RuntimeError(
                "project session graph incomplete: "
                + ", ".join(missing)
            )


__all__ = [
    "ApplicationProjectSessionGraph",
]
