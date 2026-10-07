"""MCP method names + standard error codes."""
from __future__ import annotations

from backend.mcp.jsonrpc import JsonRpcError

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "backend-mcp-server"
SERVER_VERSION = "1.0.0"

METHOD_INITIALIZE = "initialize"
METHOD_TOOLS_LIST = "tools/list"
METHOD_TOOLS_CALL = "tools/call"
METHOD_PING = "ping"

# JSON-RPC 2.0 standard error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# MCP-specific
TOOL_NOT_FOUND = -32001
TOOL_EXECUTION_FAILED = -32002


def error(
    code: int, message: str, data=None,
) -> JsonRpcError:
    return JsonRpcError(code=code, message=message, data=data)


def method_not_found(method: str) -> JsonRpcError:
    return error(
        METHOD_NOT_FOUND, f"method not found: {method}",
    )


def invalid_params(reason: str) -> JsonRpcError:
    return error(INVALID_PARAMS, f"invalid params: {reason}")


def internal_error(reason: str) -> JsonRpcError:
    return error(INTERNAL_ERROR, f"internal error: {reason}")


def tool_not_found(name: str) -> JsonRpcError:
    return error(TOOL_NOT_FOUND, f"tool not found: {name}")


def tool_failed(name: str, reason: str) -> JsonRpcError:
    return error(
        TOOL_EXECUTION_FAILED,
        f"tool execution failed: {name}",
        {"reason": reason},
    )


SUPPORTED_METHODS = (
    METHOD_INITIALIZE,
    METHOD_TOOLS_LIST,
    METHOD_TOOLS_CALL,
    METHOD_PING,
)


__all__ = [
    "PROTOCOL_VERSION",
    "SERVER_NAME", "SERVER_VERSION",
    "METHOD_INITIALIZE", "METHOD_TOOLS_LIST",
    "METHOD_TOOLS_CALL", "METHOD_PING",
    "PARSE_ERROR", "INVALID_REQUEST",
    "METHOD_NOT_FOUND", "INVALID_PARAMS", "INTERNAL_ERROR",
    "TOOL_NOT_FOUND", "TOOL_EXECUTION_FAILED",
    "error", "method_not_found", "invalid_params",
    "internal_error", "tool_not_found", "tool_failed",
    "SUPPORTED_METHODS",
]
