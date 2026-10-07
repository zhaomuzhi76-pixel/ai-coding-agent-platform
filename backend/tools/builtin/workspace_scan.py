from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.schema import ToolParameter, ToolSchema
from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)


class WorkspaceScanTool(RuntimeToolProtocol):
    name = "workspace_scan"
    description = "Return workspace runtime intelligence summary"

    def __init__(
        self,
        workspace_runtime: WorkspaceRuntimeContract,
    ) -> None:
        if not isinstance(
            workspace_runtime,
            WorkspaceRuntimeContract,
        ):
            raise TypeError(
                "workspace runtime contract required"
            )
        self.workspace_runtime = workspace_runtime

    async def execute(
        self,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        runtime = self.workspace_runtime
        context = runtime.get_context()

        output = {
            "workspace": runtime.root_path,
            "runtime": runtime.dump(),
            "metadata": context.get_runtime_data(
                "workspace_analysis",
                {},
            ),
            "capabilities": [
                "workspace_runtime",
                "workspace_query",
                "file_access",
            ],
        }

        query = arguments.get("query")
        if query is not None:
            if not isinstance(query, str):
                raise ValueError("query must be string")
            service = runtime.get_query()
            output["query"] = query
            output["matches"] = service.find(query)

        if arguments.get("include_files", False):
            index = runtime.get_index()
            output["files"] = index.files()

        return ToolResult.success_result(
            self.name,
            output,
        )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=(
                ToolParameter(
                    name="query",
                    parameter_type="string",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="include_files",
                    parameter_type="boolean",
                    required=False,
                    default=False,
                ),
            ),
        )

    def ready(self) -> bool:
        return self.workspace_runtime.ready()

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": "1.1",
            "responsibility": (
                "workspace_runtime_intelligence",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "WorkspaceScanTool",
]
