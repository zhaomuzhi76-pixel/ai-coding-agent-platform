"""L2 草稿存储（纯内存 + 线程安全，零磁盘占用）。"""
from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Sequence

from backend.rag.ingest.review.foundation.draft_status import DraftStatus
from backend.rag.ingest.review.foundation.review_contract import DraftChunk
from backend.rag.ingest.review.foundation.review_errors import DraftNotFoundError


class InMemoryDraftStore:
    """草稿与向量库物理隔离；进程退出即消失，不落硬盘。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._chunks: "OrderedDict[str, list[DraftChunk]]" = OrderedDict()
        self._status: dict[str, DraftStatus] = {}
        self._reviewers: dict[str, str] = {}

    def create_job(self, job_id: str, chunks: Sequence[DraftChunk]) -> None:
        with self._lock:
            self._chunks[job_id] = list(chunks)
            self._status[job_id] = DraftStatus.PENDING_REVIEW

    def get_chunks(self, job_id: str) -> Sequence[DraftChunk]:
        with self._lock:
            self._require(job_id)
            return tuple(self._chunks[job_id])

    def get_status(self, job_id: str) -> DraftStatus:
        with self._lock:
            self._require(job_id)
            return self._status[job_id]

    def set_status(self, job_id: str, status: DraftStatus) -> None:
        with self._lock:
            self._require(job_id)
            self._status[job_id] = status

    def update_chunks(self, job_id: str, chunks: Sequence[DraftChunk]) -> None:
        with self._lock:
            self._require(job_id)
            self._chunks[job_id] = list(chunks)

    def delete_job(self, job_id: str) -> None:
        with self._lock:
            self._chunks.pop(job_id, None)
            self._status.pop(job_id, None)
            self._reviewers.pop(job_id, None)

    def list_jobs(self, status: DraftStatus | None = None) -> Sequence[str]:
        with self._lock:
            if status is None:
                return tuple(self._chunks.keys())
            return tuple(j for j, s in self._status.items() if s is status)

    def bind_reviewer(self, job_id: str, reviewer: str) -> None:
        with self._lock:
            self._require(job_id)
            self._reviewers[job_id] = reviewer

    def _require(self, job_id: str) -> None:
        if job_id not in self._chunks:
            raise DraftNotFoundError(job_id)


_default_store: InMemoryDraftStore | None = None
_store_lock = threading.Lock()


def get_default_draft_store() -> InMemoryDraftStore:
    global _default_store
    with _store_lock:
        if _default_store is None:
            _default_store = InMemoryDraftStore()
        return _default_store
