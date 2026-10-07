"""Hybrid RAG runtime 装配。职责：
  - 从 multimodal_runtime 复用 vector_store / service
  - 装配 BM25Index + BM25Sync + HybridRetriever
  - 单例 + ensure_synced（检索前增量同步）
不做检索本身、不做索引本身、不落盘。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from dataclasses import dataclass
from typing import Any, Optional

from backend.rag.hybrid.bm25_index import BM25Index
from backend.rag.hybrid.bm25_sync import BM25Sync
from backend.rag.hybrid.contracts import FusionStrategy
from backend.rag.hybrid.retriever import HybridRetriever

LARGE_INDEX_THRESHOLD = 100_000


@dataclass(frozen=True)
class HybridRuntime:
    bm25_index: BM25Index
    bm25_sync: BM25Sync
    retriever: HybridRetriever


def build_hybrid_runtime() -> HybridRuntime:
    from backend.api.rag.multimodal_runtime import (
        get_multimodal_rag_runtime)
    mm = get_multimodal_rag_runtime()
    vs = mm.vector_store
    bm25 = BM25Index()
    sync = BM25Sync(vector_store=vs, bm25_index=bm25)
    # 首次构建：小库全量重建；大库不主动重建（首次检索时懒同步）
    try:
        n = int(vs.count()) if hasattr(vs, "count") else 0
        if 0 < n <= LARGE_INDEX_THRESHOLD:
            sync.rebuild()
    except Exception as e:
        swallow("rag.hybrid.runtime:40", e)
    hr = HybridRetriever(
        vector_retriever=mm.service,
        bm25_index=bm25,
        strategy=FusionStrategy.RRF,
    )
    return HybridRuntime(bm25_index=bm25, bm25_sync=sync, retriever=hr)


_RT: Optional[HybridRuntime] = None


def get_hybrid_runtime() -> HybridRuntime:
    global _RT
    if _RT is None:
        _RT = build_hybrid_runtime()
    return _RT


def set_hybrid_runtime(rt: Optional[HybridRuntime]) -> None:
    global _RT
    _RT = rt


def ensure_synced() -> int:
    """检索前增量同步（幂等）。返回新增条数。"""
    try:
        rt = get_hybrid_runtime()
        r = rt.bm25_sync.sync_incremental()
        return int(r.get("added", 0))
    except Exception:
        return 0


__all__ = ["HybridRuntime", "build_hybrid_runtime",
           "get_hybrid_runtime", "set_hybrid_runtime", "ensure_synced",
           "LARGE_INDEX_THRESHOLD"]
