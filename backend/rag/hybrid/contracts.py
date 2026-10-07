"""混合检索契约。职责：只描述"向量+关键词融合"的输入输出。
不做检索（子模块管）、不做融合算法（fusion 管）、不索引（bm25_index 管）。
与 rag/multimodal/contracts 边界：
  那层管"单一向量命中"；本层管"多路命中融合后的结果"。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple


class FusionStrategy(str, Enum):
    RRF = "rrf"          # Reciprocal Rank Fusion（推荐）
    WEIGHTED = "weighted"  # 加权分数融合
    VECTOR_ONLY = "vector_only"
    BM25_ONLY = "bm25_only"


@dataclass(frozen=True)
class HybridHit:
    """融合后的命中。包含向量和 BM25 两路排名/分数，便于调试。"""
    chunk_id: str
    text: str
    fused_score: float
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    vector_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0
    rerank_rank: Optional[int] = None
    source: str = ""
    source_path: str = ""
    line_no: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id, "text": self.text,
            "fused_score": round(self.fused_score, 6),
            "vector_rank": self.vector_rank,
            "bm25_rank": self.bm25_rank,
            "vector_score": round(self.vector_score, 4),
            "bm25_score": round(self.bm25_score, 4),
            "rerank_score": round(self.rerank_score, 4),
            "rerank_rank": self.rerank_rank,
            "source": self.source,
            "source_path": self.source_path,
            "line_no": self.line_no,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class HybridReport:
    query: str
    hits: Tuple[HybridHit, ...] = ()
    vector_candidates: int = 0
    bm25_candidates: int = 0
    fused_candidates: int = 0
    strategy: FusionStrategy = FusionStrategy.RRF
    reranked: bool = False
    elapsed_ms: int = 0
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not isinstance(self.hits, tuple):
            raise TypeError("hits must be tuple")

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "hits": [h.to_dict() for h in self.hits],
            "vector_candidates": self.vector_candidates,
            "bm25_candidates": self.bm25_candidates,
            "fused_candidates": self.fused_candidates,
            "strategy": self.strategy.value,
            "reranked": self.reranked,
            "elapsed_ms": self.elapsed_ms,
            "meta": dict(self.meta),
        }


__all__ = ["HybridHit", "HybridReport", "FusionStrategy"]
