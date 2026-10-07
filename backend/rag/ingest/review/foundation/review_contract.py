"""L1 契约：草稿块、召回打分、召回预览、审批决策。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DraftChunk:
    chunk_id: str
    job_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    order: int = 0


@dataclass(frozen=True)
class RecallScore:
    chunk_id: str
    bm25: float = 0.0
    rerank: float = 0.0
    fused: float = 0.0
    rank: int = 0


@dataclass(frozen=True)
class RecallPreview:
    job_id: str
    query: str
    scores: tuple[RecallScore, ...] = ()

    def top(self, k: int = 5) -> tuple[RecallScore, ...]:
        return self.scores[:k]

    def hit_ids(self) -> tuple[str, ...]:
        return tuple(s.chunk_id for s in self.scores if s.rank > 0)


@dataclass(frozen=True)
class ApprovalDecision:
    job_id: str
    action: str
    approved_chunk_ids: tuple[str, ...] = ()
    edited_chunks: tuple[DraftChunk, ...] = ()
    reviewer: str = "anonymous"
    comment: str = ""
