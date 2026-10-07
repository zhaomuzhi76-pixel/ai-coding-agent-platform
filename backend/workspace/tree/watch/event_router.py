"""WatcherRegistry: 全局 watcher 池 + 按 root 分组订阅。

契约：
    - subscribe_root(root, callback) → 返回 unsubscribe 协程
    - 同一 root 多个订阅者共享 1 个 TreeWatcher（引用计数）
    - 订阅者归零 → watcher 自动 stop 并清出池
    - 进程内单例 get_registry()

不负责：
    - 磁盘扫描（TreeWatcher 管）
    - WS 传输（ws_tree 管）
    - 事件持久化
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
from pathlib import Path
from typing import Awaitable, Callable

from .watcher import TreeWatcher, WatchEvent

Callback = Callable[[list[WatchEvent]], Awaitable[None]]
Unsubscribe = Callable[[], Awaitable[None]]


class WatcherRegistry:
    VERSION = "2.0"

    def __init__(self) -> None:
        self._by_root: dict[str, TreeWatcher] = {}
        self._subs: dict[str, list[Callback]] = {}
        self._lock = asyncio.Lock()

    async def subscribe_root(
        self,
        root: Path,
        callback: Callback,
        interval_sec: float = 2.0,
    ) -> Unsubscribe:
        if not isinstance(root, Path):
            raise TypeError("root must be Path")
        if not callable(callback):
            raise TypeError("callback must be callable")
        key = str(root)

        async with self._lock:
            subs = self._subs.setdefault(key, [])
            subs.append(callback)
            if key not in self._by_root:
                w = TreeWatcher(root, interval_sec=interval_sec)
                w.register("")
                self._by_root[key] = w
                await w.start(on_events=self._make_broadcaster(key))

        async def _unsub() -> None:
            async with self._lock:
                subs = self._subs.get(key)
                if subs is not None:
                    try:
                        subs.remove(callback)
                    except ValueError:
                        pass
                    if not subs:
                        self._subs.pop(key, None)
                        w = self._by_root.pop(key, None)
                        if w is not None:
                            await w.stop()

        return _unsub

    def _make_broadcaster(self, key: str) -> Callback:
        async def _broadcast(events: list[WatchEvent]) -> None:
            if not events:
                return
            for cb in list(self._subs.get(key, [])):
                try:
                    await cb(events)
                except Exception as e:
                    swallow("workspace.tree.watch.event_router:80", e)
        return _broadcast

    async def shutdown_all(self) -> None:
        async with self._lock:
            watchers = list(self._by_root.values())
            self._by_root.clear()
            self._subs.clear()
        for w in watchers:
            try:
                await w.stop()
            except Exception as e:
                swallow("workspace.tree.watch.event_router:92", e)

    def stats(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "roots": list(self._by_root.keys()),
            "watchers": len(self._by_root),
            "subscribers_by_root": {k: len(v) for k, v in self._subs.items()},
        }

    def dump(self) -> dict:
        return self.stats()


# ── 进程内单例 ──
_registry: WatcherRegistry | None = None
_registry_lock = asyncio.Lock()


def get_registry() -> WatcherRegistry:
    global _registry
    if _registry is None:
        _registry = WatcherRegistry()
    return _registry


async def shutdown_registry() -> None:
    global _registry
    if _registry is not None:
        await _registry.shutdown_all()
        _registry = None


__all__ = [
    "WatcherRegistry",
    "get_registry",
    "shutdown_registry",
]
