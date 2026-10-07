"""Part 2 of store.py."""
from __future__ import annotations
from .part1 import (Any, JobEvent, JobRecord, JobState, _DB_PATH, json, sqlite3,)  # noqa
from .part1 import _ensure_schema  # noqa
from .part1 import load_job_record  # noqa
from .part1 import save_job_record  # noqa
from .part1 import update_job_state  # noqa

def list_job_records(
    state: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    _ensure_schema()
    sql = ("SELECT job_id, spec_json, state, created_at, updated_at, "
           "started_at, finished_at, progress, current_step, total_steps, "
           "loss, saved_to, error, metadata_json FROM finetune_jobs")
    params: list = []
    if state and state.strip():
        sql += " WHERE state = ?"
        params.append(state.strip())
    sql += " ORDER BY created_at DESC, rowid DESC LIMIT ?"
    params.append(int(limit))
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(sql, params).fetchall()
    out = []
    for row in rows:
        spec = json.loads(row[1]) if row[1] else {}
        rec = {
            "job_id": row[0],
            "spec": spec,
            "state": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "started_at": row[5],
            "finished_at": row[6],
            "progress": row[7],
            "current_step": row[8],
            "total_steps": row[9],
            "loss": row[10],
            "saved_to": row[11],
            "error": row[12],
            "metadata": dict(json.loads(row[13] or "{}")),
        }
        out.append(rec)
    return out

def append_job_event(job_id: str, event: JobEvent) -> None:
    if not job_id or not job_id.strip():
        raise ValueError("job_id required")
    if not isinstance(event, JobEvent):
        raise TypeError("event must JobEvent")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO finetune_job_events("
            "event_id, job_id, event_type, payload_json, created_at) "
            "VALUES(?, ?, ?, ?, ?)",
            (
                event.event_id,
                job_id.strip(),
                event.event_type,
                json.dumps(event.payload, ensure_ascii=False),
                float(event.created_at),
            ),
        )

def load_job_events(
    job_id: str, limit: int = 500,
) -> list[dict[str, Any]]:
    if not job_id or not job_id.strip():
        raise ValueError("job_id required")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(
            "SELECT event_id, event_type, payload_json, created_at "
            "FROM finetune_job_events WHERE job_id = ? "
            "ORDER BY created_at ASC LIMIT ?",
            (job_id.strip(), int(limit)),
        ).fetchall()
    return [
        {
            "event_id": r[0],
            "job_id": job_id,
            "event_type": r[1],
            "payload": dict(json.loads(r[2] or "{}")),
            "created_at": r[3],
        }
        for r in rows
    ]

def delete_job_record(job_id: str) -> bool:
    if not job_id or not job_id.strip():
        raise ValueError("job_id required")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM finetune_job_events WHERE job_id = ?",
                     (job_id.strip(),))
        cur = conn.execute("DELETE FROM finetune_jobs WHERE job_id = ?",
                           (job_id.strip(),))
        return cur.rowcount > 0

def reset_job_records() -> None:
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM finetune_job_events")
        conn.execute("DELETE FROM finetune_jobs")

class JobStore:
    VERSION = "1.0"
    def save(self, r: JobRecord) -> None: save_job_record(r)
    def load(self, jid: str) -> JobRecord | None: return load_job_record(jid)
    def list(self, state: str = "", limit: int = 50) -> list[dict]:
        return list_job_records(state=state, limit=limit)
    def update(self, jid: str, s: JobState, **f) -> bool:
        return update_job_state(jid, s, **f)
    def append_event(self, jid: str, e: JobEvent) -> None:
        append_job_event(jid, e)
    def events(self, jid: str, limit: int = 500) -> list[dict]:
        return load_job_events(jid, limit=limit)
    def delete(self, jid: str) -> bool: return delete_job_record(jid)
    def reset(self) -> None: reset_job_records()
    def ready(self) -> bool: return True
    def dump(self) -> dict:
        return {"name": type(self).__name__, "version": self.VERSION}

__all__ = [
    "JobStore",
    "save_job_record", "load_job_record", "list_job_records",
    "update_job_state", "append_job_event", "load_job_events",
    "delete_job_record", "reset_job_records",
]
