"""工具统一执行器。职责：组合多个 provider，按工具名路由到能处理的 provider。
不做协议转换（mcp_bridge 管）、不注册（registry 管）、不调 LLM（agent_loop 管）。"""
from __future__ import annotations
from typing import Any, List, Optional, Protocol, Sequence

from backend.agent_tools.contracts import ToolCall, ToolResult

class ToolProviderProtocol(Protocol):
    def can_handle(self, name: str) -> bool: ...
    def execute(self, call: ToolCall) -> ToolResult: ...

class ToolExecutor:
    def __init__(self, providers: Sequence[Any] = ()) -> None:
        # 允许空：bridge 场景下可能先建 executor 后 add_provider
        self._providers: List[Any] = list(providers)

    def add_provider(self, provider: Any) -> None:
        if not callable(getattr(provider, "can_handle", None)):
            raise TypeError("provider 缺 can_handle()")
        if not callable(getattr(provider, "execute", None)):
            raise TypeError("provider 缺 execute()")
        self._providers.append(provider)

    def can_handle(self, name: str) -> bool:
        return self._find(name) is not None

    def execute(self, call: ToolCall) -> ToolResult:
        if not isinstance(call, ToolCall):
            raise TypeError("call must ToolCall")
        p = self._find(call.name)
        if p is None:
            return ToolResult(name=call.name, ok=False,
                              error=f"no provider handles: {call.name}")
        try:
            r = p.execute(call)
            # async provider 返回 coroutine → 透传，让上层 await
            if hasattr(r, "__await__"):
                return r
            if not isinstance(r, ToolResult):
                return ToolResult(name=call.name, ok=False,
                                  error=f"provider returned {type(r).__name__}, want ToolResult")
            return r
        except Exception as e:
            return ToolResult(name=call.name, ok=False,
                              error=f"{type(e).__name__}: {e}")

    def providers(self) -> list:
        return list(self._providers)

    def _find(self, name: str) -> Optional[Any]:
        for p in self._providers:
            try:
                if p.can_handle(name):
                    return p
            except Exception:
                continue
        return None

def make_executor(providers: Sequence[Any]) -> ToolExecutor:
    return ToolExecutor(providers)

__all__ = ["ToolExecutor", "make_executor", "ToolProviderProtocol"]
