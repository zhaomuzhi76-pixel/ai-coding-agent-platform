"""MCP SessionManager。职责：多 server 池化 + 状态快照 + 工具路由 + 重连。
不做持久化（registry 管）、不解析协议（session 管）、不注册到 agent_tools（executor_provider 管）。
只支持 stdio transport（HTTP 后续可加，接口不变）。"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Optional

from backend.mcp_client.contracts import (
    ServerConfig, ServerStatus, ServerTransport, ServerRuntimeState)
from backend.mcp_client.stdio_session import StdioSession

@dataclass(frozen=True)
class RouteTarget:
    server_id: str
    raw_name: str
    namespaced_name: str

class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, StdioSession] = {}
        self._states: dict[str, ServerRuntimeState] = {}
        self._tool_index: dict[str, RouteTarget] = {}
        self._lock = RLock()

    # ─── 生命周期 ─────────────────────────────────────────
    async def add(self, config: ServerConfig) -> ServerRuntimeState:
        if config.transport is not ServerTransport.STDIO:
            raise ValueError(f"暂不支持 {config.transport.value}")
        await self.remove(config.id, silent=True)

        sess = StdioSession(config)
        snap = await sess.start()
        state = ServerRuntimeState(
            server_id=config.id, status=snap.status,
            tool_count=len(snap.tools), error=snap.error,
            server_info=dict(snap.server_info),
        )
        with self._lock:
            self._sessions[config.id] = sess
            self._states[config.id] = state
            if snap.status is ServerStatus.ONLINE:
                for t in snap.tools:
                    self._tool_index[t.namespaced_name] = RouteTarget(
                        server_id=config.id, raw_name=t.raw_name,
                        namespaced_name=t.namespaced_name)
        return state

    async def remove(self, sid: str, *, silent: bool = False) -> bool:
        with self._lock:
            sess = self._sessions.pop(sid, None)
            self._states.pop(sid, None)
            for k in [k for k, v in self._tool_index.items()
                      if v.server_id == sid]:
                self._tool_index.pop(k, None)
        if sess is None:
            return False
        try:
            await sess.close()
        except Exception:  # silent-ok
            pass
        return True

    async def reconnect(self, config: ServerConfig) -> ServerRuntimeState:
        return await self.add(config)

    async def close_all(self) -> None:
        with self._lock:
            ids = list(self._sessions.keys())
        for sid in ids:
            await self.remove(sid, silent=True)

    # ─── 查询 ─────────────────────────────────────────────
    def state(self, sid: str) -> Optional[ServerRuntimeState]:
        with self._lock:
            return self._states.get(sid)

    def states(self) -> list[ServerRuntimeState]:
        with self._lock:
            return sorted(self._states.values(), key=lambda s: s.server_id)

    def tool_names(self) -> list[str]:
        with self._lock:
            return sorted(self._tool_index.keys())

    def resolve(self, namespaced_name: str) -> Optional[RouteTarget]:
        with self._lock:
            return self._tool_index.get(namespaced_name)

    def online_count(self) -> int:
        with self._lock:
            return sum(1 for s in self._states.values()
                       if s.status is ServerStatus.ONLINE)

    # ─── 调用 ─────────────────────────────────────────────
    async def call_tool(self, namespaced_name: str,
                        args: dict) -> dict:
        target = self.resolve(namespaced_name)
        if target is None:
            raise KeyError(f"unknown tool: {namespaced_name}")
        with self._lock:
            sess = self._sessions.get(target.server_id)
        if sess is None:
            raise RuntimeError(f"session gone: {target.server_id}")
        return await sess.call_tool(target.raw_name, dict(args))

_DEFAULT: Optional[SessionManager] = None

def get_default_manager() -> SessionManager:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = SessionManager()
    return _DEFAULT

def set_default_manager(mgr: Optional[SessionManager]) -> None:
    global _DEFAULT
    _DEFAULT = mgr

__all__ = ["SessionManager", "RouteTarget",
           "get_default_manager", "set_default_manager"]
