"""L3 可视化召回 —— BM25 左路 + Reranker 右路，供审核人预览。"""
from __future__ import annotations

from typing import Protocol, Sequence

from backend.rag.ingest.review.foundation.review_contract import (
    DraftChunk,
    RecallPreview,
    RecallScore,
)


class Bm25ScorerPort(Protocol):
    def score(self, query: str, texts: Sequence[str]) -> Sequence[float]: ...


class RerankerPort(Protocol):
    def rerank(self, query: str, texts: Sequence[str]) -> Sequence[float]: ...


class RecallVisualizer:
    """对草稿块执行两路召回并融合打分，供审核 UI 展示。"""

    def __init__(self, bm25: Bm25ScorerPort, reranker: RerankerPort,
                 fusion_k: int = 60) -> None:
        self._bm25 = bm25
        self._reranker = reranker
        self._k = fusion_k

    def preview(self, job_id: str, query: str,
                chunks: Sequence[DraftChunk]) -> RecallPreview:
        if not chunks:
            return RecallPreview(job_id=job_id, query=query, scores=())
        texts = [c.content for c in chunks]
        bm = list(self._bm25.score(query, texts))
        rk = list(self._reranker.rerank(query, texts))
        fused = self._rrf(bm, rk)
        order = sorted(range(len(chunks)), key=lambda i: fused[i], reverse=True)
        rank_map = {idx: pos + 1 for pos, idx in enumerate(order)}
        scores = tuple(
            RecallScore(
                chunk_id=chunks[i].chunk_id,
                bm25=float(bm[i]),
                rerank=float(rk[i]),
                fused=float(fused[i]),
                rank=rank_map[i],
            )
            for i in range(len(chunks))
        )
        ordered = tuple(sorted(scores, key=lambda s: s.rank))
        return RecallPreview(job_id=job_id, query=query, scores=ordered)

    def _rrf(self, a: Sequence[float], b: Sequence[float]) -> list[float]:
        ra = self._rank(a)
        rb = self._rank(b)
        k = self._k
        return [1.0 / (k + ra[i]) + 1.0 / (k + rb[i]) for i in range(len(a))]

    @staticmethod
    def _rank(values: Sequence[float]) -> list[int]:
        order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
        ranks = [0] * len(values)
        for pos, idx in enumerate(order):
            ranks[idx] = pos + 1
        return ranks
