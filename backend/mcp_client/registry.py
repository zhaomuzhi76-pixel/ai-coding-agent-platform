"""MCP Server 注册表。职责：服务器配置的 CRUD + JSON 持久化。
持久化位置：~/.cache/agent_mcp_servers.json（项目仓库外，遵守零磁盘纪律）。
不连服务器、不启进程、不注册工具。线程安全。
与 backend/mcp_client/contracts.py 边界：contracts 是纯数据；本层管存储。
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from threading import RLock
from typing import Iterable, Optional

from backend.mcp_client.contracts import ServerConfig

DEFAULT_PATH = os.path.expanduser("~/.cache/agent_mcp_servers.json")

class ServerRegistry:
    def __init__(self, path: str | None = None) -> None:
        self._path = Path(path or DEFAULT_PATH)
        self._items: dict[str, ServerConfig] = {}
        self._lock = RLock()
        self._loaded = False

    # ─── 持久化 ────────────────────────────────────────────
    def path(self) -> str:
        return str(self._path)

    def load(self) -> int:
        """从磁盘读入。文件不存在→空表；损坏→空表 + 备份。"""
        with self._lock:
            self._items = {}
            if not self._path.exists():
                self._loaded = True
                return 0
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                try:
                    self._path.rename(self._path.with_suffix(".corrupt"))
                except OSError:
                    pass
                self._loaded = True
                return 0
            servers = raw.get("servers") if isinstance(raw, dict) else None
            if not isinstance(servers, list):
                self._loaded = True
                return 0
            for item in servers:
                if not isinstance(item, dict):
                    continue
                try:
                    c = ServerConfig.from_dict(item)
                    self._items[c.id] = c
                except (KeyError, ValueError, TypeError):
                    continue
            self._loaded = True
            return len(self._items)

    def save(self) -> None:
        with self._lock:
            data = {"version": "1.0",
                    "servers": [c.to_dict() for c in self._items.values()]}
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            tmp.replace(self._path)

    # ─── CRUD ─────────────────────────────────────────────
    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def add(self, config: ServerConfig, *, save: bool = True) -> ServerConfig:
        self._ensure_loaded()
        with self._lock:
            self._items[config.id] = config
        if save:
            self.save()
        return config

    def upsert_many(self, configs: Iterable[ServerConfig], *,
                    save: bool = True) -> int:
        self._ensure_loaded()
        n = 0
        with self._lock:
            for c in configs:
                self._items[c.id] = c
                n += 1
        if save:
            self.save()
        return n

    def get(self, sid: str) -> Optional[ServerConfig]:
        self._ensure_loaded()
        return self._items.get(sid)

    def remove(self, sid: str, *, save: bool = True) -> bool:
        self._ensure_loaded()
        with self._lock:
            removed = self._items.pop(sid, None) is not None
        if removed and save:
            self.save()
        return removed

    def set_enabled(self, sid: str, enabled: bool, *,
                    save: bool = True) -> Optional[ServerConfig]:
        self._ensure_loaded()
        with self._lock:
            cur = self._items.get(sid)
            if cur is None:
                return None
            updated = ServerConfig(**{**cur.__dict__, "enabled": enabled})
            self._items[sid] = updated
        if save:
            self.save()
        return updated

    def all(self) -> list[ServerConfig]:
        self._ensure_loaded()
        return sorted(self._items.values(), key=lambda c: c.id)

    def enabled(self) -> list[ServerConfig]:
        return [c for c in self.all() if c.enabled]

    def count(self) -> int:
        self._ensure_loaded()
        return len(self._items)

_DEFAULT: Optional[ServerRegistry] = None

def get_default_registry() -> ServerRegistry:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = ServerRegistry()
    return _DEFAULT

def set_default_registry(reg: Optional[ServerRegistry]) -> None:
    global _DEFAULT
    _DEFAULT = reg

__all__ = ["ServerRegistry", "get_default_registry",
           "set_default_registry", "DEFAULT_PATH"]
