"""FileReadTool —— 走 WorkspaceOperationContract 的装配式工具。

与 backend/application/agent_loop/tool_registry.py::read_file 的关系：
  - 本工具  : 需要 WorkspaceOperationContract 注入，返回 ToolResultProtocol，
              走 pipeline / executor 场景
  - 后者    : 轻量、无装配，直接复用 WorkspaceFileAccess，
              走 WS Agent 循环场景

两者共享底层 WorkspaceFileAccess（含 path traversal 保护），路径安全逻辑唯一。
"""
from __future__ import annotations
from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.schema import ToolParameter, ToolSchema
from backend.workspace.contracts.operation_contract import (
    WorkspaceOperationContract,
)


class FileReadTool(RuntimeToolProtocol):
    name = "file_read"
    description = "Read workspace file content"

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

        if not isinstance(path, str) or not path.strip():
            raise ValueError("file path required")

        content = self.service.read_file(path)

        return ToolResult.success_result(
            self.name,
            {
                "path": path,
                "content": content,
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
            ),
        )

    def ready(self) -> bool:
        return self.service.ready()

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": "1.1",
            "responsibility": (
                "workspace_file_read",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "FileReadTool",
]
