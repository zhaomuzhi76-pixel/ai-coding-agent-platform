"""L5 · Shared Memory（跨 Agent 共享记忆 · 单一职责）。

职责：
  · 按 (session_id, namespace) 分区存储
  · LRU（max_size）+ TTL（ttl_s）
  · 支持 get/put/delete/list/clear

不做：持久化（上层负责）、检索、消息。
"""
from __future__ import annotations
import os
import time
from collections import OrderedDict
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple


def _key(session_id: str, namespace: str, k: str) -> Tuple[str, str, str]:
    return (session_id or "", namespace or "default", k or "")


class SharedMemory:
    """线程安全 LRU + TTL 共享记忆。"""

    def __init__(self, max_size: int = 1024, ttl_s: float = 1800.0) -> None:
        if max_size < 1:
            raise ValueError("max_size >= 1")
        if ttl_s <= 0:
            raise ValueError("ttl_s > 0")
        self._max = max_size
        self._ttl = ttl_s
        self._store: "OrderedDict[Tuple[str,str,str], Tuple[float,Any]]" = OrderedDict()
        self._lock = RLock()
        self._hits = 0
        self._miss = 0
        self._expired = 0

    def put(self, session_id: str, key: str, value: Any,
            namespace: str = "default") -> None:
        with self._lock:
            self._store[_key(session_id, namespace, key)] = (time.time(), value)
            self._store.move_to_end(_key(session_id, namespace, key))
            while len(self._store) > self._max:
                self._store.popitem(last=False)

    def get(self, session_id: str, key: str,
            namespace: str = "default") -> Optional[Any]:
        with self._lock:
            k = _key(session_id, namespace, key)
            entry = self._store.get(k)
            if entry is None:
                self._miss += 1
                return None
            ts, v = entry
            if time.time() - ts > self._ttl:
                del self._store[k]
                self._expired += 1
                self._miss += 1
                return None
            self._store.move_to_end(k)
            self._hits += 1
            return v

    def delete(self, session_id: str, key: str,
               namespace: str = "default") -> bool:
        with self._lock:
            return self._store.pop(
                _key(session_id, namespace, key), None) is not None

    def list_session(self, session_id: str,
                     namespace: Optional[str] = None) -> List[Tuple[str, Any]]:
        """列出某 session 的所有 (key, value)。"""
        with self._lock:
            out: List[Tuple[str, Any]] = []
            now = time.time()
            for (sid, ns, k), (ts, v) in list(self._store.items()):
                if sid != session_id:
                    continue
                if namespace is not None and ns != namespace:
                    continue
                if now - ts > self._ttl:
                    del self._store[(sid, ns, k)]
                    self._expired += 1
                    continue
                out.append((k, v))
            return out

    def clear(self, session_id: Optional[str] = None) -> int:
        with self._lock:
            if session_id is None:
                n = len(self._store); self._store.clear(); return n
            keys = [k for k in self._store if k[0] == session_id]
            for k in keys:
                del self._store[k]
            return len(keys)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._miss
            return {
                "size": len(self._store),
                "max_size": self._max,
                "ttl_s": self._ttl,
                "hits": self._hits,
                "miss": self._miss,
                "expired": self._expired,
                "hit_rate": round(self._hits / total, 3) if total else 0.0,
            }


_DEFAULT: Optional[SharedMemory] = None


def _make_backend() -> Any:
    """按 env RAG_MA_MEMORY_BACKEND 选后端（默认 memory）。"""
    be = os.environ.get("RAG_MA_MEMORY_BACKEND", "memory").strip().lower()
    if be == "sqlite":
        try:
            from backend.application.multi_agent.shared_memory_sqlite import (
                SharedMemorySQLite)
            return SharedMemorySQLite()
        except Exception:
            pass
    return SharedMemory()


def get_default_memory() -> Any:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = _make_backend()
    return _DEFAULT


__all__ = ["SharedMemory", "get_default_memory"]
