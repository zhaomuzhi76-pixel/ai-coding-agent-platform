"""User profile database schema（含 scope/workspace 迁移）。"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def init_schema(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace TEXT,
                category TEXT NOT NULL,
                signal TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence INTEGER NOT NULL DEFAULT 50,
                sample_count INTEGER NOT NULL DEFAULT 1,
                last_used_at REAL NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(category, key, value)
            );
            CREATE INDEX IF NOT EXISTS idx_pref_lookup
                ON preferences(category, confidence DESC);
        """)
        _migrate_scope(conn)


def _migrate_scope(conn: sqlite3.Connection) -> None:
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(preferences)")}
    except Exception:
        return
    if "scope" not in cols:
        conn.execute(
            "ALTER TABLE preferences ADD COLUMN scope TEXT NOT NULL DEFAULT 'global'"
        )
    if "workspace" not in cols:
        conn.execute(
            "ALTER TABLE preferences ADD COLUMN workspace TEXT NOT NULL DEFAULT ''"
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pref_scope "
        "ON preferences(scope, workspace, confidence DESC)"
    )


__all__ = ["init_schema"]
