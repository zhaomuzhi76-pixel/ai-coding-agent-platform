"""SQLite schema helpers shared by memory stores."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def open_db(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


@contextmanager
def with_cursor(db_path: Path) -> Iterator[sqlite3.Cursor]:
    conn = sqlite3.connect(db_path)
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def init_rules_patches(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace TEXT NOT NULL,
            rule TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'user',
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS patches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace TEXT NOT NULL,
            task TEXT NOT NULL,
            plan TEXT,
            kind TEXT NOT NULL,
            text TEXT NOT NULL,
            accepted INTEGER NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 1,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_patches_task
            ON patches(workspace, task);
    """)


def init_code_index(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS code_index (
            path TEXT NOT NULL PRIMARY KEY,
            workspace TEXT NOT NULL,
            mtime REAL NOT NULL,
            size INTEGER NOT NULL,
            symbols TEXT NOT NULL,
            imports TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    """)


def init_skills(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signature TEXT NOT NULL UNIQUE,
            task_pattern TEXT NOT NULL,
            plan_template TEXT NOT NULL,
            kind TEXT NOT NULL,
            text_template TEXT NOT NULL,
            success_count INTEGER NOT NULL DEFAULT 1,
            project_count INTEGER NOT NULL DEFAULT 1,
            last_used_at REAL NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_skill_success
            ON skills(success_count DESC);
    """)


def init_error_fixes(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS error_fixes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signature TEXT NOT NULL UNIQUE,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            fix_kind TEXT NOT NULL,
            fix_text TEXT NOT NULL,
            fix_plan TEXT NOT NULL DEFAULT '',
            success_count INTEGER NOT NULL DEFAULT 1,
            fail_count INTEGER NOT NULL DEFAULT 0,
            project_count INTEGER NOT NULL DEFAULT 1,
            last_used_at REAL NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_err_sig
            ON error_fixes(signature, success_count DESC);
    """)
