"""工具注册中心。职责：注册/列举/按分类与领域过滤。
不执行工具、不调 LLM、不持状态。单例通过 get_default_registry()。"""
from __future__ import annotations
from threading import RLock
from typing import Iterable, Optional

from backend.agent_tools.contracts import (
    ToolCategory, ToolDescriptor, ToolDomain)

class ToolRegistry:
    def __init__(self) -> None:
        self._items: dict[str, ToolDescriptor] = {}
        self._lock = RLock()

    def register(self, d: ToolDescriptor) -> ToolDescriptor:
        with self._lock:
            self._items[d.name] = d
            return d

    def register_many(self, ds: Iterable[ToolDescriptor]) -> int:
        n = 0
        for d in ds:
            self.register(d); n += 1
        return n

    def get(self, name: str) -> Optional[ToolDescriptor]:
        return self._items.get(name)

    def all(self) -> list[ToolDescriptor]:
        return sorted(self._items.values(), key=lambda d: d.name)

    def by_category(self, cat: ToolCategory) -> list[ToolDescriptor]:
        return [d for d in self.all() if d.category == cat]

    def by_domain(self, dom: ToolDomain) -> list[ToolDescriptor]:
        return [d for d in self.all() if d.domain == dom]

    def by_server(self, server: str) -> list[ToolDescriptor]:
        return [d for d in self.all() if d.server == server]

    def filter(self, *, category: Optional[ToolCategory] = None,
               domain: Optional[ToolDomain] = None,
               server: Optional[str] = None) -> list[ToolDescriptor]:
        out = self.all()
        if category is not None: out = [d for d in out if d.category == category]
        if domain is not None:   out = [d for d in out if d.domain == domain]
        if server is not None:   out = [d for d in out if d.server == server]
        return out

    def names(self) -> list[str]:
        return [d.name for d in self.all()]

    def unregister(self, name: str) -> bool:
        with self._lock:
            return self._items.pop(name, None) is not None

    def unregister_by_server(self, server: str) -> int:
        with self._lock:
            names = [k for k, v in self._items.items() if v.server == server]
            for n in names:
                self._items.pop(n, None)
            return len(names)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def count(self) -> int:
        return len(self._items)

_DEFAULT: Optional[ToolRegistry] = None

def get_default_registry() -> ToolRegistry:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = ToolRegistry()
    return _DEFAULT

__all__ = ["ToolRegistry", "get_default_registry"]
