"""图文 RAG 服务。职责：编排 索引 + 检索，给上层（chatbot / API）用。
不切片（chunker 管）、不向量化（embed_fn 注入）、不 upsert（indexer 管）、
不排序（reranker 注入）、不组装响应（API 层管）。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from backend.rag.multimodal.chunker import MultimodalChunker, make_default_chunker
from backend.rag.multimodal.indexer import (
    IndexReport, MultimodalIndexer)
from backend.rag.multimodal.retriever import (
    EmbedFn, RerankFn, SearchReport, MultimodalRetriever)

DEFAULT_LIMIT = 5
DEFAULT_BATCH = 64

@dataclass(frozen=True)
class ServiceStatus:
    ready: bool
    indexed: int
    has_embed: bool
    has_rerank: bool

class MultimodalRagService:
    def __init__(self, *, vector_store: Any, embed_fn: EmbedFn,
                 rerank_fn: Optional[RerankFn] = None,
                 chunker: Optional[MultimodalChunker] = None) -> None:
        self._vs = vector_store
        self._embed = embed_fn
        self._rerank = rerank_fn
        self._chunker = chunker or make_default_chunker()
        self._indexer = MultimodalIndexer(vector_store=vector_store,
                                          chunker=self._chunker,
                                          embed_fn=embed_fn)
        self._retriever = MultimodalRetriever(
            vector_store=vector_store, embed_fn=embed_fn, rerank_fn=rerank_fn)

    # ---------- 索引 ----------
    def index_items(self, items: Iterable[Mapping[str, Any]], *,
                    batch_size: int = DEFAULT_BATCH) -> IndexReport:
        return self._indexer.index_items(items, batch_size=batch_size)

    def index_text(self, text: str, *, source: str = "",
                   source_path: str = "", line_no: int = 0,
                   role: str = "", images: Any = None,
                   metadata: Optional[Mapping[str, Any]] = None,
                   batch_size: int = DEFAULT_BATCH) -> IndexReport:
        return self._indexer.index_text(
            text=text, source=source, source_path=source_path,
            line_no=line_no, role=role, images=images,
            metadata=metadata, batch_size=batch_size)

    # ---------- 检索 ----------
    def search(self, query: str, *, limit: int = DEFAULT_LIMIT,
               where: Optional[Mapping[str, Any]] = None,
               rerank: bool = False,
               rerank_top_k: int = 0) -> SearchReport:
        return self._retriever.search(
            query, limit=limit, where=where,
            rerank=rerank, rerank_top_k=rerank_top_k)

    def search_dict(self, query: str, **kw) -> dict:
        """给 API 层的便捷序列化出口。"""
        rep = self.search(query, **kw)
        return {
            "query": rep.query,
            "candidates": rep.candidates,
            "reranked": rep.reranked,
            "hits": [h.to_dict() for h in rep.hits],
        }

    # ---------- 状态 ----------
    def count(self) -> int:
        method = getattr(self._vs, "count", None)
        try:
            return int(method()) if callable(method) else -1
        except Exception:
            return -1

    def status(self) -> ServiceStatus:
        return ServiceStatus(
            ready=True, indexed=self.count(),
            has_embed=callable(self._embed),
            has_rerank=callable(self._rerank))

def make_service(*, vector_store: Any, embed_fn: EmbedFn,
                 rerank_fn: Optional[RerankFn] = None,
                 chunker: Optional[MultimodalChunker] = None) -> MultimodalRagService:
    return MultimodalRagService(vector_store=vector_store, embed_fn=embed_fn,
                                rerank_fn=rerank_fn, chunker=chunker)

__all__ = ["MultimodalRagService", "ServiceStatus", "make_service"]
