"""RoutingStore: 用户执行配置持久化（SQLite）。"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from backend.platform.routing.models import UserRouting

_DB_DIR = Path.home() / ".biancheng"
_DB_PATH = _DB_DIR / "metrics.db"


def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_routing (
                user_id TEXT PRIMARY KEY,
                routing_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
        """)


class RoutingStore:
    VERSION = "1.0"

    def save(self, user_id: str, routing: UserRouting) -> None:
        if not user_id.strip():
            raise ValueError("user_id required")
        routing.validate()
        _ensure_schema()
        import time
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_routing("
                "user_id, routing_json, updated_at) "
                "VALUES(?, ?, ?)",
                (
                    user_id.strip(),
                    json.dumps(routing.to_dict(), ensure_ascii=False),
                    time.time(),
                ),
            )

    def load(self, user_id: str) -> UserRouting:
        if not user_id.strip():
            return UserRouting()
        _ensure_schema()
        with sqlite3.connect(_DB_PATH) as conn:
            row = conn.execute(
                "SELECT routing_json FROM user_routing WHERE user_id=?",
                (user_id.strip(),),
            ).fetchone()
        if not row:
            return UserRouting()
        try:
            return UserRouting.from_dict(json.loads(row[0]))
        except Exception:
            return UserRouting()

    def reset(self, user_id: str) -> None:
        _ensure_schema()
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                "DELETE FROM user_routing WHERE user_id=?",
                (user_id.strip(),),
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {"name": type(self).__name__, "version": self.VERSION}


__all__ = ["RoutingStore"]
