"""code_index 表结构（供 MemoryStore._init_schema 调用）。"""
from __future__ import annotations

import sqlite3

from backend.code_intelligence.memory._shared.schema import (
    init_code_index,
)

__all__ = ["create_index_schema", "init_code_index"]


def create_index_schema(conn: sqlite3.Connection) -> None:
    init_code_index(conn)


def index_load(conn: sqlite3.Connection, path: str) -> dict | None:
    row = conn.execute(
        "SELECT path, workspace, mtime, size, symbols, imports, updated_at "
        "FROM code_index WHERE path=?",
        (path,),
    ).fetchone()
    if row is None:
        return None
    return {
        "path": row[0], "workspace": row[1], "mtime": row[2],
        "size": row[3], "symbols": row[4], "imports": row[5],
        "updated_at": row[6],
    }


def index_upsert_many(conn: sqlite3.Connection, rows: list) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO code_index("
        "path, workspace, mtime, size, symbols, imports, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
