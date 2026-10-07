"""已删除/已取消 job 的持久化登记。职责：跨重启记住用户删除的 job。
存储：sqlite（同 vector_db 目录），记录 tombstone。
独立插件，不修改原 registry 逻辑。"""
from __future__ import annotations
import os
import sqlite3
import threading
import time
from typing import List, Set


class DeletedRegistry:
    def __init__(self, db_path: str = None) -> None:
        path = db_path or os.path.join(
            os.getenv("VECTOR_DB_PATH", "./vector_db"), "deleted_jobs.db")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS deleted (
                job_id TEXT PRIMARY KEY,
                reason TEXT,
                deleted_at REAL
            )
        """)
        self._conn.commit()
        self._lock = threading.Lock()

    def mark(self, job_id: str, reason: str = "user_delete") -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO deleted VALUES (?, ?, ?)",
                (job_id, reason, time.time()))
            self._conn.commit()

    def is_deleted(self, job_id: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM deleted WHERE job_id=?", (job_id,))
        return cur.fetchone() is not None

    def all_ids(self) -> Set[str]:
        cur = self._conn.execute("SELECT job_id FROM deleted")
        return {r[0] for r in cur.fetchall()}

    def unmark(self, job_id: str) -> None:
        with self._lock:
            self._conn.execute(
                "DELETE FROM deleted WHERE job_id=?", (job_id,))
            self._conn.commit()


_instance = None
def get_deleted_registry() -> DeletedRegistry:
    global _instance
    if _instance is None:
        _instance = DeletedRegistry()
    return _instance


__all__ = ["DeletedRegistry", "get_deleted_registry"]
