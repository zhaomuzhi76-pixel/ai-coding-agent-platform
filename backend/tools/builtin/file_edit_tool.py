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
from backend.workspace.workspace_architecture_guard import (
    WorkspaceBoundaryGuard,
)


class FileEditTool(RuntimeToolProtocol):
    name = "file_edit"
    description = "Edit workspace file by replacing text"

    def __init__(
        self,
        service: WorkspaceOperationContract,
        architecture_guard: WorkspaceBoundaryGuard,
    ) -> None:
        if not isinstance(
            service,
            WorkspaceOperationContract,
        ):
            raise TypeError(
                "service must WorkspaceOperationContract"
            )
        if not isinstance(
            architecture_guard,
            WorkspaceBoundaryGuard,
        ):
            raise TypeError(
                "architecture guard required"
            )
        self.service = service
        self.architecture_guard = architecture_guard

    async def execute(
        self,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        path = arguments.get("path")
        old_text = arguments.get("old_text")
        new_text = arguments.get("new_text")

        if not isinstance(path, str) or not path.strip():
            raise ValueError("path required")
        if not isinstance(old_text, str):
            raise ValueError("old_text required")
        if not isinstance(new_text, str):
            raise ValueError("new_text required")

        current = self.service.read_file(path)
        occurrences = current.count(old_text)

        if occurrences == 0:
            raise ValueError("old_text not found")
        if occurrences > 1:
            raise ValueError("old_text must occur exactly once")

        updated = current.replace(old_text, new_text, 1)
        guard = self.architecture_guard.check(
            {"path": path, "content": updated}
        )

        if not guard["allowed"]:
            return ToolResult.success_result(
                self.name,
                {
                    "path": path,
                    "replaced": 0,
                    "blocked": True,
                    "reason": "architecture conflict",
                    "architecture": guard,
                },
            )

        result = self.service.edit_file(
            path,
            old_text,
            new_text,
        )

        return ToolResult.success_result(
            self.name,
            {
                "path": path,
                "replaced": result.get("replaced", 1),
                "architecture": guard,
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
                    name="old_text",
                    parameter_type="string",
                    description="exact existing text",
                ),
                ToolParameter(
                    name="new_text",
                    parameter_type="string",
                    description="replacement text",
                ),
            ),
        )

    def ready(self) -> bool:
        return (
            self.service.ready()
            and self.architecture_guard.ready()
        )

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": "2.1",
            "responsibility": (
                "workspace_exact_text_edit",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "FileEditTool",
]
