"""RemoteTool: wrap a remote MCP tool as RuntimeToolProtocol."""
from __future__ import annotations

from typing import Any, Dict

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.schema import ToolSchema
from backend.mcp.client import McpClient, McpError
from backend.mcp.schema_mapper import from_mcp_tool


class RemoteTool(RuntimeToolProtocol):
    """A tool served by a remote MCP endpoint, callable via ToolRuntime."""

    VERSION = "1.0"

    def __init__(
        self,
        client: McpClient,
        descriptor: Dict[str, Any],
        *,
        namespaced: bool = True,
        prefix: str = "mcp",
    ) -> None:
        if client is None:
            raise ValueError("client required")
        self._client = client
        self._schema = from_mcp_tool(descriptor)
        raw_name = self._schema.name
        self.name = f"{prefix}.{raw_name}" if namespaced else raw_name
        self.description = self._schema.description

    async def execute(
        self, arguments: ToolArguments,
    ) -> ToolResultProtocol:
        try:
            remote = await self._client.call_tool(
                self._schema.name, dict(arguments),
            )
        except McpError as exc:
            return ToolResult.failure_result(
                self.name, f"MCP error: {exc}",
            )
        except Exception as exc:
            return ToolResult.failure_result(
                self.name, f"{type(exc).__name__}: {exc}",
            )
        is_error = bool(remote.get("isError", False))
        content = remote.get("content", [])
        output = self._extract_text(content)
        if is_error:
            return ToolResult.failure_result(self.name, output)
        return ToolResult.success_result(self.name, output)

    @staticmethod
    def _extract_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return str(content)
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "\n".join(parts)

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self._schema.description,
            parameters=self._schema.parameters,
        )

    def ready(self) -> bool:
        return self._client.ready()

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": self.VERSION,
            "responsibility": "remote_mcp_tool",
            "remote_name": self._schema.name,
            "ready": self.ready(),
        }


__all__ = ["RemoteTool"]
