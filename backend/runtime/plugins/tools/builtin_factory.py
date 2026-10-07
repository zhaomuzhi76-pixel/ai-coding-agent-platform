from __future__ import annotations

from backend.core.code_intelligence.analysis_port import (
    CodeAnalyzerProtocol,
)
from backend.runtime.contracts.tool import (
    RuntimeToolContractProtocol,
)
from backend.runtime.tools.security.command_guard import (
    ToolCommandGuard,
)
from backend.tools.builtin.code_analysis import CodeAnalysisTool
from backend.tools.builtin.file_edit_tool import FileEditTool
from backend.tools.builtin.file_read import FileReadTool
from backend.tools.builtin.file_tree_tool import FileTreeTool
from backend.tools.builtin.file_write import FileWriteTool
from backend.tools.builtin.search_tool import SearchTool
from backend.tools.builtin.terminal_tool import TerminalTool
from backend.tools.builtin.workspace_scan import WorkspaceScanTool
from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)
from backend.workspace.workspace_architecture_guard import (
    WorkspaceBoundaryGuard,
)


class RuntimeBuiltinToolFactory:
    """Runtime-owned builtin tool construction boundary."""

    VERSION = "1.4"
    RESPONSIBILITY = (
        "runtime_builtin_tool_construction",
    )

    def create(
        self,
        workspace: WorkspaceRuntimeContract,
        analyzer: CodeAnalyzerProtocol,
    ) -> tuple[RuntimeToolContractProtocol, ...]:
        self._validate_workspace(workspace)
        self._validate_analyzer(analyzer)

        operations = workspace.get_operations()
        index = workspace.get_index()
        root = workspace.root_path

        tools: tuple[RuntimeToolContractProtocol, ...] = (
            FileReadTool(operations),
            FileWriteTool(operations),
            FileEditTool(
                operations,
                WorkspaceBoundaryGuard(),
            ),
            FileTreeTool(index),
            SearchTool(index, operations),
            TerminalTool(
                root,
                ToolCommandGuard(),
            ),
            CodeAnalysisTool(
                analyzer,
                operations,
            ),
            WorkspaceScanTool(workspace),
        )

        if not all(tool.ready() for tool in tools):
            raise RuntimeError(
                "runtime builtin tool construction produced "
                "unready tool"
            )

        return tools

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
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate_workspace(
        workspace: object,
    ) -> None:
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

    @staticmethod
    def _validate_analyzer(
        analyzer: object,
    ) -> None:
        if not isinstance(
            analyzer,
            CodeAnalyzerProtocol,
        ):
            raise TypeError(
                "analyzer must implement CodeAnalyzerProtocol"
            )

        if not analyzer.ready():
            raise RuntimeError(
                "code analyzer not ready"
            )


__all__ = [
    "RuntimeBuiltinToolFactory",
]
