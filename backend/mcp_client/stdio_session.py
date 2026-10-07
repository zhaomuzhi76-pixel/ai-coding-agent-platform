"""MCP Stdio 会话。职责：一个 ServerConfig → 起子进程 → initialize + tools/list。
复用 backend/mcp/transport/stdio.py + backend/mcp/client.py，不改它们。
不注册工具、不做重连、不管生命周期（session_manager 管）。"""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.mcp.client import McpClient, McpError
from backend.mcp.transport.stdio import StdioClientTransport
from backend.mcp_client.contracts import (
    ServerConfig, ServerStatus, ServerTransport, RemoteToolDesc)

DEFAULT_CONNECT_TIMEOUT = 60.0  # npx 首次拉包可能 30s+

@dataclass(frozen=True)
class SessionSnapshot:
    server_id: str
    status: ServerStatus
    server_info: dict = field(default_factory=dict)
    tools: tuple = ()
    error: str = ""
    elapsed_ms: int = 0

class StdioSession:
    """单次 stdio 会话。start() → initialize + tools/list；close() 关子进程。"""
    def __init__(self, config: ServerConfig, *,
                 timeout: float = DEFAULT_CONNECT_TIMEOUT) -> None:
        if config.transport is not ServerTransport.STDIO:
            raise ValueError("StdioSession 只支持 stdio transport")
        if not config.command.strip():
            raise ValueError("stdio 必须提供 command")
        self._cfg = config
        self._timeout = timeout
        self._transport: Optional[StdioClientTransport] = None
        self._client: Optional[McpClient] = None
        self._tools: tuple = ()
        self._server_info: dict = {}

    @property
    def server_id(self) -> str:
        return self._cfg.id

    @property
    def tools(self) -> tuple:
        return self._tools

    @property
    def server_info(self) -> dict:
        return dict(self._server_info)

    def ready(self) -> bool:
        return self._client is not None and self._client.ready()

    async def start(self) -> SessionSnapshot:
        t0 = time.time()
        self._transport = StdioClientTransport(
            command=self._cfg.command,
            args=list(self._cfg.args),
            env=dict(self._cfg.env) or None,
        )
        try:
            await asyncio.wait_for(self._transport.start(),
                                   timeout=self._timeout)
        except FileNotFoundError as e:
            return self._snap(ServerStatus.ERROR, t0, error=f"命令不存在: {e}")
        except asyncio.TimeoutError:
            return self._snap(ServerStatus.ERROR, t0, error="启动子进程超时")
        except Exception as e:
            return self._snap(ServerStatus.ERROR, t0,
                              error=f"start: {type(e).__name__}: {e}")

        self._client = McpClient(self._transport)
        try:
            info = await asyncio.wait_for(self._client.initialize(),
                                          timeout=self._timeout)
        except asyncio.TimeoutError:
            await self.close()
            return self._snap(ServerStatus.ERROR, t0, error="initialize 超时")
        except Exception as e:
            await self.close()
            return self._snap(ServerStatus.ERROR, t0,
                              error=f"initialize: {type(e).__name__}: {e}")
        if isinstance(info, dict):
            si = info.get("serverInfo")
            self._server_info = dict(si) if isinstance(si, dict) else {}

        try:
            raw_tools = await asyncio.wait_for(self._client.list_tools(),
                                               timeout=self._timeout)
        except asyncio.TimeoutError:
            await self.close()
            return self._snap(ServerStatus.ERROR, t0, error="tools/list 超时")
        except McpError as e:
            await self.close()
            return self._snap(ServerStatus.ERROR, t0, error=f"tools/list: {e}")
        except Exception as e:
            await self.close()
            return self._snap(ServerStatus.ERROR, t0,
                              error=f"tools/list: {type(e).__name__}: {e}")

        self._tools = tuple(self._to_desc(r) for r in raw_tools
                            if isinstance(r, dict))
        return self._snap(ServerStatus.ONLINE, t0)

    async def call_tool(self, raw_name: str, args: dict) -> dict:
        if self._client is None:
            raise RuntimeError("session not started")
        return await self._client.call_tool(raw_name, dict(args))

    async def close(self) -> None:
        if self._transport is not None:
            try:
                await self._transport.close()
            except Exception:  # silent-ok
                pass
        self._transport = None
        self._client = None

    def _to_desc(self, raw: dict) -> RemoteToolDesc:
        raw_name = str(raw.get("name", "")).strip()
        ns = self._cfg.namespace.strip() or "mcp"
        return RemoteToolDesc(
            server_id=self._cfg.id,
            raw_name=raw_name,
            namespaced_name=f"{ns}.{raw_name}",
            description=str(raw.get("description", "")),
            input_schema=raw.get("inputSchema") or {},
        )

    def _snap(self, status: ServerStatus, t0: float, *,
              error: str = "") -> SessionSnapshot:
        return SessionSnapshot(
            server_id=self._cfg.id, status=status,
            server_info=dict(self._server_info), tools=self._tools,
            error=error, elapsed_ms=int((time.time() - t0) * 1000))

__all__ = ["StdioSession", "SessionSnapshot", "DEFAULT_CONNECT_TIMEOUT"]
