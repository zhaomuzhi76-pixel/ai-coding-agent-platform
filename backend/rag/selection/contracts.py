"""
RAG 选择契约层。

职责边界（不可扩展）：
  - 描述"向量索引命名空间"这一 RAG 侧独有概念
  - 引用 providers.selection 的 EmbeddingDescriptor/RerankDescriptor，不重复定义
  - 不做检索、不做向量化、不碰 vector_store
上游：providers.selection.contracts
下游：L1 rag.selection.namespace_resolver、L2 chatbot 检索桥
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.providers.selection.contracts import (  # re-export for RAG-side consumers
    EmbeddingDescriptor,
    RerankDescriptor,
)

__all__ = ["EmbeddingDescriptor", "RerankDescriptor", "IndexNamespace"]


@dataclass(frozen=True)
class IndexNamespace:
    """
    向量索引命名空间。
    由 (embedding_id, dim) 唯一决定 —— 防止切模型时跨维度复用同一索引。
    """
    embedding_id: str
    dim: int

    def __post_init__(self) -> None:
        if not self.embedding_id:
            raise ValueError("IndexNamespace.embedding_id must not be empty")
        if self.dim <= 0:
            raise ValueError(f"IndexNamespace.dim must be > 0, got {self.dim}")

    @property
    def name(self) -> str:
        return f"idx_{self.embedding_id}_{self.dim}"

    @classmethod
    def from_descriptor(cls, descriptor: EmbeddingDescriptor) -> "IndexNamespace":
        return cls(embedding_id=descriptor.id, dim=descriptor.dim)
