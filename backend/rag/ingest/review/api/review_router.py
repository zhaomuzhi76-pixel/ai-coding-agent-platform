"""L4 审核 API（框架无关，可挂 FastAPI / WS / CLI）。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.foundation.draft_status import DraftStatus
from backend.rag.ingest.review.foundation.review_contract import ApprovalDecision
from backend.rag.ingest.review.review.approval_router import ApprovalRouter
from backend.rag.ingest.review.review.recall_visualizer import RecallVisualizer
from backend.rag.ingest.review.storage.draft_store import get_default_draft_store


class ReviewApi:
    """审核门对外接口：待审列表、召回预览、通过/拒绝。"""

    def __init__(self, router: ApprovalRouter,
                 visualizer: RecallVisualizer | None = None) -> None:
        self._router = router
        self._visualizer = visualizer
        self._store = get_default_draft_store()

    def list_pending(self) -> list[str]:
        return list(self._store.list_jobs(DraftStatus.PENDING_REVIEW))

    def preview_recall(self, job_id: str, query: str) -> dict[str, Any]:
        if self._visualizer is None:
            return {"job_id": job_id, "query": query, "scores": []}
        chunks = self._store.get_chunks(job_id)
        result = self._visualizer.preview(job_id, query, chunks)
        return {
            "job_id": result.job_id,
            "query": result.query,
            "scores": [
                {"chunk_id": s.chunk_id, "bm25": s.bm25,
                 "rerank": s.rerank, "fused": s.fused, "rank": s.rank}
                for s in result.scores
            ],
        }

    def approve(self, job_id: str, approved_ids: list[str],
                reviewer: str = "anonymous") -> dict[str, Any]:
        return self._router.route(ApprovalDecision(
            job_id=job_id, action="approve",
            approved_chunk_ids=tuple(approved_ids), reviewer=reviewer,
        ))

    def reject(self, job_id: str, reviewer: str = "anonymous") -> dict[str, Any]:
        return self._router.route(ApprovalDecision(
            job_id=job_id, action="reject", reviewer=reviewer,
        ))
