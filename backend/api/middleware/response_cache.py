"""响应缓存（LRU + TTL）。

职责：单一（缓存 get/put + 命中率）。
不做：限流、观测聚合、路由。
"""
from __future__ import annotations
import hashlib
import time
from collections import OrderedDict
from typing import Any, Optional


class ResponseCache:
    """LRU + TTL 双策略（进程内共享，线程内安全）。"""

    def __init__(self, max_size: int = 256, ttl_s: float = 300.0):
        if max_size < 1:
            raise ValueError("max_size >= 1")
        if ttl_s <= 0:
            raise ValueError("ttl_s > 0")
        self._max = max_size
        self._ttl = ttl_s
        self._store: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()
        self._hit = 0
        self._miss = 0
        self._evicted = 0
        self._expired = 0

    @staticmethod
    def key(query: str) -> str:
        return hashlib.sha256((query or "").encode("utf-8")).hexdigest()[:16]

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            self._miss += 1
            return None
        ts, value = entry
        if time.time() - ts > self._ttl:
            del self._store[key]
            self._expired += 1
            self._miss += 1
            return None
        self._store.move_to_end(key)
        self._hit += 1
        return value

    def put(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)
        self._store.move_to_end(key)
        while len(self._store) > self._max:
            self._store.popitem(last=False)
            self._evicted += 1

    def clear(self) -> None:
        self._store.clear()

    def snapshot(self) -> dict:
        total = self._hit + self._miss
        return {
            "max_size": self._max,
            "ttl_s": self._ttl,
            "size": len(self._store),
            "hit": self._hit,
            "miss": self._miss,
            "expired": self._expired,
            "evicted": self._evicted,
            "hit_rate": round(self._hit / total, 3) if total else 0.0,
        }
