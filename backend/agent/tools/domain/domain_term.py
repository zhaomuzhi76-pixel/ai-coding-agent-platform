"""Generic domain term lookup tool."""
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


class DomainTermTool(RuntimeToolProtocol):
    name = "domain_term"
    description = (
        "查询领域术语 / 概念定义。"
        "不传 name 时列出该领域所有术语。"
    )
    VERSION = "1.0"

    def __init__(self, registry: DomainRegistry) -> None:
        if registry is None:
            raise ValueError("domain registry required")
        self._registry = registry

    async def execute(
        self, arguments: ToolArguments,
    ) -> ToolResultProtocol:
        domain_name = str(arguments.get("domain", "") or "").strip()
        if not domain_name:
            return ToolResult.success_result(
                self.name,
                {"error": "domain required",
                 "available": self._registry.names()},
            )
        try:
            provider = self._registry.resolve(domain_name)
        except KeyError as exc:
            return ToolResult.success_result(
                self.name,
                {"error": str(exc),
                 "available": self._registry.names()},
            )
        name = str(arguments.get("name", "") or "").strip()
        if not name:
            return ToolResult.success_result(
                self.name,
                {"domain": domain_name, "terms": provider.list_terms()},
            )
        term = provider.lookup_term(name)
        if term is None:
            return ToolResult.success_result(
                self.name,
                {"error": f"term not found: {name}",
                 "available": provider.list_terms()},
            )
        return ToolResult.success_result(
            self.name, {"domain": domain_name, **term.to_dict()},
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
                    name="name",
                    parameter_type="string",
                    description="术语名",
                    required=False,
                ),
            ),
        )

    def ready(self) -> bool:
        return self._registry.ready()

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": self.VERSION,
            "responsibility": "domain_term_lookup",
            "ready": self.ready(),
        }


__all__ = ["DomainTermTool"]
