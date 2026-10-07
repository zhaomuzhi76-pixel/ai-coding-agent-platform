"""Cost SQLite storage — 跨进程共享。"""
from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_DB_DIR = Path.home() / ".biancheng"
_DB_PATH = _DB_DIR / "metrics.db"


def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cost_records (
                record_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT '',
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0.0,
                latency_ms REAL NOT NULL DEFAULT 0.0,
                success INTEGER NOT NULL DEFAULT 1,
                error TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cost_created
                ON cost_records(created_at DESC);
        """)


def insert_record(rec: Dict[str, Any]) -> None:
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cost_records("
            "record_id, provider, model, role, "
            "input_tokens, output_tokens, cost, latency_ms, "
            "success, error, created_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rec.get("record_id") or uuid.uuid4().hex[:12],
                rec["provider"], rec["model"], rec.get("role", ""),
                int(rec.get("input_tokens", 0)),
                int(rec.get("output_tokens", 0)),
                float(rec.get("cost", 0.0)),
                float(rec.get("latency_ms", 0.0)),
                1 if rec.get("success", True) else 0,
                rec.get("error", "")[:200],
                float(rec.get("created_at", time.time())),
            ),
        )


def query_records(
    since: Optional[float] = None,
    until: Optional[float] = None,
    limit: int = 20000,
) -> List[Dict[str, Any]]:
    _ensure_schema()
    sql = ("SELECT record_id, provider, model, role, "
           "input_tokens, output_tokens, cost, latency_ms, "
           "success, error, created_at FROM cost_records")
    clauses, params = [], []
    if since is not None:
        clauses.append("created_at >= ?"); params.append(since)
    if until is not None:
        clauses.append("created_at <= ?"); params.append(until)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        {"record_id": r[0], "provider": r[1], "model": r[2],
         "role": r[3], "input_tokens": r[4], "output_tokens": r[5],
         "cost": r[6], "latency_ms": r[7],
         "success": bool(r[8]), "error": r[9], "created_at": r[10]}
        for r in rows
    ]


def reset_records() -> None:
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM cost_records")


__all__ = ["insert_record", "query_records", "reset_records"]
