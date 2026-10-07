"""图文混合检索。职责：query → embedding → 向量库 search → MultimodalHit[]。
不切片、不索引、不生成 embedding（依赖注入 embed_fn）。
不重写 VectorStore，只解析其返回结构。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

from backend.rag.multimodal.contracts import (
    IMAGES_META_KEY, ImageRef, MultimodalHit)

EmbedFn = Callable[[Sequence[str]], Sequence[Sequence[float]]]
RerankFn = Callable[[str, list], list]

DEFAULT_LIMIT = 5

@dataclass(frozen=True)
class SearchReport:
    query: str
    hits: tuple
    candidates: int
    reranked: bool

def _first_layer(x: Any, idx: int) -> Any:
    """Chroma 返回常为 [[...]]；扁平结构则直接取。"""
    if isinstance(x, (list, tuple)) and len(x) > 0 \
            and isinstance(x[0], (list, tuple)):
        return x[idx]
    return x

def _distances_to_scores(raw: Any, n: int) -> list[float]:
    if not isinstance(raw, (list, tuple)) or len(raw) == 0:
        return [0.0] * n
    out: list[float] = []
    for d in raw:
        try:
            f = float(d)
        except (TypeError, ValueError):
            f = 0.0
        # Chroma 默认返回 L2 距离：score = 1 / (1 + d)
        out.append(round(1.0 / (1.0 + max(f, 0.0)), 6))
    return out

def _hit_from_row(chunk_id: str, text: str, score: float,
                  meta: Mapping[str, Any]) -> MultimodalHit:
    from backend.rag.multimodal.contracts import MultimodalChunk
    chunk = MultimodalChunk.from_metadata(chunk_id, text, meta)
    return MultimodalHit(
        chunk_id=chunk.chunk_id, text=chunk.text, score=score,
        images=chunk.images, source=chunk.source,
        source_path=chunk.source_path, line_no=chunk.line_no,
        role=chunk.role, metadata=chunk.metadata)

class MultimodalRetriever:
    def __init__(self, *, vector_store: Any, embed_fn: EmbedFn,
                 rerank_fn: Optional[RerankFn] = None) -> None:
        if not callable(embed_fn):
            raise TypeError("embed_fn must be callable")
        self._vs = vector_store
        self._embed = embed_fn
        self._rerank = rerank_fn

    def _search_raw(self, query_vec: Sequence[float], limit: int,
                    where: Optional[Mapping[str, Any]]) -> list:
        method = getattr(self._vs, "search", None)
        if not callable(method):
            raise TypeError("vector_store 缺少 search 方法")
        try:
            raw = method([list(query_vec)], limit=limit, where=where)
        except TypeError:
            raw = method([list(query_vec)], limit)
        if not isinstance(raw, Mapping):
            raise TypeError(f"search 返回非 mapping: {type(raw).__name__}")
        return self._parse_result(raw)

    def _parse_result(self, raw: Mapping[str, Any]) -> list[MultimodalHit]:
        ids = list(_first_layer(raw.get("ids", []), 0))
        docs = list(_first_layer(raw.get("documents", []), 0))
        metas = list(_first_layer(raw.get("metadatas", []), 0))
        dists = _first_layer(raw.get("distances", []), 0)
        n = min(len(ids), len(docs), len(metas)) if ids else 0
        scores = _distances_to_scores(dists, n)
        out: list[MultimodalHit] = []
        for i in range(n):
            meta = metas[i] if isinstance(metas[i], Mapping) else {}
            try:
                out.append(_hit_from_row(str(ids[i]), str(docs[i]),
                                          scores[i], meta))
            except Exception:
                continue
        return out

    def search(self, query: str, *, limit: int = DEFAULT_LIMIT,
               where: Optional[Mapping[str, Any]] = None,
               rerank: bool = False,
               rerank_top_k: int = 0) -> SearchReport:
        q = (query or "").strip()
        if not q:
            raise ValueError("query must not be empty")
        if limit <= 0:
            raise ValueError("limit must be > 0")
        vecs = self._embed([q])
        if not vecs:
            raise RuntimeError("embed_fn 未返回向量")
        hits = self._search_raw(vecs[0], limit, where)
        reranked = False
        if rerank and self._rerank is not None and hits:
            try:
                ranked = self._rerank(q, list(hits))
                if isinstance(ranked, list):
                    hits = [h for h in ranked if isinstance(h, MultimodalHit)]
                    reranked = True
                if rerank_top_k > 0 and len(hits) > rerank_top_k:
                    hits = hits[:rerank_top_k]
            except Exception:
                reranked = False
        return SearchReport(query=q, hits=tuple(hits),
                            candidates=len(hits), reranked=reranked)

    def search_hits(self, query: str, **kw) -> list:
        return list(self.search(query, **kw).hits)

def make_retriever(*, vector_store: Any, embed_fn: EmbedFn,
                   rerank_fn: Optional[RerankFn] = None) -> MultimodalRetriever:
    return MultimodalRetriever(vector_store=vector_store, embed_fn=embed_fn,
                               rerank_fn=rerank_fn)

__all__ = ["SearchReport", "MultimodalRetriever", "make_retriever"]
