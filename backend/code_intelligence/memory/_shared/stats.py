"""Row count helper."""
from __future__ import annotations

import sqlite3
from pathlib import Path


def count_rows(db_path: Path, table: str) -> int:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
