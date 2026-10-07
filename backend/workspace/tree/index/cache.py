"""TreeIndex: mtime-keyed 目录缓存。

契约：
  - key = (rel_path, dir_mtime_ns, dir_size)
  - value = entries list（沿用 list_children 返回结构）
  - LRU 上限（默认 512 目录）
  - 命中/未命中/失效 三种结果可统计

不负责：
  - 磁盘扫描（调用方传 entries）
  - 忽略过滤（filter 层管）
  - 分页（pagination 层管）
  - 持久化（内存缓存，进程重启即清）
"""
from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MtimeKey:
    path: str
    mtime_ns: int
    size: int


@dataclass(frozen=True, slots=True)
class IndexEntry:
    entries: tuple[dict, ...]
    cached_at: float


@dataclass
class IndexStats:
    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    evictions: int = 0

    def dump(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "invalidations": self.invalidations,
            "evictions": self.evictions,
            "total": self.hits + self.misses,
            "hit_rate": round(
                self.hits / max(1, self.hits + self.misses), 3
            ),
        }


class TreeIndex:
    VERSION = "1.0"

    def __init__(self, max_entries: int = 512) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        self.max_entries = int(max_entries)
        self._store: OrderedDict[str, IndexEntry] = OrderedDict()
        self._key: dict[str, MtimeKey] = {}
        self.stats = IndexStats()

    def get(
        self,
        path: str,
        mtime_ns: int,
        size: int,
    ) -> tuple[dict, ...] | None:
        """返回缓存的 entries；mtime/size 变了则失效并返回 None。"""
        cur = MtimeKey(path, int(mtime_ns), int(size))
        prev = self._key.get(path)
        if prev is None:
            self.stats.misses += 1
            return None
        if prev != cur:
            self.stats.invalidations += 1
            self._drop(path)
            return None
        entry = self._store.get(path)
        if entry is None:
            self.stats.misses += 1
            return None
        # LRU touch
        self._store.move_to_end(path)
        self.stats.hits += 1
        return entry.entries

    def put(
        self,
        path: str,
        mtime_ns: int,
        size: int,
        entries: list[dict],
    ) -> None:
        if not isinstance(entries, list):
            raise TypeError("entries must be list")
        frozen = tuple(dict(e) for e in entries)
        self._store[path] = IndexEntry(frozen, time.time())
        self._key[path] = MtimeKey(path, int(mtime_ns), int(size))
        self._store.move_to_end(path)
        self._evict_if_needed()

    def invalidate(self, path: str) -> None:
        self._drop(path)
        self.stats.invalidations += 1

    def clear(self) -> None:
        self._store.clear()
        self._key.clear()

    def size(self) -> int:
        return len(self._store)

    def ready(self) -> bool:
        return self.max_entries > 0

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "max_entries": self.max_entries,
            "size": self.size(),
            "stats": self.stats.dump(),
            "ready": self.ready(),
        }

    # ── 内部 ──
    def _drop(self, path: str) -> None:
        self._store.pop(path, None)
        self._key.pop(path, None)

    def _evict_if_needed(self) -> None:
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)
            # key 也需同步删
            if self._key:
                oldest = next(iter(self._key))
                self._key.pop(oldest, None)
            self.stats.evictions += 1


__all__ = ["TreeIndex", "IndexEntry", "MtimeKey", "IndexStats"]
