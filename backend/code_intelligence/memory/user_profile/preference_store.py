"""Reinforce / weaken / decay preferences."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from backend.code_intelligence.memory.user_profile.contract import (
    DECAY_DAYS,
)


def reinforce(
    db_path: Path, category: str, key: str, delta: int = 5,
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE preferences SET "
            "confidence=MIN(100, confidence + ?), "
            "sample_count=sample_count+1, "
            "last_used_at=? "
            "WHERE category=? AND key=?",
            (delta, time.time(), category, key),
        )


def weaken(
    db_path: Path, category: str, key: str, delta: int = 10,
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE preferences SET "
            "confidence=MAX(0, confidence - ?), "
            "last_used_at=? "
            "WHERE category=? AND key=?",
            (delta, time.time(), category, key),
        )


def decay_stale(db_path: Path) -> int:
    now = time.time()
    cutoff = now - 7 * 86400
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, confidence, last_used_at FROM preferences "
            "WHERE last_used_at < ?",
            (cutoff,),
        ).fetchall()
        n = 0
        for r in rows:
            days = (now - r[2]) / 86400.0
            decayed = max(
                0,
                int(r[1] * (0.5 ** (days / DECAY_DAYS))),
            )
            conn.execute(
                "UPDATE preferences SET confidence=? WHERE id=?",
                (decayed, r[0]),
            )
            n += 1
        return n
