from __future__ import annotations

from backend.runtime.bootstrap.providers import (
    RuntimeComponentProvider,
)
from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)


class RuntimeComponentProviderFactory:
    """
    Construct the runtime component provider.

    Owns:
        - RuntimeComponentProvider construction
        - runtime infrastructure readiness validation
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        workspace_root: str,
        workspace_factory: WorkspaceRuntimeFactoryContract,
        code_intelligence_workspace,
        code_intelligence_resolver,
        code_modification_provider,
        code_analyzer,
    ) -> RuntimeComponentProvider:
        if not isinstance(workspace_root, str) or not workspace_root.strip():
            raise ValueError(
                "workspace root required"
            )

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

        runtime = RuntimeComponentProvider(
            workspace_root=workspace_root,
            workspace_factory=workspace_factory,
            code_intelligence_workspace=code_intelligence_workspace,
            code_intelligence_resolver=code_intelligence_resolver,
            code_modification_provider=code_modification_provider,
            code_analyzer=code_analyzer,
        )

        if not runtime.ready():
            raise RuntimeError(
                "runtime component provider unavailable"
            )

        return runtime

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeComponentProviderFactory",
]
