"""RAG 编排门面（L1 · 单例 · 对外统一入口）。

职责：
    - 组合 indexer + retriever
    - 提供 index_dataset / query / status / health
    - 单例 get_rag_service()

不负责：
    - 切片（chunker 管）
    - 向量化（EmbeddingService 管）
    - 存储（VectorStore 管）
    - 精排（reranker_server 独立进程 · 9033）
    - HTTP / UI（api 层管）
"""
from __future__ import annotations

from typing import Any, Optional

from .indexer import RagIndexer
from .retriever import RagRetriever
from .spec import RagHit


class RagService:
    VERSION = "1.0"

    def __init__(
        self,
        indexer: Optional[RagIndexer] = None,
        retriever: Optional[RagRetriever] = None,
    ) -> None:
        self.indexer = indexer or RagIndexer()
        self.retriever = retriever or RagRetriever()

    # ─── 索引 ──────────────────────────────────────
    async def index_dataset(
        self, dataset_path: str, dataset_id: str = "",
        on_progress=None,
    ) -> dict[str, Any]:
        return await self.indexer.index_dataset(
            dataset_path, dataset_id=dataset_id, on_progress=on_progress,
        )

    async def index_texts(
        self, texts: list[str], source: str = "inline",
    ) -> dict[str, Any]:
        return await self.indexer.index_texts(texts, source=source)

    # ─── 检索 ──────────────────────────────────────
    async def query(
        self, query: str, *, top_k: int = 5,
        use_rerank: bool | None = None,
    ) -> list[RagHit]:
        return await self.retriever.query(
            query, top_k=top_k, use_rerank=use_rerank,
        )

    async def query_dict(
        self, query: str, *, top_k: int = 5,
        use_rerank: bool | None = None,
    ) -> list[dict]:
        hits = await self.query(query, top_k=top_k, use_rerank=use_rerank)
        return [h.to_dict() for h in hits]

    # ─── 状态 ──────────────────────────────────────
    def count(self) -> int:
        return self.retriever.count()

    def clear(self) -> dict[str, Any]:
        return self.indexer.clear()

    async def status(self) -> dict[str, Any]:
        rh = await self.retriever.rerank_health()
        return {
            "count": self.count(),
            "collection": self.retriever.vector_config.collection_name,
            "vector_path": self.retriever.vector_config.path,
            "embedding": {
                "base_url": self.retriever.embed_base_url,
                "model": self.retriever.embed_model,
            },
            "reranker": {
                "url": self.retriever.rerank_url,
                "enabled": self.retriever.rerank_enabled,
                "health": rh,
            },
        }


_SERVICE: Optional[RagService] = None


def get_rag_service() -> RagService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = RagService()
    return _SERVICE


__all__ = ["RagService", "get_rag_service"]
