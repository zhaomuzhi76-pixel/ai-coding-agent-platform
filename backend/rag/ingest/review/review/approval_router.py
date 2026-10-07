"""L3 审批路由 —— 状态双写（machine + store 同步），职责单一。"""
from __future__ import annotations

from typing import Sequence

from backend.rag.ingest.review.foundation.draft_status import DraftStatus
from backend.rag.ingest.review.foundation.review_contract import (
    ApprovalDecision,
    DraftChunk,
)
from backend.rag.ingest.review.foundation.review_errors import ReviewError
from backend.rag.ingest.review.review.draft_state_machine import DraftStateMachine
from backend.rag.ingest.review.storage.draft_promoter import DraftPromoter
from backend.rag.ingest.review.storage.draft_store_contract import DraftStoreContract

_ACTIONS = {"approve", "reject", "edit_and_approve"}


class ApprovalRouter:
    """将审核决策路由到状态机 + 存储 + 提升器。"""

    def __init__(self, store: DraftStoreContract,
                 machine: DraftStateMachine,
                 promoter: DraftPromoter | None = None) -> None:
        self._store = store
        self._machine = machine
        self._promoter = promoter

    def route(self, decision: ApprovalDecision) -> dict:
        if decision.action not in _ACTIONS:
            raise ReviewError(f"unknown action: {decision.action}")
        job_id = decision.job_id
        self._enter(job_id, DraftStatus.REVIEWING)
        if decision.action == "reject":
            return self._reject(job_id)
        if decision.action == "edit_and_approve":
            self._apply_edits(job_id, decision.edited_chunks)
        self._enter(job_id, DraftStatus.APPROVED)
        self._enter(job_id, DraftStatus.WRITING)
        try:
            written = self._promote(job_id, decision.approved_chunk_ids)
        except Exception:
            self._enter(job_id, DraftStatus.FAILED)
            raise
        self._enter(job_id, DraftStatus.DONE)
        self._store.delete_job(job_id)
        return {"job_id": job_id, "action": decision.action, "written": written}

    def _reject(self, job_id: str) -> dict:
        self._enter(job_id, DraftStatus.REJECTED)
        self._store.delete_job(job_id)
        return {"job_id": job_id, "action": "reject", "written": 0}

    def _apply_edits(self, job_id: str, edits: Sequence[DraftChunk]) -> None:
        if edits:
            self._store.update_chunks(job_id, edits)

    def _promote(self, job_id: str, approved_ids: Sequence[str]) -> int:
        if self._promoter is None:
            return 0
        return self._promoter.promote(job_id, approved_ids)

    def _enter(self, job_id: str, dst: DraftStatus) -> None:
        self._machine.transition(job_id, dst)
        self._store.set_status(job_id, dst)
