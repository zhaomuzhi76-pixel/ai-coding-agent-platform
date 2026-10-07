"""L4 审核路由工厂 —— 装配 Store / StateMachine / Recall / Router。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.api.review_router import ReviewApi
from backend.rag.ingest.review.review.approval_router import ApprovalRouter
from backend.rag.ingest.review.review.draft_state_machine import DraftStateMachine
from backend.rag.ingest.review.review.recall_visualizer import RecallVisualizer
from backend.rag.ingest.review.storage.draft_promoter import DraftPromoter
from backend.rag.ingest.review.storage.draft_store import get_default_draft_store


def _zero_bm25(query: str, texts: list[str]) -> list[float]:
    return [0.0] * len(texts)


def _zero_rerank(query: str, texts: list[str]) -> list[float]:
    return [0.0] * len(texts)


def build_review_api(writer: Any | None = None,
                     bm25: Any | None = None,
                     reranker: Any | None = None) -> ReviewApi:
    store = get_default_draft_store()
    machine = DraftStateMachine()
    promoter = DraftPromoter(store, writer) if writer is not None else None
    visualizer = RecallVisualizer(
        bm25 or _zero_bm25,
        reranker or _zero_rerank,
    )
    router = ApprovalRouter(store, machine, promoter)
    return ReviewApi(router, visualizer)
