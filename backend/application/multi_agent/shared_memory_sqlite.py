"""Shared Memory · SQLite 落盘后端（与 SharedMemory 同接口）。

表：memory(session_id, namespace, key, value_json, ts)
LRU 按 ts 升序淘汰；TTL 在 get 时判定。
env: RAG_MA_MEMORY_BACKEND=sqlite 时激活。
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple


class SharedMemorySQLite:
    def __init__(self, path: str = "", max_size: int = 4096,
                 ttl_s: float = 1800.0) -> None:
        self._path = path or os.path.expanduser(
            "~/.cache/agent_shared_memory.db")
        self._max = max_size
        self._ttl = ttl_s
        self._lock = RLock()
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        self._init_schema()

    def _conn(self):
        conn = sqlite3.connect(self._path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    session_id TEXT NOT NULL,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    ts REAL NOT NULL,
                    PRIMARY KEY (session_id, namespace, key)
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_ts ON memory(ts)")

    def put(self, session_id: str, key: str, value: Any,
            namespace: str = "default") -> None:
        vj = json.dumps(value, ensure_ascii=False, default=str)
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO memory "
                "(session_id, namespace, key, value_json, ts) "
                "VALUES (?,?,?,?,?)",
                (session_id or "", namespace or "default",
                 key or "", vj, time.time()))
            self._evict_locked(c)

    def _evict_locked(self, c) -> None:
        cnt = c.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        if cnt <= self._max:
            return
        excess = cnt - self._max
        c.execute(
            "DELETE FROM memory WHERE rowid IN "
            "(SELECT rowid FROM memory ORDER BY ts ASC LIMIT ?)",
            (excess,))

    def get(self, session_id: str, key: str,
            namespace: str = "default") -> Optional[Any]:
        with self._lock, self._conn() as c:
            row = c.execute(
                "SELECT value_json, ts FROM memory "
                "WHERE session_id=? AND namespace=? AND key=?",
                (session_id or "", namespace or "default", key or "")
            ).fetchone()
            if not row:
                return None
            vj, ts = row
            if time.time() - ts > self._ttl:
                c.execute(
                    "DELETE FROM memory WHERE session_id=? AND "
                    "namespace=? AND key=?",
                    (session_id or "", namespace or "default", key or ""))
                return None
            try:
                return json.loads(vj)
            except Exception:
                return None

    def delete(self, session_id: str, key: str,
               namespace: str = "default") -> bool:
        with self._lock, self._conn() as c:
            cur = c.execute(
                "DELETE FROM memory WHERE session_id=? AND "
                "namespace=? AND key=?",
                (session_id or "", namespace or "default", key or ""))
            return cur.rowcount > 0

    def list_session(self, session_id: str,
                     namespace: Optional[str] = None
                     ) -> List[Tuple[str, Any]]:
        with self._lock, self._conn() as c:
            if namespace is None:
                # ★ 修正：单参数 SQL 必须用 tuple（加逗号）
                rows = c.execute(
                    "SELECT key, value_json, ts FROM memory "
                    "WHERE session_id=?",
                    (session_id or "",)
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT key, value_json, ts FROM memory "
                    "WHERE session_id=? AND namespace=?",
                    (session_id or "", namespace)).fetchall()
        out: List[Tuple[str, Any]] = []
        for k, vj, ts in rows:
            if time.time() - ts > self._ttl:
                continue
            try:
                out.append((k, json.loads(vj)))
            except Exception:
                continue
        return out

    def clear(self, session_id: Optional[str] = None) -> int:
        with self._lock, self._conn() as c:
            if session_id is None:
                cur = c.execute("DELETE FROM memory")
            else:
                cur = c.execute(
                    "DELETE FROM memory WHERE session_id=?",
                    (session_id,))
            return cur.rowcount

    def stats(self) -> Dict[str, Any]:
        with self._lock, self._conn() as c:
            cnt = c.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        return {"backend": "sqlite", "path": self._path,
                "size": cnt, "max_size": self._max, "ttl_s": self._ttl}


__all__ = ["SharedMemorySQLite"]
