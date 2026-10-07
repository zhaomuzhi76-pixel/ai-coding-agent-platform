"""Record and distill observations."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict


def record_observation(
    db_path: Path,
    workspace: str,
    category: str,
    signal: str,
    payload: Dict[str, Any],
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO observations("
            "workspace, category, signal, payload, created_at) "
            "VALUES(?, ?, ?, ?, ?)",
            (workspace, category, signal,
             json.dumps(payload, ensure_ascii=False), time.time()),
        )


def distill_preference(
    db_path: Path,
    category: str,
    signal: str,
    payload: Dict[str, Any],
) -> None:
    key = payload.get("key") or signal
    value = payload.get("value")
    if not key or value is None:
        return
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT id, sample_count FROM preferences "
            "WHERE category=? AND key=? AND value=?",
            (category, key, str(value)),
        ).fetchone()
        now = time.time()
        if row:
            new_conf = min(100, 50 + (row[1] + 1) * 10)
            conn.execute(
                "UPDATE preferences SET "
                "confidence=?, sample_count=sample_count+1, "
                "last_used_at=? WHERE id=?",
                (new_conf, now, row[0]),
            )
        else:
            conn.execute(
                "INSERT INTO preferences("
                "category, key, value, confidence, "
                "sample_count, last_used_at, created_at) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                (category, key, str(value), 50, 1, now, now),
            )
