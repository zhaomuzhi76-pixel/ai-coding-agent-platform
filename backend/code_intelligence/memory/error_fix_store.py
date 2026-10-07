from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class ErrorFixStore:
    """跨项目错误修复库（signature → fix_template）。"""

    VERSION = "1.0"
    _LOCK = threading.Lock()
    _INSTANCE: "ErrorFixStore | None" = None

    def __init__(self) -> None:
        root = Path.home() / ".biancheng" / "global"
        root.mkdir(parents=True, exist_ok=True)
        self.db_path = root / "global.db"
        self._init_schema()

    @classmethod
    def instance(cls) -> "ErrorFixStore":
        with cls._LOCK:
            if cls._INSTANCE is None:
                cls._INSTANCE = cls()
            return cls._INSTANCE

    def _init_schema(self) -> None:
        from backend.code_intelligence.memory._shared.schema import (
            init_error_fixes,
        )
        with sqlite3.connect(self.db_path) as conn:
            init_error_fixes(conn)

    def lookup(self, signature: str) -> dict[str, Any] | None:
        if not signature:
            return None
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, error_type, fix_kind, fix_text, "
                "fix_plan, success_count, fail_count "
                "FROM error_fixes WHERE signature=?",
                (signature,),
            ).fetchone()
            if not row:
                return None
            conn.execute(
                "UPDATE error_fixes SET last_used_at=? WHERE id=?",
                (time.time(), row[0]),
            )
            return {"id": row[0], "error_type": row[1],
                    "fix_kind": row[2], "fix_text": row[3],
                    "fix_plan": row[4],
                    "success_count": row[5], "fail_count": row[6]}

    def record_success(
        self, *, signature: str, error_type: str,
        error_message: str, fix_kind: str, fix_text: str,
        fix_plan: str = "", workspace: str = "",
    ) -> int:
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM error_fixes WHERE signature=?",
                (signature,),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE error_fixes SET success_count=success_count+1, "
                    "last_used_at=? WHERE id=?",
                    (now, row[0]),
                )
                return int(row[0])
            cur = conn.execute(
                "INSERT INTO error_fixes("
                "signature, error_type, error_message, "
                "fix_kind, fix_text, fix_plan, "
                "success_count, project_count, last_used_at, created_at) "
                "VALUES(?, ?, ?, ?, ?, ?, 1, 1, ?, ?)",
                (signature, error_type, error_message,
                 fix_kind, fix_text, fix_plan, now, now),
            )
            return int(cur.lastrowid)

    def record_failure(self, signature: str) -> None:
        if not signature:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE error_fixes SET fail_count=fail_count+1, "
                "last_used_at=? WHERE signature=?",
                (time.time(), signature),
            )

    def stats(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM error_fixes"
            ).fetchone()[0]
            high = conn.execute(
                "SELECT COUNT(*) FROM error_fixes WHERE success_count >= 3"
            ).fetchone()[0]
        return {"total": total, "high_confidence": high,
                "db_path": str(self.db_path)}

    def ready(self) -> bool:
        return self.db_path.exists()

    def dump(self) -> dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION,
                "ready": self.ready(), "stats": self.stats()}


__all__ = ["ErrorFixStore"]
