"""MCP 远端工具 Provider。职责：把 SessionManager 里的远端工具挂进 agent_tools.executor。
实现 ToolProviderProtocol（can_handle/execute）。远端是 async，故 execute 是 async def，
由 chat_loop 的 `if hasattr(result, "__await__")` 兼容分支 await 之。
不做连接（session_manager 管）、不做翻译（tool_adapter 管）、不做注册（registry 管）。"""
from __future__ import annotations
from typing import Any

from backend.agent_tools.contracts import ToolCall, ToolResult
from backend.mcp_client.session_manager import SessionManager

class McpToolProvider:
    def __init__(self, manager: SessionManager) -> None:
        if manager is None:
            raise ValueError("manager required")
        self._mgr = manager

    def can_handle(self, name: str) -> bool:
        if not isinstance(name, str) or not name:
            return False
        try:
            return self._mgr.resolve(name) is not None
        except Exception:
            return False

    async def execute(self, call: ToolCall) -> ToolResult:
        target = self._mgr.resolve(call.name)
        if target is None:
            return ToolResult(name=call.name, ok=False,
                              error=f"unknown mcp tool: {call.name}")
        try:
            raw = await self._mgr.call_tool(call.name, dict(call.arguments))
        except KeyError as e:
            return ToolResult(name=call.name, ok=False, error=str(e))
        except Exception as e:
            return ToolResult(name=call.name, ok=False,
                              error=f"{type(e).__name__}: {e}")
        is_error = bool(raw.get("isError", False)) if isinstance(raw, dict) else False
        content = raw.get("content", []) if isinstance(raw, dict) else raw
        text = self._extract_text(content)
        return ToolResult(name=call.name, ok=not is_error,
                          output=text,
                          error="" if not is_error else text,
                          meta={"server_id": target.server_id,
                                "raw_name": target.raw_name})

    @staticmethod
    def _extract_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return str(content)
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "\n".join(parts)

__all__ = ["McpToolProvider"]
