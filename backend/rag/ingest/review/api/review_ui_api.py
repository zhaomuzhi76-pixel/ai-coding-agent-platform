"""L4 审核 UI API —— 页面数据 + 待审核列表 + 演示播种。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.foundation.draft_status import DraftStatus
from backend.rag.ingest.review.foundation.review_contract import (
    ApprovalDecision, DraftChunk,
)
from backend.rag.ingest.review.review.approval_router import ApprovalRouter
from backend.rag.ingest.review.review.recall_visualizer import RecallVisualizer
from backend.rag.ingest.review.review.review_ui_builder import ReviewUiBuilder
from backend.rag.ingest.review.storage.draft_store import get_default_draft_store

DEFAULT_QUERY = "知识库 入库 审核"


class ReviewUiApi:
    def __init__(self, router: ApprovalRouter,
                 visualizer: RecallVisualizer | None = None) -> None:
        self._router = router
        self._visualizer = visualizer
        self._builder = ReviewUiBuilder()
        self._store = get_default_draft_store()

    def list_pending(self) -> dict[str, Any]:
        jobs = list(self._store.list_jobs(DraftStatus.PENDING_REVIEW))
        out = []
        for jid in jobs:
            try:
                chunks = list(self._store.get_chunks(jid))
            except Exception:
                chunks = []
            out.append({
                "job_id": jid,
                "chunk_count": len(chunks),
                "preview": chunks[0].content[:80] if chunks else "",
            })
        return {"jobs": out, "count": len(out)}

    def seed_demo(self, job_id: str, texts: list[str]) -> dict[str, Any]:
        texts = [t for t in texts if t and t.strip()]
        if not texts:
            texts = [
                "RAG 知识库入库流程包括解析、分块、审核、向量化四个阶段。",
                "今天天气不错，适合出门散步。",
                "审核门要求草稿状态从 pending_review 经 reviewing 到 approved。",
            ]
        self._store.create_job(job_id, [
            DraftChunk(chunk_id=f"c{i}", job_id=job_id, content=t, order=i)
            for i, t in enumerate(texts)
        ])
        return {"job_id": job_id, "chunk_count": len(texts)}

    def get_page(self, job_id: str, query: str = DEFAULT_QUERY) -> dict[str, Any]:
        chunks = self._store.get_chunks(job_id)
        preview = None
        if self._visualizer is not None:
            preview = self._visualizer.preview(job_id, query, chunks)
        page = self._builder.build(job_id, query, chunks, preview)
        return page.to_dict()

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

    def edit_and_approve(self, job_id: str, edits: list[dict[str, Any]],
                         approved_ids: list[str],
                         reviewer: str = "anonymous") -> dict[str, Any]:
        chunk_edits = tuple(
            DraftChunk(chunk_id=str(e.get("chunk_id") or ""),
                       job_id=job_id, content=str(e.get("content") or ""),
                       order=int(e.get("order") or 0),
                       metadata=dict(e.get("metadata") or {}))
            for e in edits
        )
        return self._router.route(ApprovalDecision(
            job_id=job_id, action="edit_and_approve",
            approved_chunk_ids=tuple(approved_ids),
            edited_chunks=chunk_edits, reviewer=reviewer,
        ))
