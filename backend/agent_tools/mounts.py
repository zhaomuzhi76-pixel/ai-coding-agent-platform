"""会话级工具挂载。职责：记录每个 session 启用哪些工具 + 白名单执行壳。
不注册（registry 管）、不执行实际逻辑（executor 管）、不组 prompt（chat_loop 管）。"""
from __future__ import annotations
from threading import RLock
from typing import Any, FrozenSet, Iterable, Optional

from backend.agent_tools.contracts import ToolCall, ToolResult
from backend.agent_tools.registry import ToolRegistry

DEFAULT_ALL = True

class SessionMounts:
    def __init__(self, *, default_all: bool = DEFAULT_ALL) -> None:
        self._data: dict[str, FrozenSet[str]] = {}
        self._lock = RLock()
        self._default_all = default_all

    def resolve(self, sid: str, registry: ToolRegistry) -> FrozenSet[str]:
        if not sid: raise ValueError("session_id required")
        with self._lock:
            if sid in self._data:
                return self._data[sid]
            if self._default_all:
                return frozenset(registry.names())
            return frozenset()

    def set(self, sid: str, names: Iterable[str],
            registry: Optional[ToolRegistry] = None) -> FrozenSet[str]:
        if not sid: raise ValueError("session_id required")
        valid = set(str(n) for n in names)
        if registry is not None:
            unknown = valid - set(registry.names())
            if unknown:
                raise ValueError(f"unknown tools: {sorted(unknown)}")
        fs = frozenset(valid)
        with self._lock:
            self._data[sid] = fs
        return fs

    def add(self, sid: str, names: Iterable[str],
            registry: ToolRegistry) -> FrozenSet[str]:
        return self.set(sid, self.resolve(sid, registry) | set(names), registry)

    def remove(self, sid: str, names: Iterable[str],
               registry: ToolRegistry) -> FrozenSet[str]:
        return self.set(sid, self.resolve(sid, registry) - set(names), registry)

    def clear_session(self, sid: str) -> None:
        with self._lock:
            self._data.pop(sid, None)

class WhitelistExecutor:
    """给 chat_loop 用的执行壳：只允许白名单内工具执行。"""
    def __init__(self, inner: Any, allow: FrozenSet[str]) -> None:
        self._inner = inner
        self._allow = allow

    def can_handle(self, name: str) -> bool:
        return name in self._allow and self._inner.can_handle(name)

    def execute(self, call: ToolCall) -> ToolResult:
        if call.name not in self._allow:
            return ToolResult(name=call.name, ok=False,
                              error=f"tool not enabled: {call.name}")
        return self._inner.execute(call)

__all__ = ["SessionMounts", "WhitelistExecutor", "DEFAULT_ALL"]
