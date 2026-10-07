"""对话 trace 存储（SQLite，可审计/可回放）。
DB: ~/.cache/agent_knowledge/chat_trace.db
环境变量：
  RAG_CHAT_TRACE_ENABLED=1       总开关
  RAG_CHAT_TRACE_DB_PATH=        覆盖 DB 路径
  RAG_CHAT_TRACE_MAX_ROWS=50000  上限
"""
from __future__ import annotations
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_ENABLED = os.environ.get("RAG_CHAT_TRACE_ENABLED", "1") == "1"
_DB_OVERRIDE = os.environ.get("RAG_CHAT_TRACE_DB_PATH", "")
_MAX_ROWS = int(os.environ.get("RAG_CHAT_TRACE_MAX_ROWS", "50000"))


def _db_path() -> str:
    if _DB_OVERRIDE:
        return _DB_OVERRIDE
    base = os.path.expanduser("~/.cache/agent_knowledge")
    Path(base).mkdir(parents=True, exist_ok=True)
    return os.path.join(base, "chat_trace.db")


class ChatTrace:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db = db_path or _db_path()
        self._conn = sqlite3.connect(self._db, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                session_id TEXT NOT NULL,
                query TEXT NOT NULL,
                answer TEXT DEFAULT '',
                evidence_count INTEGER DEFAULT 0,
                confidence REAL DEFAULT 0,
                refused INTEGER DEFAULT 0,
                tool_calls INTEGER DEFAULT 0,
                steps INTEGER DEFAULT 0,
                latency_ms INTEGER DEFAULT 0,
                error TEXT DEFAULT '',
                meta_json TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ts ON traces(ts DESC)")
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sid ON traces(session_id)")
        self._conn.commit()
        self._lock = threading.Lock()

    def record(self, *, session_id: str, query: str, answer: str = "",
               evidence_count: int = 0, confidence: float = 0.0,
               refused: bool = False, tool_calls: int = 0, steps: int = 0,
               latency_ms: int = 0, error: str = "",
               meta: Optional[Dict[str, Any]] = None) -> int:
        if not _ENABLED:
            return 0
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO traces (ts, session_id, query, answer, "
                "evidence_count, confidence, refused, tool_calls, "
                "steps, latency_ms, error, meta_json) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (time.time(), session_id, query[:1000], answer[:2000],
                 int(evidence_count), float(confidence),
                 1 if refused else 0, int(tool_calls), int(steps),
                 int(latency_ms), (error or "")[:500],
                 json.dumps(meta or {}, ensure_ascii=False)))
            self._conn.commit()
            rid = int(cur.lastrowid or 0)
            # 裁剪
            n = self._conn.execute(
                "SELECT COUNT(*) FROM traces").fetchone()[0]
            if n > _MAX_ROWS:
                over = n - _MAX_ROWS
                self._conn.execute(
                    "DELETE FROM traces WHERE id IN "
                    "(SELECT id FROM traces ORDER BY id ASC LIMIT ?)",
                    (over,))
                self._conn.commit()
            return rid

    def list_recent(self, limit: int = 100,
                    session_id: Optional[str] = None) -> List[Dict]:
        with self._lock:
            if session_id:
                rows = self._conn.execute(
                    "SELECT id, ts, session_id, query, answer, "
                    "evidence_count, confidence, refused, tool_calls, "
                    "steps, latency_ms, error FROM traces "
                    "WHERE session_id=? ORDER BY ts DESC LIMIT ?",
                    (session_id, limit)).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT id, ts, session_id, query, answer, "
                    "evidence_count, confidence, refused, tool_calls, "
                    "steps, latency_ms, error FROM traces "
                    "ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
        return [{
            "id": r[0], "ts": r[1], "session_id": r[2], "query": r[3],
            "answer": r[4], "evidence_count": r[5], "confidence": r[6],
            "refused": bool(r[7]), "tool_calls": r[8], "steps": r[9],
            "latency_ms": r[10], "error": r[11],
        } for r in rows]

    def stats(self, hours: int = 24) -> Dict[str, Any]:
        since = time.time() - hours * 3600
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*), "
                "COALESCE(SUM(refused),0), "
                "COALESCE(AVG(latency_ms),0), "
                "COALESCE(AVG(confidence),0) "
                "FROM traces WHERE ts >= ?", (since,)).fetchone()
        return {"hours": hours, "count": int(row[0] or 0),
                "refused": int(row[1] or 0),
                "avg_latency_ms": round(float(row[2] or 0), 1),
                "avg_confidence": round(float(row[3] or 0), 4)}

    @property
    def db_path(self) -> str:
        return self._db

    def close(self) -> None:
        try: self._conn.close()
        except Exception: pass


_singleton: Optional[ChatTrace] = None
_guard = threading.Lock()


def get_trace() -> ChatTrace:
    global _singleton
    if _singleton is None:
        with _guard:
            if _singleton is None:
                _singleton = ChatTrace()
    return _singleton


__all__ = ["ChatTrace", "get_trace", "_ENABLED", "_MAX_ROWS"]
