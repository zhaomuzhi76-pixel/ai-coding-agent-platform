"""RAG 向量库管理聚合路由（工业级）。

职责：
  - 只做 include_router，把 4 个业务路由聚合到统一 prefix
  - 不做业务逻辑（各子 router 管）
  - 不改挂载点（__main__.py 仍是 from vector_admin_router import router）

结构：
  vector_common.py        共享 helper
  vector_manage_router    /vectors/sources, /vectors/delete*
  vector_detail_router    /vectors/source-detail, /vectors/chunk/delete
  vector_recall_router    /recall-filtered
  vector_curate_router    /curate/*
"""
from __future__ import annotations
from fastapi import APIRouter

from backend.api.rag.vector_manage_router import router as _manage
from backend.api.rag.vector_detail_router import router as _detail
from backend.api.rag.vector_recall_router import router as _recall
from backend.api.rag.vector_curate_router import router as _curate

router = APIRouter(prefix="/api/rag", tags=["rag-vector-admin"])
router.include_router(_manage)
router.include_router(_detail)
router.include_router(_recall)
router.include_router(_curate)

__all__ = ["router"]
