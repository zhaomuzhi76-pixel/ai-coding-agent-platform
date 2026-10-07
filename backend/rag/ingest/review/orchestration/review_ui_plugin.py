"""L4 审核 UI 插件 —— 挂 /api/rag/review/ui 命名空间。"""
from __future__ import annotations

import json
from typing import Any

from backend.rag.ingest.review.api.review_ui_api import ReviewUiApi
from backend.rag.ingest.review.api.review_ui_static import html
from backend.rag.ingest.review.review.approval_router import ApprovalRouter
from backend.rag.ingest.review.review.bm25_scorer_adapter import build_scorer
from backend.rag.ingest.review.review.draft_state_machine import DraftStateMachine
from backend.rag.ingest.review.review.recall_visualizer import RecallVisualizer
from backend.rag.ingest.review.review.reranker_adapter import build_reranker
from backend.rag.ingest.review.storage.draft_promoter import DraftPromoter
from backend.rag.ingest.review.storage.draft_store import get_default_draft_store
from backend.rag.ingest.review.storage.vector_writer_adapter import build_writer

ROUTE_PREFIX = "/api/rag/review/ui"
ROUTES: tuple[tuple[str, str, str], ...] = (
    ("GET",  f"{ROUTE_PREFIX}",         "审核 UI 页面（HTML）"),
    ("GET",  f"{ROUTE_PREFIX}/page",    "页面数据 JSON"),
    ("POST", f"{ROUTE_PREFIX}/approve", "全部/部分通过"),
    ("POST", f"{ROUTE_PREFIX}/reject",  "拒绝"),
)


def _build_api() -> ReviewUiApi:
    store = get_default_draft_store()
    router = ApprovalRouter(store, DraftStateMachine(),
                            DraftPromoter(store, build_writer()))
    return ReviewUiApi(router, RecallVisualizer(build_scorer(), build_reranker()))


def build_router(api: ReviewUiApi | None = None) -> Any:
    """返回 FastAPI APIRouter；未安装 FastAPI 时返回 None。"""
    try:
        from fastapi import APIRouter, Body, Query  # type: ignore
        from fastapi.responses import HTMLResponse  # type: ignore
    except Exception:
        return None
    _api = api or _build_api()
    router = APIRouter()

    @router.get(f"{ROUTE_PREFIX}", response_class=HTMLResponse)
    def page() -> Any:
        return HTMLResponse(html())

    @router.get(f"{ROUTE_PREFIX}/jobs")
    def jobs() -> dict:
        return _api.list_pending()

    @router.post(f"{ROUTE_PREFIX}/seed")
    def seed(payload: dict = Body(...)) -> dict:
        return _api.seed_demo(
            str(payload.get("job_id") or "demo-job"),
            list(payload.get("texts") or []),
        )

    @router.get(f"{ROUTE_PREFIX}/page")
    def page_data(job_id: str = Query(...), query: str = Query("")) -> dict:
        return _api.get_page(job_id, query or "知识库 入库 审核")

    @router.post(f"{ROUTE_PREFIX}/approve")
    def approve(job_id: str = Query(...), payload: dict = Body(...)) -> dict:
        approved = list(payload.get("approved_chunk_ids") or [])
        edits = list(payload.get("edits") or [])
        if edits and payload.get("action") == "edit_and_approve":
            return _api.edit_and_approve(job_id, edits, approved)
        return _api.approve(job_id, approved)

    @router.post(f"{ROUTE_PREFIX}/reject")
    def reject(job_id: str = Query(...), payload: dict = Body(default={})) -> dict:
        return _api.reject(job_id)

    return router


class ReviewUiPlugin:
    descriptor = {
        "name": "rag_review_ui",
        "version": "1.0.0",
        "description": "L23 审核 UI —— 草稿块 + BM25/Reranker 分数条 + 审核按钮",
        "prefix": ROUTE_PREFIX,
        "routes": ROUTES,
    }

    @property
    def name(self) -> str:
        return self.descriptor["name"]

    def routes(self) -> tuple[tuple[str, str, str], ...]:
        return tuple(self.descriptor["routes"])

    def build_router(self) -> Any:
        return build_router()

    def export_routes_json(self) -> str:
        return json.dumps({"prefix": ROUTE_PREFIX, "routes": list(ROUTES)},
                          ensure_ascii=False, indent=2)


def build_plugin() -> ReviewUiPlugin:
    return ReviewUiPlugin()
