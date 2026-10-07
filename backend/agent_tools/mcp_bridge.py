"""Agent 工具 ↔ MCP JSON-RPC 协议桥。
职责：把 MCP tools/list、tools/call 请求转成 ToolDescriptor / ToolCall，
调用 ToolExecutor 拿 ToolResult，再编回 MCP 响应。
不做执行、不注册、不改 backend/mcp/*。"""
from __future__ import annotations
from typing import Any, Mapping, Optional

from backend.agent_tools.contracts import ToolCall, ToolDescriptor
from backend.agent_tools.executor import ToolExecutor
from backend.agent_tools.registry import ToolRegistry

def _schema_for(d: ToolDescriptor) -> dict:
    return {
        "name": d.name,
        "description": d.description,
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索查询（RAG）"},
                "limit": {"type": "integer", "description": "返回条数（RAG）"},
                "term": {"type": "string", "description": "术语（DOMAIN lookup）"},
                "keyword": {"type": "string", "description": "关键词（DOMAIN search）"},
                "args": {"type": "object", "description": "透传参数"},
            },
            "required": [],
        },
        "x-category": d.category.value,
        "x-domain": d.domain.value,
        "x-server": d.server,
    }

class McpToolBridge:
    VERSION = "1.0"
    def __init__(self, registry: ToolRegistry, executor: ToolExecutor) -> None:
        self._reg = registry
        self._exe = executor

    def initialize(self) -> dict:
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "agent-tools-bridge", "version": self.VERSION},
            "capabilities": {"tools": {"listChanged": False}},
        }

    def tools_list(self) -> dict:
        return {"tools": [_schema_for(d) for d in self._reg.all()]}

    def tools_call(self, params: Mapping[str, Any]) -> dict:
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            return self._err("invalid_params", "name required")
        args = params.get("arguments") or {}
        if not isinstance(args, Mapping):
            return self._err("invalid_params", "arguments must object")
        if self._reg.get(name) is None:
            return self._err("tool_not_found", name)
        call = ToolCall(name=name, arguments=args)
        result = self._exe.execute(call)
        return {
            "content": [{"type": "text", "text": result.output or ""}],
            "isError": not result.ok,
            "tool": name,
            "meta": dict(result.meta),
        }

    @staticmethod
    def _err(code: str, msg: str) -> dict:
        return {"error": {"code": code, "message": msg}}

def build_bridge(registry: ToolRegistry,
                 executor: Optional[ToolExecutor] = None) -> McpToolBridge:
    if executor is None:
        executor = ToolExecutor(providers=())
    return McpToolBridge(registry, executor)

__all__ = ["McpToolBridge", "build_bridge"]
