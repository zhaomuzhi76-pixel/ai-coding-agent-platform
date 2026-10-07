"""L1 审核 UI 契约 —— 前端渲染所需的纯数据结构。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChunkCard:
    chunk_id: str
    content: str
    order: int
    bm25: float
    rerank: float
    fused: float
    rank: int
    bm25_bar: float
    rerank_bar: float
    is_hit: bool
    selected: bool = True
    action: str = "keep"

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "order": self.order,
            "bm25": round(self.bm25, 4),
            "rerank": round(self.rerank, 4),
            "fused": round(self.fused, 6),
            "rank": self.rank,
            "bm25_bar": round(self.bm25_bar, 4),
            "rerank_bar": round(self.rerank_bar, 4),
            "is_hit": self.is_hit,
            "selected": self.selected,
            "action": self.action,
        }


@dataclass(frozen=True)
class ReviewActionSpec:
    action_id: str
    label: str
    style: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.action_id, "label": self.label, "style": self.style}


DEFAULT_ACTIONS: tuple[ReviewActionSpec, ...] = (
    ReviewActionSpec("approve", "全部通过", "primary"),
    ReviewActionSpec("edit_and_approve", "编辑后通过", "default"),
    ReviewActionSpec("reject", "拒绝全部", "danger"),
)


@dataclass(frozen=True)
class ReviewPageData:
    job_id: str
    query: str
    chunks: tuple[ChunkCard, ...] = ()
    actions: tuple[ReviewActionSpec, ...] = DEFAULT_ACTIONS
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hits = sum(1 for c in self.chunks if c.is_hit)
        return {
            "job_id": self.job_id,
            "query": self.query,
            "total": len(self.chunks),
            "hit_count": hits,
            "selected_count": sum(1 for c in self.chunks if c.selected),
            "actions": [a.to_dict() for a in self.actions],
            "chunks": [c.to_dict() for c in self.chunks],
            "metadata": dict(self.metadata),
        }
