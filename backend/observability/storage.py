"""Tracer SQLite storage — 跨进程共享。"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_DB_DIR = Path.home() / ".biancheng"
_DB_PATH = _DB_DIR / "metrics.db"


def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS spans (
                span_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                parent_id TEXT,
                status TEXT NOT NULL DEFAULT 'ok',
                duration_ms REAL NOT NULL DEFAULT 0.0,
                error TEXT NOT NULL DEFAULT '',
                attributes TEXT NOT NULL DEFAULT '{}',
                started_at REAL NOT NULL,
                ended_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_spans_started
                ON spans(started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_spans_name
                ON spans(name);
        """)


def insert_span(span: Dict[str, Any]) -> None:
    _ensure_schema()
    import json
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO spans("
            "span_id, name, parent_id, status, duration_ms, "
            "error, attributes, started_at, ended_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                span.get("span_id", ""), span.get("name", ""),
                span.get("parent_id"), span.get("status", "ok"),
                float(span.get("duration_ms", 0.0)),
                span.get("error", "")[:200],
                json.dumps(span.get("attributes", {})),
                float(span.get("started_at", 0.0)),
                float(span.get("ended_at", time.time())),
            ),
        )


def query_spans(
    since: Optional[float] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    _ensure_schema()
    import json
    sql = ("SELECT span_id, name, parent_id, status, duration_ms, "
           "error, attributes, started_at, ended_at FROM spans")
    params: List[Any] = []
    if since is not None:
        sql += " WHERE started_at >= ?"
        params.append(since)
    sql += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        try:
            attrs = json.loads(r[6])
        except Exception:
            attrs = {}
        out.append({
            "span_id": r[0], "name": r[1], "parent_id": r[2],
            "status": r[3], "duration_ms": r[4], "error": r[5],
            "attributes": attrs,
            "started_at": r[7], "ended_at": r[8],
        })
    return out


def reset_spans() -> None:
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM spans")


__all__ = ["insert_span", "query_spans", "reset_spans"]
