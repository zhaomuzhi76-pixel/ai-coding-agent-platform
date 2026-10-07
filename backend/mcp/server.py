"""MCP server: expose a ToolRuntime over JSON-RPC."""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.mcp import protocol as P
from backend.mcp.jsonrpc import (
    JsonRpcRequest, JsonRpcResponse,
)
from backend.mcp.schema_mapper import to_mcp_tool
from backend.mcp.transport.base import Transport
from backend.runtime.tools.runtime import ToolRuntime


class McpServer:
    """Handle MCP JSON-RPC requests against a ToolRuntime."""

    VERSION = "1.0.0"

    def __init__(
        self,
        tool_runtime: ToolRuntime,
        transport: Transport,
        *,
        server_name: str = P.SERVER_NAME,
        server_version: str = P.SERVER_VERSION,
    ) -> None:
        if not isinstance(tool_runtime, ToolRuntime):
            raise TypeError("tool_runtime must ToolRuntime")
        self._tools = tool_runtime
        self._transport = transport
        self._name = server_name
        self._version = server_version
        self._initialized = False

    # ─── main loop ──────────────────────────────────────────
    async def serve_forever(self) -> None:
        while True:
            raw = await self._transport.receive()
            if raw is None:
                break
            response = await self._handle(raw)
            if response is not None:
                await self._transport.send(response)

    # ─── dispatch ───────────────────────────────────────────
    async def _handle(
        self, raw: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict) or "method" not in raw:
            return JsonRpcResponse(
                id=raw.get("id") if isinstance(raw, dict) else None,
                error=P.error(P.INVALID_REQUEST, "not a request"),
            ).to_dict()
        req = JsonRpcRequest.from_dict(raw)
        response = await self.handle_request(req)
        if response is None:
            return None
        return response.to_dict()

    async def handle_request(
        self, req: JsonRpcRequest,
    ) -> Optional[JsonRpcResponse]:
        try:
            if req.method == P.METHOD_INITIALIZE:
                return JsonRpcResponse(
                    id=req.id, result=self._initialize(req.params),
                )
            if req.method == P.METHOD_PING:
                return JsonRpcResponse(id=req.id, result={})
            if req.method == P.METHOD_TOOLS_LIST:
                return JsonRpcResponse(
                    id=req.id, result=self._list_tools(),
                )
            if req.method == P.METHOD_TOOLS_CALL:
                return await self._call_tool(req)
            return JsonRpcResponse(
                id=req.id, error=P.method_not_found(req.method),
            )
        except Exception as exc:
            return JsonRpcResponse(
                id=req.id,
                error=P.internal_error(f"{type(exc).__name__}: {exc}"),
            )

    # ─── method impls ───────────────────────────────────────
    def _initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self._initialized = True
        return {
            "protocolVersion": P.PROTOCOL_VERSION,
            "serverInfo": {
                "name": self._name, "version": self._version,
            },
            "capabilities": {"tools": {"listChanged": False}},
        }

    def _list_tools(self) -> Dict[str, Any]:
        tools = []
        for name in self._tools.registry.names():
            tool = self._tools.registry.get(name)
            if tool is None:
                continue
            tools.append(to_mcp_tool(tool.schema()))
        return {"tools": tools}

    async def _call_tool(
        self, req: JsonRpcRequest,
    ) -> JsonRpcResponse:
        name = req.params.get("name")
        args = req.params.get("arguments") or {}
        if not isinstance(name, str) or not name.strip():
            return JsonRpcResponse(
                id=req.id, error=P.invalid_params("name required"),
            )
        if not isinstance(args, dict):
            return JsonRpcResponse(
                id=req.id,
                error=P.invalid_params("arguments must object"),
            )
        if self._tools.get_tool(name) is None:
            return JsonRpcResponse(
                id=req.id, error=P.tool_not_found(name),
            )
        try:
            result = await self._tools.execute(name, args)
        except Exception as exc:
            return JsonRpcResponse(
                id=req.id,
                error=P.tool_failed(name, f"{type(exc).__name__}: {exc}"),
            )
        return JsonRpcResponse(
            id=req.id, result=self._serialize_result(result),
        )

    @staticmethod
    def _serialize_result(result: Any) -> Dict[str, Any]:
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(getattr(result, "output", result)),
                }
            ],
            "isError": not bool(getattr(result, "success", True)),
            "tool": getattr(result, "tool_name", ""),
        }

    # ─── introspection ──────────────────────────────────────
    def initialized(self) -> bool:
        return self._initialized

    def ready(self) -> bool:
        return self._tools.ready() and self._transport.ready()

    def dump(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "version": self._version,
            "protocol": P.PROTOCOL_VERSION,
            "ready": self.ready(),
            "initialized": self._initialized,
        }


__all__ = ["McpServer"]
