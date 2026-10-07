"""Part 1 of store.py."""
from __future__ import annotations

import json

import sqlite3

import time

from pathlib import Path

from typing import Any

from ..event import JobEvent

from ..record import JobRecord

from ..spec import JobSpec

from ..state import JobState

_DB_DIR = Path.home() / ".biancheng"

_DB_PATH = _DB_DIR / "metrics.db"

def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS finetune_jobs (
                job_id TEXT PRIMARY KEY,
                spec_json TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                started_at REAL NOT NULL DEFAULT 0,
                finished_at REAL NOT NULL DEFAULT 0,
                progress REAL NOT NULL DEFAULT 0,
                current_step INTEGER NOT NULL DEFAULT 0,
                total_steps INTEGER NOT NULL DEFAULT 0,
                loss REAL NOT NULL DEFAULT 0,
                saved_to TEXT NOT NULL DEFAULT '',
                error TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_ft_jobs_state
                ON finetune_jobs(state, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_ft_jobs_created
                ON finetune_jobs(created_at DESC);

            CREATE TABLE IF NOT EXISTS finetune_job_events (
                event_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_ft_events_job
                ON finetune_job_events(job_id, created_at ASC);
        """)

def save_job_record(record: JobRecord) -> None:
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO finetune_jobs("
            "job_id, spec_json, state, created_at, updated_at, "
            "started_at, finished_at, progress, current_step, total_steps, "
            "loss, saved_to, error, metadata_json) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.job_id,
                json.dumps(record.spec.to_dict(), ensure_ascii=False),
                record.state.value,
                float(record.created_at),
                float(record.updated_at),
                float(record.started_at),
                float(record.finished_at),
                float(record.progress),
                int(record.current_step),
                int(record.total_steps),
                float(record.loss),
                record.saved_to[:500],
                record.error[:500],
                json.dumps(record.metadata, ensure_ascii=False),
            ),
        )

def update_job_state(
    job_id: str, state: JobState, **fields: Any,
) -> bool:
    """更新状态 + 可选字段（progress/current_step/loss/saved_to/error 等）。"""
    if not isinstance(state, JobState):
        raise TypeError("state must JobState")
    _ensure_schema()
    updates = {"state": state.value, "updated_at": time.time()}
    for k in ("progress", "current_step", "total_steps", "loss",
              "saved_to", "error", "started_at", "finished_at"):
        if k in fields:
            updates[k] = fields[k]
    cols = ", ".join(f"{k} = ?" for k in updates)
    vals = list(updates.values()) + [job_id]
    with sqlite3.connect(_DB_PATH) as conn:
        cur = conn.execute(
            f"UPDATE finetune_jobs SET {cols} WHERE job_id = ?", vals,
        )
        return cur.rowcount > 0

def load_job_record(job_id: str) -> JobRecord | None:
    if not job_id or not job_id.strip():
        raise ValueError("job_id required")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        row = conn.execute(
            "SELECT job_id, spec_json, state, created_at, updated_at, "
            "started_at, finished_at, progress, current_step, total_steps, "
            "loss, saved_to, error, metadata_json "
            "FROM finetune_jobs WHERE job_id = ?",
            (job_id.strip(),),
        ).fetchone()
    if row is None:
        return None
    return JobRecord(
        job_id=row[0],
        spec=JobSpec.from_dict(json.loads(row[1])),
        state=JobState(row[2]),
        created_at=row[3],
        updated_at=row[4],
        started_at=row[5],
        finished_at=row[6],
        progress=row[7],
        current_step=row[8],
        total_steps=row[9],
        loss=row[10],
        saved_to=row[11],
        error=row[12],
        metadata=dict(json.loads(row[13] or "{}")),
    )
