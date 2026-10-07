from __future__ import annotations

from backend.assembly.application_project_session_graph import (
    ApplicationProjectSessionGraph,
)
from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)


class ApplicationProjectSessionConstruction:
    """Assembly-root constructor for the project/session graph."""

    VERSION = "3.0"

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

        self.graph = ApplicationProjectSessionGraph(
            workspace_factory=workspace_factory,
        )
        self._assembly: dict[str, object] | None = None

    def create(self) -> dict[str, object]:
        if not self.ready():
            raise RuntimeError(
                "project session construction unavailable"
            )

        assembly = self.graph.create()
        self._validate(assembly)
        self._assembly = dict(assembly)
        return dict(assembly)

    def ready(self) -> bool:
        return (
            self.graph.ready()
            and self.graph.workspace_factory.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "built": self._assembly is not None,
            "graph": self.graph.dump(),
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
                "project session assembly incomplete: "
                + ", ".join(missing)
            )


__all__ = [
    "ApplicationProjectSessionConstruction",
]
