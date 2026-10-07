"""混合检索器。职责：编排 向量检索 + BM25 检索 + 融合。
不做向量检索（MultimodalRetriever 管）、不做 BM25（BM25Index 管）、
不做融合算法（fusion 管）—— 只做编排 + 降级。
降级策略：向量挂 → 只 BM25；BM25 挂 → 只向量；两挂 → 空报告。
"""
from __future__ import annotations
import time
from typing import Any, Optional

from backend.rag.hybrid.contracts import (
    FusionStrategy, HybridReport)
from backend.rag.hybrid.fusion import fuse
from backend.rag.hybrid.reranker_client import (
    RerankerClient, get_default_reranker)

import os as _os_r  # [ENV] 动态 fetch 倍数

# [DYNAMIC] 内部 fetch_k 至少 = top_k * 此倍数（env 可调）
_FETCH_MULT = int(_os_r.environ.get("RAG_HYBRID_FETCH_MULT", "10"))
_FETCH_MIN = int(_os_r.environ.get("RAG_HYBRID_FETCH_MIN", "200"))

DEFAULT_VECTOR_FETCH_K = 20
DEFAULT_BM25_FETCH_K = 20
DEFAULT_TOP_K = 10


class HybridRetriever:
    def __init__(self, *, vector_retriever: Any,
                 bm25_index: Any,
                 strategy: FusionStrategy = FusionStrategy.RRF,
                 vector_fetch_k: int = DEFAULT_VECTOR_FETCH_K,
                 bm25_fetch_k: int = DEFAULT_BM25_FETCH_K,
                 reranker: Optional[RerankerClient] = None,
                 rerank_pool: int = 20) -> None:
        if vector_retriever is None:
            raise ValueError("vector_retriever required")
        if bm25_index is None:
            raise ValueError("bm25_index required")
        if vector_fetch_k <= 0 or bm25_fetch_k <= 0:
            raise ValueError("fetch_k must be > 0")
        self._vec = vector_retriever
        self._bm25 = bm25_index
        self._strategy = strategy
        self._vk = vector_fetch_k
        self._bk = bm25_fetch_k
        self._reranker = reranker
        self._rerank_pool = rerank_pool

    @property
    def strategy(self) -> FusionStrategy:
        return self._strategy

    def search(self, query: str, *, top_k: int = DEFAULT_TOP_K,
               where=None, rerank: bool = False) -> HybridReport:
        q = (query or "").strip()
        if not q:
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be > 0")

        t0 = time.time()
        vec_hits: list = []
        bm25_hits: list = []
        vec_err = ""
        bm25_err = ""

        # 向量路
        try:
            _vk = max(self._vk, top_k * _FETCH_MULT, _FETCH_MIN)
            rep = self._vec.search(q, limit=_vk, where=where)
            vec_hits = list(getattr(rep, "hits", ()) or ())
        except Exception as e:
            vec_err = f"{type(e).__name__}: {e}"

        # BM25 路
        try:
            _bk = max(self._bk, top_k * _FETCH_MULT, _FETCH_MIN)
            bm25_hits = self._bm25.search(q, top_k=_bk, where=where)
        except Exception as e:
            bm25_err = f"{type(e).__name__}: {e}"

        # 两路都挂
        if vec_err and bm25_err:
            return HybridReport(
                query=q, hits=(), strategy=self._strategy,
                elapsed_ms=int((time.time() - t0) * 1000),
                meta={"degraded": "both_unavailable",
                      "vector_error": vec_err, "bm25_error": bm25_err})

        # 单路降级
        degraded = ""
        if vec_err:
            degraded = "vector_unavailable"
        elif bm25_err:
            degraded = "bm25_unavailable"

        # 融合：rerank=True 时多取候选供精排
        fetch_k = max(top_k, self._rerank_pool) if rerank else top_k
        hits = fuse(query=q, vector_hits=vec_hits, bm25_hits=bm25_hits,
                    strategy=self._strategy, top_k=fetch_k)

        reranked = False
        if rerank and hits:
            hits, reranked = self._apply_rerank(q, hits, top_k)
        else:
            hits = hits[:top_k]

        return HybridReport(
            query=q, hits=tuple(hits),
            vector_candidates=len(vec_hits),
            bm25_candidates=len(bm25_hits),
            fused_candidates=len(hits),
            strategy=self._strategy,
            reranked=reranked,
            elapsed_ms=int((time.time() - t0) * 1000),
            meta={"degraded": degraded,
                  "vector_error": vec_err, "bm25_error": bm25_err,
                  "vector_fetch_k": self._vk,
                  "bm25_fetch_k": self._bk},
        )

    def _apply_rerank(self, query: str, hits: list,
                       top_k: int) -> tuple:
        """对融合命中跑 reranker。返回 (new_hits, applied)。"""
        rr = self._reranker or get_default_reranker()
        docs = [h.text for h in hits]
        try:
            results = rr.rerank(query, docs, top_k=len(docs))
        except Exception:
            return hits[:top_k], False
        if not results:
            return hits[:top_k], False
        from backend.rag.hybrid.contracts import HybridHit
        new_hits: list = []
        for new_rank, r in enumerate(results, 1):
            idx = int(r.get("index", -1))
            if idx < 0 or idx >= len(hits):
                continue
            h = hits[idx]
            new_hits.append(HybridHit(
                chunk_id=h.chunk_id, text=h.text,
                fused_score=h.fused_score,
                vector_rank=h.vector_rank, bm25_rank=h.bm25_rank,
                vector_score=h.vector_score, bm25_score=h.bm25_score,
                rerank_score=float(r.get("score", 0.0)),
                rerank_rank=new_rank,
                source=h.source, source_path=h.source_path,
                line_no=h.line_no, metadata=h.metadata))
        if not new_hits:
            return hits[:top_k], False
        return new_hits[:top_k], True


def make_hybrid_retriever(*, vector_retriever: Any, bm25_index: Any,
                          strategy: FusionStrategy = FusionStrategy.RRF,
                          vector_fetch_k: int = DEFAULT_VECTOR_FETCH_K,
                          bm25_fetch_k: int = DEFAULT_BM25_FETCH_K
                          ) -> HybridRetriever:
    return HybridRetriever(
        vector_retriever=vector_retriever, bm25_index=bm25_index,
        strategy=strategy, vector_fetch_k=vector_fetch_k,
        bm25_fetch_k=bm25_fetch_k)


__all__ = ["HybridRetriever", "make_hybrid_retriever",
           "DEFAULT_VECTOR_FETCH_K", "DEFAULT_BM25_FETCH_K",
           "DEFAULT_TOP_K"]
