"""Generic domain lookup tool (reuses frozen core/runtime contracts)."""
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


class DomainLookupTool(RuntimeToolProtocol):
    name = "domain_lookup"
    description = (
        "查询任意领域（agriculture / finance / ...）的实体信息。"
        "domain 指定领域，entity_type 指定实体类型，name 指定实体。"
        "不传 name 时列出该类型下所有实体。"
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
        entity_type = str(arguments.get("entity_type", "") or "").strip()
        name = str(arguments.get("name", "") or "").strip()
        if not entity_type:
            return ToolResult.success_result(
                self.name,
                {"domain": domain_name,
                 "entity_types": provider.list_entity_types()},
            )
        if not name:
            return ToolResult.success_result(
                self.name,
                {"domain": domain_name,
                 "entity_type": entity_type,
                 "entities": provider.list_entities(entity_type)},
            )
        entity = provider.lookup_entity(entity_type, name)
        if entity is None:
            return ToolResult.success_result(
                self.name,
                {"error": f"not found: {name}",
                 "available": provider.list_entities(entity_type)},
            )
        return ToolResult.success_result(
            self.name, {"domain": domain_name, **entity.to_dict()},
        )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=(
                ToolParameter(
                    name="domain",
                    parameter_type="string",
                    description="领域名，如 agriculture / finance",
                ),
                ToolParameter(
                    name="entity_type",
                    parameter_type="string",
                    description="实体类型，如 crop / stock",
                    required=False,
                ),
                ToolParameter(
                    name="name",
                    parameter_type="string",
                    description="实体名或代码",
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
            "responsibility": "domain_entity_lookup",
            "ready": self.ready(),
        }


__all__ = ["DomainLookupTool"]
