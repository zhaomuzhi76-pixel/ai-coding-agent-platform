from __future__ import annotations

from pathlib import Path

from backend.core.code_intelligence.analysis_port import (
    CodeAnalyzerProtocol,
)
from backend.runtime.tools.runtime import ToolRuntime
from backend.rag.service import get_rag_service
from backend.rag.tools.rag_tools import register_rag_tools
from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)


class RuntimeBuiltinToolRegistrar:
    """
    Register builtin tools into each workspace-scoped ToolRuntime.

    Responsibility:
        - accept the injected analyzer contract
        - construct builtin tools
        - register them into the supplied ToolRuntime
        - enforce one registration per workspace/runtime pair

    Not Responsible:
        - ToolRuntime construction
        - workspace construction
        - executor construction
        - capability registration
        - concrete code intelligence construction
    """

    VERSION = "3.0"

    def __init__(
        self,
        *,
        code_analyzer: CodeAnalyzerProtocol,
    ) -> None:
        if not isinstance(
            code_analyzer,
            CodeAnalyzerProtocol,
        ):
            raise TypeError(
                "code analyzer contract required"
            )

        if not code_analyzer.ready():
            raise RuntimeError(
                "code analyzer unavailable"
            )

        self.code_analyzer = code_analyzer
        self._bindings: dict[
            str,
            tuple[int, int],
        ] = {}

    def register(
        self,
        *,
        runtime: ToolRuntime,
        workspace: WorkspaceRuntimeContract,
    ) -> int:
        if not isinstance(
            runtime,
            ToolRuntime,
        ):
            raise TypeError(
                "runtime must ToolRuntime"
            )

        if not isinstance(
            workspace,
            WorkspaceRuntimeContract,
        ):
            raise TypeError(
                "workspace must WorkspaceRuntimeContract"
            )

        if not workspace.ready():
            raise RuntimeError(
                "workspace runtime not ready"
            )

        if not self.code_analyzer.ready():
            raise RuntimeError(
                "code analyzer unavailable"
            )

        workspace_root = self._workspace_root(
            workspace
        )
        runtime_id = id(runtime)
        existing = self._bindings.get(
            workspace_root
        )

        if existing is not None:
            bound_runtime_id, count = existing

            if bound_runtime_id != runtime_id:
                raise RuntimeError(
                    "workspace already bound to another "
                    "tool runtime"
                )

            return count

        from backend.runtime.plugins.tools.builtin_factory import (
            RuntimeBuiltinToolFactory,
        )

        tools = RuntimeBuiltinToolFactory().create(
            workspace=workspace,
            analyzer=self.code_analyzer,
        )

        for tool in tools:
            runtime.register_tool(tool)

        count = len(tools)
        if count == 0:
            raise RuntimeError(
                "builtin tool registration produced no tools"
            )

        self._bindings[workspace_root] = (
            runtime_id,
            count,
        )
        return count

    def ready(self) -> bool:
        return (
            self.code_analyzer.ready()
            and all(
                count > 0
                for _, count in self._bindings.values()
            )
        ) if self._bindings else self.code_analyzer.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "workspace_count": len(
                self._bindings
            ),
            "workspaces": tuple(
                self._bindings
            ),
            "tool_counts": {
                root: count
                for root, (_, count)
                in self._bindings.items()
            },
            "code_analyzer": type(
                self.code_analyzer
            ).__name__,
        }

    @staticmethod
    def _workspace_root(
        workspace: WorkspaceRuntimeContract,
    ) -> str:
        root = workspace.root_path

        if (
            not isinstance(root, str)
            or not root.strip()
        ):
            raise ValueError(
                "workspace root required"
            )

        return str(
            Path(root)
            .expanduser()
            .resolve()
        )


__all__ = [
    "RuntimeBuiltinToolRegistrar",
]

def register_rag_tools_into(runtime) -> None:
    """把 RAG 工具注册进 runtime（幂等；失败静默）。"""
    try:
        service = get_rag_service()
        register_rag_tools(runtime, service)
    except Exception as exc:
        print(f"[tool_registrar] rag register failed: {exc}", flush=True)

