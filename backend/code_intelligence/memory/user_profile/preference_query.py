"""Query preferences and render context."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def top_preferences(
    db_path: Path,
    category: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        if category:
            rows = conn.execute(
                "SELECT category, key, value, confidence, sample_count "
                "FROM preferences WHERE category=? AND confidence>50 "
                "ORDER BY confidence DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT category, key, value, confidence, sample_count "
                "FROM preferences WHERE confidence>50 "
                "ORDER BY confidence DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [
        {"category": r[0], "key": r[1], "value": r[2],
         "confidence": r[3], "sample_count": r[4]}
        for r in rows
    ]


def render_context(db_path: Path, limit: int = 8) -> str:
    prefs = top_preferences(db_path, limit=limit)
    if not prefs:
        return ""
    lines = ["User preferences (learned from past accepts):"]
    for p in prefs:
        lines.append(
            f"- {p['category']}/{p['key']} = {p['value']!r} "
            f"(confidence {p['confidence']})"
        )
    return "\n".join(lines) + "\n"
