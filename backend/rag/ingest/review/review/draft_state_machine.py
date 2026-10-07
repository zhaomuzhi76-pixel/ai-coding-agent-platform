"""L3 草稿状态机 —— 唯一状态真相源。"""
from __future__ import annotations

import threading
from typing import Callable

from backend.rag.ingest.review.foundation.draft_status import (
    ALLOWED_TRANSITIONS,
    DraftStatus,
)
from backend.rag.ingest.review.foundation.review_errors import StateTransitionError

Listener = Callable[[str, DraftStatus, DraftStatus], None]


class DraftStateMachine:
    """约束草稿状态转移；非法转移直接拒绝。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._status: dict[str, DraftStatus] = {}
        self._listeners: list[Listener] = []

    def register(self, job_id: str,
                 initial: DraftStatus = DraftStatus.PENDING_REVIEW) -> None:
        with self._lock:
            self._status[job_id] = initial

    def current(self, job_id: str) -> DraftStatus:
        with self._lock:
            return self._status.get(job_id, DraftStatus.PENDING_REVIEW)

    def can_transition(self, src: DraftStatus, dst: DraftStatus) -> bool:
        return dst in ALLOWED_TRANSITIONS.get(src, frozenset())

    def transition(self, job_id: str, dst: DraftStatus) -> DraftStatus:
        with self._lock:
            src = self._status.get(job_id, DraftStatus.PENDING_REVIEW)
            if not self.can_transition(src, dst):
                raise StateTransitionError(
                    f"job={job_id} {src.value} → {dst.value} 非法"
                )
            self._status[job_id] = dst
        self._notify(job_id, src, dst)
        return dst

    def add_listener(self, fn: Listener) -> None:
        self._listeners.append(fn)

    def _notify(self, job_id: str, src: DraftStatus, dst: DraftStatus) -> None:
        for fn in tuple(self._listeners):
            fn(job_id, src, dst)
