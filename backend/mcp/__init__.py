"""MCP layer: protocol adaptation over frozen tool contracts.

职责边界：
    core.tools.*       -> 工具协议（冻结）
    runtime.tools.*    -> 工具运行时（冻结）
    backend.mcp.*      -> 只做 JSON-RPC + MCP method 适配
MCP 不重造工具、不重造结果类型、不重造 registry。
"""
from backend.mcp.jsonrpc import (
    JsonRpcError, JsonRpcRequest, JsonRpcResponse,
    encode, decode,
)
from backend.mcp.schema_mapper import to_mcp_tool, from_mcp_tool
from backend.mcp.server import McpServer
from backend.mcp.client import McpClient, McpError
from backend.mcp.remote_tool import RemoteTool
from backend.mcp.bridge import attach_remote

__all__ = [
    "JsonRpcError", "JsonRpcRequest", "JsonRpcResponse",
    "encode", "decode",
    "to_mcp_tool", "from_mcp_tool",
    "McpServer", "McpClient", "McpError",
    "RemoteTool", "attach_remote",
]
