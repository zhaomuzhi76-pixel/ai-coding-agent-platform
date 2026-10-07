from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.schema import ToolParameter, ToolSchema
from backend.workspace.contracts.operation_contract import (
    WorkspaceOperationContract,
)


class FileWriteTool(RuntimeToolProtocol):
    name = "file_write"
    description = "Write workspace file content"

    def __init__(
        self,
        service: WorkspaceOperationContract,
    ) -> None:
        if not isinstance(
            service,
            WorkspaceOperationContract,
        ):
            raise TypeError(
                "service must WorkspaceOperationContract"
            )
        self.service = service

    async def execute(
        self,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        path = arguments.get("path")
        content = arguments.get("content")

        if not isinstance(path, str) or not path.strip():
            raise ValueError("file path required")
        if not isinstance(content, str):
            raise ValueError("file content required")

        self.service.write_file(path, content)

        return ToolResult.success_result(
            self.name,
            {
                "path": path,
                "written": True,
                "size": len(content),
            },
        )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=(
                ToolParameter(
                    name="path",
                    parameter_type="string",
                    description="workspace relative file path",
                ),
                ToolParameter(
                    name="content",
                    parameter_type="string",
                    description="file content",
                ),
            ),
        )

    def ready(self) -> bool:
        return self.service.ready()

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": "1.1",
            "responsibility": (
                "workspace_file_write",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "FileWriteTool",
]
