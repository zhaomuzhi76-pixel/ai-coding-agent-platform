"""MCP Client 契约。职责：只描述"要连的 MCP server"与"拉到的远端工具"。
不连、不启进程、不注册工具、不持久化。
与 backend/mcp/* 边界：那层是协议实现；本层是"配置 + 状态"的纯数据。"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

class ServerTransport(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"

class ServerStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ONLINE = "online"
    ERROR = "error"

def _freeze(m: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(m))

@dataclass(frozen=True)
class ServerConfig:
    """一个 MCP server 的连接配置。id 为稳定主键（用户自定义）。"""
    id: str
    name: str
    transport: ServerTransport
    # stdio 专属
    command: str = ""
    args: Tuple[str, ...] = ()
    env: Mapping[str, str] = field(default_factory=dict)
    # http/sse 专属
    url: str = ""
    # 通用
    enabled: bool = True
    namespace: str = "mcp"       # 工具名前缀
    include: Tuple[str, ...] = ()  # 白名单（空 = 全部）
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "env", _freeze(self.env))
        object.__setattr__(self, "meta", _freeze(self.meta))
        if not self.id.strip(): raise ValueError("ServerConfig.id required")
        if not self.name.strip(): raise ValueError("ServerConfig.name required")
        if not isinstance(self.args, tuple):
            raise TypeError("args must be tuple")
        if not isinstance(self.include, tuple):
            raise TypeError("include must be tuple")
        t = self.transport
        if t is ServerTransport.STDIO and not self.command.strip():
            raise ValueError("stdio transport requires command")
        if t in (ServerTransport.HTTP, ServerTransport.SSE) and not self.url.strip():
            raise ValueError(f"{t.value} transport requires url")

    def to_dict(self) -> dict:
        d = {
            "id": self.id, "name": self.name,
            "transport": self.transport.value,
            "enabled": self.enabled, "namespace": self.namespace,
            "include": list(self.include), "meta": dict(self.meta),
        }
        if self.transport is ServerTransport.STDIO:
            d["command"] = self.command
            d["args"] = list(self.args)
            d["env"] = dict(self.env)
        else:
            d["url"] = self.url
        return d

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ServerConfig":
        return cls(
            id=str(raw["id"]), name=str(raw["name"]),
            transport=ServerTransport(str(raw["transport"])),
            command=str(raw.get("command", "")),
            args=tuple(str(x) for x in (raw.get("args") or [])),
            env={str(k): str(v) for k, v in (raw.get("env") or {}).items()},
            url=str(raw.get("url", "")),
            enabled=bool(raw.get("enabled", True)),
            namespace=str(raw.get("namespace", "mcp")),
            include=tuple(str(x) for x in (raw.get("include") or [])),
            meta=dict(raw.get("meta") or {}),
        )

@dataclass(frozen=True)
class RemoteToolDesc:
    """MCP server 返回的工具描述（tools/list 的原始字段精简版）。"""
    server_id: str
    raw_name: str
    namespaced_name: str
    description: str
    input_schema: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_schema", _freeze(self.input_schema))
        if not self.raw_name.strip(): raise ValueError("RemoteToolDesc.raw_name required")
        if not self.namespaced_name.strip():
            raise ValueError("RemoteToolDesc.namespaced_name required")

@dataclass(frozen=True)
class ServerRuntimeState:
    """运行时状态快照（不落盘）。"""
    server_id: str
    status: ServerStatus = ServerStatus.DISCONNECTED
    tool_count: int = 0
    error: str = ""
    started_at: float = 0.0
    server_info: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "server_info", _freeze(self.server_info))

    def to_dict(self) -> dict:
        return {
            "server_id": self.server_id,
            "status": self.status.value,
            "tool_count": self.tool_count,
            "error": self.error,
            "started_at": self.started_at,
            "server_info": dict(self.server_info),
        }

__all__ = ["ServerTransport", "ServerStatus", "ServerConfig",
           "RemoteToolDesc", "ServerRuntimeState"]
