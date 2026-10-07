"""MCP client: send requests, correlate responses."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.mcp import protocol as P
from backend.mcp.jsonrpc import JsonRpcRequest
from backend.mcp.transport.base import Transport


class McpError(RuntimeError):
    """Raised when MCP server returns an error."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.data = data


class McpClient:
    """Request / response client for a single MCP transport."""

    VERSION = "1.0.0"

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._next_id = 1
        self._server_info: Dict[str, Any] = {}

    # ─── low-level ──────────────────────────────────────────
    def _alloc_id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    async def request(
        self, method: str, params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        req_id = self._alloc_id()
        req = JsonRpcRequest(method=method, params=params or {}, id=req_id)
        await self._transport.send(req.to_dict())
        while True:
            raw = await self._transport.receive()
            if raw is None:
                raise McpError(-32000, "transport closed")
            if raw.get("id") != req_id:
                continue  # 忽略乱序 / 通知
            if "error" in raw:
                err = raw["error"]
                raise McpError(
                    int(err.get("code", -32603)),
                    str(err.get("message", "unknown")),
                    err.get("data"),
                )
            return raw.get("result")

    # ─── MCP methods ────────────────────────────────────────
    async def initialize(
        self, client_name: str = "backend-mcp-client",
        client_version: str = "1.0.0",
    ) -> Dict[str, Any]:
        result = await self.request(P.METHOD_INITIALIZE, {
            "protocolVersion": P.PROTOCOL_VERSION,
            "capabilities": {},  # 新版 MCP server 要求该字段为对象
            "clientInfo": {
                "name": client_name, "version": client_version,
            },
        })
        if isinstance(result, dict):
            self._server_info = result.get("serverInfo", {})
        return result if isinstance(result, dict) else {}

    async def list_tools(self) -> List[Dict[str, Any]]:
        result = await self.request(P.METHOD_TOOLS_LIST, {})
        if isinstance(result, dict):
            tools = result.get("tools")
            if isinstance(tools, list):
                return tools
        return []

    async def call_tool(
        self, name: str, arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        result = await self.request(P.METHOD_TOOLS_CALL, {
            "name": name, "arguments": dict(arguments),
        })
        return result if isinstance(result, dict) else {"content": []}

    async def ping(self) -> bool:
        result = await self.request(P.METHOD_PING, {})
        return result == {}

    # ─── introspection ──────────────────────────────────────
    def server_info(self) -> Dict[str, Any]:
        return dict(self._server_info)

    def ready(self) -> bool:
        return self._transport.ready()

    def dump(self) -> Dict[str, Any]:
        return {
            "ready": self.ready(),
            "server": dict(self._server_info),
            "next_id": self._next_id,
        }


__all__ = ["McpClient", "McpError"]
