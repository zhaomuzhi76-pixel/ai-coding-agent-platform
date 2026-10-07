"""审核契约。职责：只描述"待审核块"与"可视化召回结果"。
不做存储（draft_store 管）、不检索（preview 管）、不入库（commit 管）。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple


@dataclass(frozen=True)
class DraftChunk:
    """待审核块。id 稳定，可勾选/编辑。"""
    chunk_id: str
    text: str
    source: str = ""
    source_path: str = ""
    line_no: int = 0
    role: str = ""
    images: Tuple[dict, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata",
                           MappingProxyType(dict(self.metadata)))
        if not self.chunk_id: raise ValueError("chunk_id required")
        if not isinstance(self.images, tuple):
            raise TypeError("images must be tuple")

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id, "text": self.text,
            "source": self.source, "source_path": self.source_path,
            "line_no": self.line_no, "role": self.role,
            "images": list(self.images),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "DraftChunk":
        return cls(
            chunk_id=str(d["chunk_id"]), text=str(d.get("text", "")),
            source=str(d.get("source", "")),
            source_path=str(d.get("source_path", "")),
            line_no=int(d.get("line_no", 0)),
            role=str(d.get("role", "")),
            images=tuple(d.get("images") or ()),
            metadata=dict(d.get("metadata") or {}),
        )


@dataclass(frozen=True)
class ReviewPreviewHit:
    """可视化召回命中的单块。三路分数 + 综合。"""
    chunk_id: str
    text: str
    bm25_rank: int = 0
    bm25_score: float = 0.0
    rerank_rank: int = 0
    rerank_score: float = 0.0
    fused_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id, "text": self.text,
            "bm25_rank": self.bm25_rank,
            "bm25_score": round(self.bm25_score, 6),
            "rerank_rank": self.rerank_rank,
            "rerank_score": round(self.rerank_score, 6),
            "fused_score": round(self.fused_score, 6),
        }


@dataclass(frozen=True)
class ReviewPreview:
    """可视化召回结果。"""
    job_id: str
    query: str
    total_drafts: int = 0
    hits: Tuple[ReviewPreviewHit, ...] = ()
    reranked: bool = False
    elapsed_ms: int = 0
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not isinstance(self.hits, tuple):
            raise TypeError("hits must be tuple")

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id, "query": self.query,
            "total_drafts": self.total_drafts,
            "hits": [h.to_dict() for h in self.hits],
            "reranked": self.reranked,
            "elapsed_ms": self.elapsed_ms,
            "meta": dict(self.meta),
        }


__all__ = ["DraftChunk", "ReviewPreviewHit", "ReviewPreview"]
