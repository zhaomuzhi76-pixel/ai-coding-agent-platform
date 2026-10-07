"""L3 审核 UI 构建器 —— 草稿块 + 召回分 → 可渲染页面数据。"""
from __future__ import annotations

from typing import Sequence

from backend.rag.ingest.review.foundation.review_contract import (
    DraftChunk,
    RecallPreview,
)
from backend.rag.ingest.review.foundation.review_ui_contract import (
    ChunkCard,
    DEFAULT_ACTIONS,
    ReviewPageData,
)


class ReviewUiBuilder:
    """把 RecallPreview + DraftChunk 转为前端渲染数据。"""

    def build(self, job_id: str, query: str,
              chunks: Sequence[DraftChunk],
              preview: RecallPreview | None) -> ReviewPageData:
        score_map = self._score_map(preview)
        bm25_max = self._max_score(score_map, "bm25")
        rerank_max = self._max_score(score_map, "rerank")
        cards = tuple(
            self._card(chunk, score_map.get(chunk.chunk_id),
                       bm25_max, rerank_max)
            for chunk in chunks
        )
        ordered = tuple(sorted(cards, key=lambda c: (c.rank if c.rank > 0 else 999,
                                                     c.order)))
        meta = {
            "bm25_max": round(bm25_max, 4),
            "rerank_max": round(rerank_max, 4),
            "fusion": "rrf",
        }
        return ReviewPageData(
            job_id=job_id, query=query, chunks=ordered,
            actions=DEFAULT_ACTIONS, metadata=meta,
        )

    def _card(self, chunk: DraftChunk, score, bm25_max: float,
              rerank_max: float) -> ChunkCard:
        bm25 = score.bm25 if score else 0.0
        rerank = score.rerank if score else 0.0
        fused = score.fused if score else 0.0
        rank = score.rank if score else 0
        return ChunkCard(
            chunk_id=chunk.chunk_id, content=chunk.content,
            order=chunk.order,
            bm25=bm25, rerank=rerank, fused=fused, rank=rank,
            bm25_bar=_norm(bm25, bm25_max),
            rerank_bar=_norm(rerank, rerank_max),
            is_hit=rank > 0,
            selected=rank > 0,
            action="keep",
        )

    @staticmethod
    def _score_map(preview: RecallPreview | None) -> dict:
        if preview is None:
            return {}
        return {s.chunk_id: s for s in preview.scores}

    @staticmethod
    def _max_score(score_map: dict, field: str) -> float:
        if not score_map:
            return 0.0
        return max(getattr(s, field, 0.0) for s in score_map.values())


def _norm(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return min(value / max_value, 1.0)
