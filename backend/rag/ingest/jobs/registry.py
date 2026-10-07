"""异步任务注册表。职责：内存字典 + JSON 快照持久化。
不调度任务（worker 管）、不做解析（service 管）。
持久化到 ~/.cache/agent_knowledge/jobs/<job_id>.json（项目仓库外）。
序列化在 _serde.py；磁盘操作在 _persist.py。线程安全。
"""
from __future__ import annotations
import os
from pathlib import Path
from threading import RLock
from typing import Optional

from backend.rag.ingest.jobs._persist import (
    cleanup_oldest, delete_job, load_all, save_job)
from backend.rag.ingest.jobs._serde import deserialize
from backend.rag.ingest.jobs.contracts import (
    IngestJob, JobPhase, JobProgress, JobStatus, JobStep, new_job_id)

DEFAULT_ROOT = os.path.expanduser("~/.cache/agent_knowledge/jobs")
MAX_HISTORY = 500


class JobRegistry:
    def __init__(self, *, root: Optional[str] = None,
                 persist: bool = True,
                 max_history: int = MAX_HISTORY) -> None:
        if max_history <= 0:
            raise ValueError("max_history must be > 0")
        self._root = Path(root or DEFAULT_ROOT)
        self._persist = persist
        self._max = max_history
        self._jobs: dict = {}
        self._lock = RLock()

    @property
    def root(self) -> str:
        return str(self._root)

    @property
    def persist_enabled(self) -> bool:
        return self._persist

    # ---------- 创建 / 更新 ----------
    def create(self, *, filename: str, kb: str,
               size_bytes: int = 0, lang: str = "",
               job_id: Optional[str] = None) -> IngestJob:
        if not filename: raise ValueError("filename required")
        if not kb: raise ValueError("kb required")
        jid = job_id or new_job_id()
        job = IngestJob(job_id=jid, filename=filename, kb=kb,
                         size_bytes=size_bytes, lang=lang)
        with self._lock:
            self._jobs[jid] = job
        self._save(job)
        return job

    def update(self, job: IngestJob) -> IngestJob:
        if not isinstance(job, IngestJob):
            raise TypeError("job must be IngestJob")
        with self._lock:
            if job.job_id not in self._jobs:
                raise KeyError(f"job not found: {job.job_id}")
            self._jobs[job.job_id] = job
        self._save(job)
        return job

    def update_progress(self, job_id: str, progress: JobProgress,
                         status: Optional[JobStatus] = None) -> IngestJob:
        with self._lock:
            cur = self._jobs.get(job_id)
            if cur is None:
                raise KeyError(f"job not found: {job_id}")
            new = cur.with_progress(progress, status=status)
            self._jobs[job_id] = new
        self._save(new)
        return new

    def finish(self, job_id: str, *, status: JobStatus,
               error: str = "", origin_hash: Optional[str] = None,
               chunks_indexed: Optional[int] = None) -> IngestJob:
        with self._lock:
            cur = self._jobs.get(job_id)
            if cur is None:
                raise KeyError(f"job not found: {job_id}")
            new = cur.with_status(status, error=error,
                                   origin_hash=origin_hash,
                                   chunks_indexed=chunks_indexed)
            self._jobs[job_id] = new
        self._save(new)
        return new

    def append_step(self, job_id: str, phase: JobPhase,
                     message: str = "",
                     detail: Optional[dict] = None) -> None:
        import time as _t
        with self._lock:
            cur = self._jobs.get(job_id)
            if cur is None: return
            step = JobStep(ts=_t.time(), phase=phase,
                            message=message, detail=detail or {})
            new = IngestJob(
                job_id=cur.job_id, filename=cur.filename,
                kb=cur.kb, lang=cur.lang, size_bytes=cur.size_bytes,
                status=cur.status, progress=cur.progress,
                created_at=cur.created_at, started_at=cur.started_at,
                finished_at=cur.finished_at, error=cur.error,
                origin_hash=cur.origin_hash,
                chunks_indexed=cur.chunks_indexed,
                meta=cur.meta, steps=cur.steps + (step,))
            self._jobs[job_id] = new
        self._save(new)

    # ---------- 查询 ----------
    def get(self, job_id: str) -> Optional[IngestJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_recent(self, limit: int = 20) -> list:
        if limit <= 0: raise ValueError("limit must be > 0")
        with self._lock:
            jobs = sorted(self._jobs.values(),
                          key=lambda j: j.created_at, reverse=True)
            return jobs[:limit]

    def count(self) -> int:
        with self._lock:
            return len(self._jobs)

    def remove(self, job_id: str) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs.pop(job_id, None)
        if self._persist:
            delete_job(self._root, job_id)
        return True

    def clear(self) -> None:
        with self._lock:
            ids = list(self._jobs.keys())
            self._jobs.clear()
        if self._persist:
            for jid in ids:
                delete_job(self._root, jid)

    # ---------- 持久化 ----------
    def _save(self, job: IngestJob) -> None:
        if not self._persist:
            return
        save_job(self._root, job)
        cleanup_oldest(self._root, self._max)

    def load_from_disk(self) -> int:
        if not self._persist:
            return 0
        n = 0
        with self._lock:
            for d in load_all(self._root):
                job = deserialize(d)
                if job is not None:
                    self._jobs[job.job_id] = job
                    n += 1
        return n


_DEFAULT: Optional[JobRegistry] = None


def get_default_job_registry() -> JobRegistry:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = JobRegistry()
    return _DEFAULT


def set_default_job_registry(r: Optional[JobRegistry]) -> None:
    global _DEFAULT
    _DEFAULT = r


__all__ = ["JobRegistry", "get_default_job_registry",
           "set_default_job_registry", "DEFAULT_ROOT", "MAX_HISTORY"]
