"""Pipeline 持久化队列。职责：三阶段任务入队/出队/完成/失败/断电恢复。
存储：vector_db/pipeline_queue.db（SQLite + WAL）。不执行任务。
"""
from __future__ import annotations
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

STAGES = ("ocr", "embed", "vecwrite")
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

class PipelineQueue:
    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base = os.environ.get("VECTOR_DB_PATH", "vector_db")
            Path(base).mkdir(parents=True, exist_ok=True)
            db_path = os.path.join(base, "pipeline_queue.db")
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                payload TEXT DEFAULT '{}',
                error TEXT DEFAULT '',
                attempts INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stage_status "
            "ON pipeline_jobs(stage, status, priority DESC, id ASC)")
        self._conn.commit()
        self._lock = threading.Lock()

    def enqueue(self, job_id: str, stage: str, *,
                payload: Optional[dict] = None,
                priority: int = 0) -> int:
        if stage not in STAGES:
            raise ValueError(f"invalid stage: {stage}")
        if not job_id:
            raise ValueError("job_id required")
        now = time.time()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO pipeline_jobs "
                "(job_id, stage, status, priority, payload, "
                " created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (job_id, stage, STATUS_PENDING, int(priority),
                 json.dumps(payload or {}, ensure_ascii=False),
                 now, now))
            self._conn.commit()
            return int(cur.lastrowid or 0)

    def dequeue(self, stage: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, job_id, payload, attempts FROM pipeline_jobs "
                "WHERE stage=? AND status=? "
                "ORDER BY priority DESC, id ASC LIMIT 1",
                (stage, STATUS_PENDING)).fetchone()
            if not row:
                return None
            rid, job_id, payload, attempts = row
            self._conn.execute(
                "UPDATE pipeline_jobs SET status=?, updated_at=? WHERE id=?",
                (STATUS_RUNNING, time.time(), rid))
            self._conn.commit()
            try:
                pl = json.loads(payload or "{}")
            except Exception:
                pl = {}
            return {"id": int(rid), "job_id": str(job_id),
                    "payload": pl, "attempts": int(attempts)}

    def complete(self, row_id: int) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE pipeline_jobs SET status=?, updated_at=? WHERE id=?",
                (STATUS_DONE, time.time(), row_id))
            self._conn.commit()

    def fail(self, row_id: int, error: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE pipeline_jobs SET status=?, error=?, "
                "attempts=attempts+1, updated_at=? WHERE id=?",
                (STATUS_FAILED, str(error)[:500], time.time(), row_id))
            self._conn.commit()

    def recover_running(self) -> int:
        """断电重启：把 running 的任务重新标为 pending。"""
        with self._lock:
            cur = self._conn.execute(
                "UPDATE pipeline_jobs SET status=?, updated_at=? "
                "WHERE status=?",
                (STATUS_PENDING, time.time(), STATUS_RUNNING))
            self._conn.commit()
            return int(cur.rowcount or 0)

    def stats(self) -> Dict[str, int]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT stage, status, COUNT(*) FROM pipeline_jobs "
                "GROUP BY stage, status")
            out: Dict[str, int] = {}
            for stage, status, n in cur.fetchall():
                out[f"{stage}.{status}"] = int(n)
            return out

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

__all__ = ["PipelineQueue", "STAGES",
           "STATUS_PENDING", "STATUS_RUNNING", "STATUS_DONE", "STATUS_FAILED"]
