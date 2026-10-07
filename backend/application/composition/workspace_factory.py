from __future__ import annotations

from backend.application.composition.workspace import (
    ApplicationWorkspaceComposition,
)
from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)


class ApplicationWorkspaceCompositionFactory:
    """
    Sole construction owner for ApplicationWorkspaceComposition.
    """

    VERSION = "2.1"

    def create(
        self,
        *,
        workspace_root: str,
        factory: WorkspaceRuntimeFactoryContract,
    ) -> ApplicationWorkspaceComposition:
        composition = ApplicationWorkspaceComposition(
            workspace_root=workspace_root,
            factory=factory,
        )

        if not composition.ready():
            raise RuntimeError(
                "application workspace composition unavailable"
            )

        return composition

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationWorkspaceCompositionFactory",
]
