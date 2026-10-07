from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.schema import ToolParameter, ToolSchema
from backend.tools.builtin.dependencies import (
    CodeAnalyzerProtocol,
)
from backend.workspace.contracts.operation_contract import (
    WorkspaceOperationContract,
)


class CodeAnalysisTool(RuntimeToolProtocol):
    name = "code_analysis"
    description = "Analyze python source structure"

    def __init__(
        self,
        analyzer: CodeAnalyzerProtocol,
        operations: WorkspaceOperationContract,
    ) -> None:
        if not isinstance(analyzer, CodeAnalyzerProtocol):
            raise TypeError("analyzer must CodeAnalyzerProtocol")
        if not isinstance(
            operations,
            WorkspaceOperationContract,
        ):
            raise TypeError(
                "operations must WorkspaceOperationContract"
            )
        self.analyzer = analyzer
        self.operations = operations

    async def execute(
        self,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        source = arguments.get("content")
        path = arguments.get("path")

        if source is not None and not isinstance(source, str):
            raise ValueError("content must be string")
        if path is not None and not isinstance(path, str):
            raise ValueError("path must be string")

        if not source and path:
            source = self.operations.read_file(path)

        if not source:
            raise ValueError("source or path required")

        analysis = self.analyzer.analyze(source)

        return ToolResult.success_result(
            self.name,
            {
                "path": path,
                "analysis": analysis,
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
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="content",
                    parameter_type="string",
                    required=False,
                    default=None,
                ),
            ),
        )

    def ready(self) -> bool:
        return (
            self.analyzer.ready()
            and self.operations.ready()
        )

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": "2.0",
            "responsibility": (
                "python_code_analysis",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "CodeAnalysisTool",
]
