"""L23 router 工厂 —— 对接 backend/__main__.py 的 routers 列表。"""
from __future__ import annotations

from fastapi import APIRouter


def build_review_ui_router() -> APIRouter:
    from backend.rag.ingest.review.orchestration.review_ui_plugin import (
        build_plugin,
    )
    return _safe(build_plugin().build_router())


def build_reranker_center_router() -> APIRouter:
    from backend.rag.ingest.review.orchestration.reranker_center_plugin import (
        build_plugin,
    )
    return _safe(build_plugin().build_router())


def build_provider_center_router() -> APIRouter:
    from backend.rag.ingest.review.provider_center.plugin import build_plugin
    plugin = build_plugin()
    plugin.on_load(None)
    return _safe(plugin.build_router())


def build_recall_test_router() -> APIRouter:
    from backend.rag.ingest.review.api.recall_test_router import build_router
    return _safe(build_router())


def _safe(router: object | None) -> APIRouter:
    return router if isinstance(router, APIRouter) else APIRouter()


__all__ = [
    "build_review_ui_router",
    "build_reranker_center_router",
    "build_provider_center_router",
    "build_recall_test_router",
]
