"""L2 提案持久化 —— sqlite 存储（跨进程/重启不丢）。

不重复职责：只做 CRUD；提案数据结构由 proposal.py 定；
会话上下文由 platform.py 管；HTTP 由 binding 层管。
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_DB = Path.home() / ".biancheng" / "global" / "platform_proposals.db"
_LOCK = threading.RLock()


def _init() -> None:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS proposals (
                proposal_id TEXT PRIMARY KEY,
                session_id TEXT DEFAULT '',
                workspace TEXT DEFAULT '',
                model TEXT DEFAULT '',
                user_id TEXT DEFAULT '',
                status TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_status_upd
                ON proposals(status, updated_at DESC);
        """)


def save(p: dict[str, Any], *, session_id: str = "",
         workspace: str = "", model: str = "", user_id: str = "") -> None:
    _init()
    pid = str(p.get("proposal_id") or "")
    if not pid:
        return
    now = time.time()
    with _LOCK, sqlite3.connect(_DB) as conn:
        conn.execute("""
            INSERT INTO proposals(proposal_id, session_id, workspace, model,
                user_id, status, data_json, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(proposal_id) DO UPDATE SET
                status=excluded.status,
                data_json=excluded.data_json,
                updated_at=excluded.updated_at
        """, (pid, session_id, workspace, model, user_id,
              str(p.get("status") or ""),
              json.dumps(p, ensure_ascii=False, default=str),
              float(p.get("created_at") or now), now))


def get(proposal_id: str) -> dict[str, Any] | None:
    _init()
    with _LOCK, sqlite3.connect(_DB) as conn:
        row = conn.execute(
            "SELECT data_json FROM proposals WHERE proposal_id=?",
            (proposal_id,)).fetchone()
    return json.loads(row[0]) if row else None


def list_all(*, status: str = "", limit: int = 100,
             user_id: str = "") -> list[dict[str, Any]]:
    _init()
    sql = "SELECT data_json FROM proposals"
    cond, args = [], []
    if status:
        cond.append("status=?"); args.append(status)
    if user_id:
        cond.append("user_id=?"); args.append(user_id)
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    args.append(limit)
    with _LOCK, sqlite3.connect(_DB) as conn:
        rows = conn.execute(sql, args).fetchall()
    return [json.loads(r[0]) for r in rows]


def delete(proposal_id: str) -> bool:
    _init()
    with _LOCK, sqlite3.connect(_DB) as conn:
        cur = conn.execute(
            "DELETE FROM proposals WHERE proposal_id=?", (proposal_id,))
    return cur.rowcount > 0


__all__ = ["save", "get", "list_all", "delete"]
