"""Convert between core ToolSchema and MCP tool descriptors."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.core.tools.schema import ToolParameter, ToolSchema

# MCP 用 JSON Schema 类型名；core 用 ToolParameterType
_TYPE_FROM_MCP = {
    "string": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
    "object": "object",
    "array": "array",
}


def to_mcp_tool(schema: ToolSchema) -> Dict[str, Any]:
    """core ToolSchema -> MCP tools/list item."""
    properties: Dict[str, Any] = {}
    required: List[str] = []
    for p in schema.parameters:
        prop: Dict[str, Any] = {
            "type": p.parameter_type,
            "description": p.description,
        }
        if p.default is not None:
            prop["default"] = p.default
        properties[p.name] = prop
        if p.required:
            required.append(p.name)
    return {
        "name": schema.name,
        "description": schema.description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def from_mcp_tool(descriptor: Dict[str, Any]) -> ToolSchema:
    """MCP tools/list item -> core ToolSchema."""
    name = descriptor.get("name", "")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("MCP tool descriptor missing name")
    description = str(descriptor.get("description", ""))
    schema = descriptor.get("inputSchema") or {}
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    params: List[ToolParameter] = []
    for pname, spec in props.items():
        if not isinstance(spec, dict):
            continue
        mcp_type = str(spec.get("type", "string"))
        ptype = _TYPE_FROM_MCP.get(mcp_type, "string")
        params.append(ToolParameter(
            name=pname,
            parameter_type=ptype,
            description=str(spec.get("description", "")),
            required=pname in required,
            default=spec.get("default"),
        ))
    return ToolSchema(
        name=name, description=description,
        parameters=tuple(params),
    )


__all__ = ["to_mcp_tool", "from_mcp_tool"]
