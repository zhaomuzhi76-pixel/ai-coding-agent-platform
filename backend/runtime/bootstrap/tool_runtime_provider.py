from __future__ import annotations

from pathlib import Path

from backend.runtime.bootstrap.tool_registrar import RuntimeBuiltinToolRegistrar
from backend.runtime.tools.alias import ToolAliasResolver
from backend.runtime.tools.argument_resolver import ToolArgumentResolver
from backend.runtime.tools.registry import ToolRegistry
from backend.runtime.tools.runtime import ToolRuntime
from backend.runtime.tools.security.composition import ToolSecurityComposition
from backend.workspace.contracts.runtime_contract import WorkspaceRuntimeContract
from backend.workspace.contracts.runtime_factory_contract import WorkspaceRuntimeFactoryContract


class RuntimeToolRuntimeProvider:
    """Workspace-scoped unique ToolRuntime provider."""

    VERSION = "3.1"

    def __init__(
        self,
        *,
        registrar: RuntimeBuiltinToolRegistrar,
        workspace_factory: WorkspaceRuntimeFactoryContract,
    ) -> None:
        if not isinstance(registrar, RuntimeBuiltinToolRegistrar):
            raise TypeError("registrar must RuntimeBuiltinToolRegistrar")
        if not isinstance(workspace_factory, WorkspaceRuntimeFactoryContract):
            raise TypeError("workspace factory contract required")
        self.registrar = registrar
        self.workspace_factory = workspace_factory
        self._runtimes: dict[str, ToolRuntime] = {}

    def create(
        self,
        workspace: str | WorkspaceRuntimeContract,
    ) -> ToolRuntime:
        root = self._workspace_root(workspace)
        existing = self._runtimes.get(root)
        if existing is not None:
            if not existing.ready():
                raise RuntimeError("workspace tool runtime unavailable")
            return existing

        governance = ToolSecurityComposition().create()

        runtime = ToolRuntime(
            registry=ToolRegistry(),
            alias_resolver=ToolAliasResolver(),
            argument_resolver=ToolArgumentResolver(),
            governance=governance,
            workspace_root=root,
        )

        if isinstance(workspace, str):
            bound_workspace = self.workspace_factory.create(root)
        else:
            bound_workspace = workspace

        if not bound_workspace.ready():
            raise RuntimeError("workspace runtime not ready")

        self.registrar.register(
            runtime=runtime,
            workspace=bound_workspace,
        )

        if not runtime.ready():
            raise RuntimeError("workspace tool runtime unavailable")

        self._runtimes[root] = runtime
        return runtime

    def ready(self) -> bool:
        return (
            self.registrar.ready()
            and all(runtime.ready() for runtime in self._runtimes.values())
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "runtime_count": len(self._runtimes),
            "workspace_factory": type(self.workspace_factory).__name__,
            "workspaces": tuple(self._runtimes),
            "registrar": self.registrar.dump(),
            "ready": self.ready(),
        }

    @staticmethod
    def _workspace_root(
        workspace: str | WorkspaceRuntimeContract,
    ) -> str:
        if isinstance(workspace, str):
            root = workspace
        elif isinstance(workspace, WorkspaceRuntimeContract):
            root = workspace.root_path
        else:
            raise TypeError(
                "workspace must str or WorkspaceRuntimeContract"
            )

        if not isinstance(root, str) or not root.strip():
            raise ValueError("workspace root required")

        return str(Path(root).expanduser().resolve())


__all__ = ["RuntimeToolRuntimeProvider"]
