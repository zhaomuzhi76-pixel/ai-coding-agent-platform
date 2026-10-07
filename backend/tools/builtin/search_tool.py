from __future__ import annotations

import fnmatch

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.schema import ToolParameter, ToolSchema
from backend.workspace.contracts.index_contract import (
    WorkspaceIndexContract,
)
from backend.workspace.contracts.operation_contract import (
    WorkspaceOperationContract,
)


class SearchTool(RuntimeToolProtocol):
    name = "search"
    description = "Search workspace index"
    MAX_RESULTS = 100

    def __init__(
        self,
        index: WorkspaceIndexContract,
        operations: WorkspaceOperationContract,
    ) -> None:
        if not isinstance(
            index,
            WorkspaceIndexContract,
        ):
            raise TypeError(
                "index must WorkspaceIndexContract"
            )
        if not isinstance(
            operations,
            WorkspaceOperationContract,
        ):
            raise TypeError(
                "operations must WorkspaceOperationContract"
            )
        self.index = index
        self.operations = operations

    async def execute(
        self,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        pattern = arguments.get("pattern", "*")
        query = arguments.get("query")
        keyword = arguments.get("keyword")

        if not isinstance(pattern, str):
            raise ValueError("pattern must be string")
        if keyword is not None:
            if not isinstance(keyword, str):
                raise ValueError("keyword must be string")
            query = keyword
        if query is not None and not isinstance(query, str):
            raise ValueError("query must be string")

        results = []

        for item in self.index.files():
            if len(results) >= self.MAX_RESULTS:
                break

            path = item.get("path", "")
            if not path or not fnmatch.fnmatch(path, pattern):
                continue

            result = {"file": path}

            if query:
                matches = self._search_content(path, query)
                if not matches:
                    continue
                result["matches"] = matches

            results.append(result)

        return ToolResult.success_result(
            self.name,
            {
                "query": query,
                "pattern": pattern,
                "count": len(results),
                "results": results,
            },
        )

    def _search_content(
        self,
        path: str,
        query: str,
    ) -> list[int]:
        try:
            content = self.operations.read_file(path)
        except Exception:
            return []

        needle = query.lower()

        return [
            line_no
            for line_no, line in enumerate(
                content.splitlines(),
                start=1,
            )
            if needle in line.lower()
        ]

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=(
                ToolParameter(
                    name="pattern",
                    parameter_type="string",
                    required=False,
                    default="*",
                ),
                ToolParameter(
                    name="query",
                    parameter_type="string",
                    required=False,
                    default=None,
                ),
            ),
        )

    def ready(self) -> bool:
        return (
            self.index.ready()
            and self.operations.ready()
        )

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": "1.1",
            "responsibility": (
                "indexed_search",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "SearchTool",
]
