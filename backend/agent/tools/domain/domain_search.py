"""Generic domain search tool."""
from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.schema import ToolParameter, ToolSchema
from backend.domain.registry import DomainRegistry


class DomainSearchTool(RuntimeToolProtocol):
    name = "domain_search"
    description = "在指定领域内做关键词搜索，返回匹配实体。"
    VERSION = "1.0"

    def __init__(self, registry: DomainRegistry) -> None:
        if registry is None:
            raise ValueError("domain registry required")
        self._registry = registry

    async def execute(
        self, arguments: ToolArguments,
    ) -> ToolResultProtocol:
        domain_name = str(arguments.get("domain", "") or "").strip()
        query = str(arguments.get("query", "") or "").strip()
        try:
            limit = int(arguments.get("limit", 10) or 10)
        except (TypeError, ValueError):
            limit = 10
        if not domain_name:
            return ToolResult.success_result(
                self.name,
                {"error": "domain required",
                 "available": self._registry.names()},
            )
        if not query:
            return ToolResult.success_result(
                self.name, {"error": "query required"},
            )
        try:
            provider = self._registry.resolve(domain_name)
        except KeyError as exc:
            return ToolResult.success_result(
                self.name,
                {"error": str(exc),
                 "available": self._registry.names()},
            )
        hits = provider.search_entities(query, limit=limit)
        return ToolResult.success_result(
            self.name,
            {
                "domain": domain_name,
                "query": query,
                "count": len(hits),
                "results": [h.to_dict() for h in hits],
            },
        )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=(
                ToolParameter(
                    name="domain",
                    parameter_type="string",
                    description="领域名",
                ),
                ToolParameter(
                    name="query",
                    parameter_type="string",
                    description="搜索关键词",
                ),
                ToolParameter(
                    name="limit",
                    parameter_type="integer",
                    description="返回上限",
                    required=False,
                    default=10,
                ),
            ),
        )

    def ready(self) -> bool:
        return self._registry.ready()

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": self.VERSION,
            "responsibility": "domain_search",
            "ready": self.ready(),
        }


__all__ = ["DomainSearchTool"]
