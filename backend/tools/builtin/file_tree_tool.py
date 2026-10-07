from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.schema import ToolSchema
from backend.workspace.contracts.index_contract import (
    WorkspaceIndexContract,
)


class FileTreeTool(RuntimeToolProtocol):
    name = "file_tree"
    description = "Return workspace tree from index"

    def __init__(
        self,
        index: WorkspaceIndexContract,
    ) -> None:
        if not isinstance(
            index,
            WorkspaceIndexContract,
        ):
            raise TypeError(
                "index must WorkspaceIndexContract"
            )
        self.index = index

    async def execute(
        self,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        files = sorted(
            item["path"]
            for item in self.index.files()
            if item.get("path")
        )

        directories = sorted(
            {
                "/".join(path.split("/")[:-1])
                for path in files
                if "/" in path
            }
        )

        return ToolResult.success_result(
            self.name,
            {
                "directories": directories,
                "files": files,
                "directory_count": len(directories),
                "file_count": len(files),
            },
        )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
        )

    def ready(self) -> bool:
        return self.index.ready()

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": "1.2",
            "responsibility": (
                "indexed_tree_view",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "FileTreeTool",
]
