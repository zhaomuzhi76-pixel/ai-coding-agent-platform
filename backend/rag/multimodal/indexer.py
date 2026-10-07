"""图文混合索引。职责：MultimodalChunk → 向量库 upsert。
不切片（chunker 管）、不检索（retriever 管）、不组装响应。
对 VectorStore 的 upsert 签名做自适应，避免硬编码。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from backend.rag.multimodal.chunker import MultimodalChunker, make_default_chunker
from backend.rag.multimodal.contracts import MultimodalChunk

UpsertFn = Callable[[Sequence[str], Sequence[Mapping[str, Any]], Sequence[str]], None]

DEFAULT_BATCH = 64

@dataclass(frozen=True)
class IndexReport:
    indexed: int
    chunks: int
    skipped: int
    batches: int
    errors: tuple = ()

def _make_default_upsert(vector_store: Any) -> UpsertFn:
    """对 VectorStore.upsert_documents 做签名兼容。"""
    method = getattr(vector_store, "upsert_documents", None)
    if not callable(method):
        raise TypeError("vector_store 缺少可调用的 upsert_documents")

    def _call(texts, metadatas, ids, embeddings=None):
        t, m, i = list(texts), list(metadatas), list(ids)
        # 真实签名：upsert_documents(documents, ids, metadata=None, embeddings=None)
        try:
            method(t, i, m, embeddings)
            return
        except TypeError:
            pass
        try:
            method(t, i, metadata=m, embeddings=embeddings)
            return
        except TypeError:
            pass
        method(documents=t, ids=i, metadata=m, embeddings=embeddings)

    return _call

class MultimodalIndexer:
    def __init__(self, vector_store: Any,
                 chunker: Optional[MultimodalChunker] = None,
                 upsert_fn: Optional[UpsertFn] = None,
                 embed_fn: Any = None) -> None:
        self._vs = vector_store
        self._chunker = chunker or make_default_chunker()
        self._upsert = upsert_fn or _make_default_upsert(vector_store)
        self._embed = embed_fn

    @property
    def chunker(self) -> MultimodalChunker:
        return self._chunker

    def index_chunks(self, chunks: Iterable[MultimodalChunk], *,
                     batch_size: int = DEFAULT_BATCH) -> IndexReport:
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        lst = list(chunks)
        if not lst:
            return IndexReport(indexed=0, chunks=0, skipped=0, batches=0)
        total = 0
        errors: list[str] = []
        nbatch = 0
        for start in range(0, len(lst), batch_size):
            batch = lst[start:start + batch_size]
            texts = [c.text for c in batch]
            metas = [c.to_metadata() for c in batch]
            ids = [c.chunk_id for c in batch]
            try:
                if self._embed is not None:
                    embs = self._embed(texts)
                    self._upsert(texts, metas, ids, embs)
                else:
                    self._upsert(texts, metas, ids)
                total += len(batch)
                nbatch += 1
            except Exception as e:
                errors.append(f"batch@{start}: {type(e).__name__}: {e}")
        return IndexReport(indexed=total, chunks=len(lst),
                           skipped=len(lst) - total, batches=nbatch,
                           errors=tuple(errors))

    def index_items(self, items: Iterable[Mapping[str, Any]], *,
                    batch_size: int = DEFAULT_BATCH) -> IndexReport:
        return self.index_chunks(self._chunker.chunk_items(items),
                                 batch_size=batch_size)

    def index_text(self, text: str, *, source: str = "", source_path: str = "",
                   line_no: int = 0, role: str = "",
                   images: Any = None,
                   metadata: Optional[Mapping[str, Any]] = None,
                   batch_size: int = DEFAULT_BATCH) -> IndexReport:
        chunks = self._chunker.chunk_text(
            text=text, source=source, source_path=source_path,
            line_no=line_no, role=role, images=images, metadata=metadata)
        return self.index_chunks(chunks, batch_size=batch_size)

def make_default_indexer(vector_store: Any) -> MultimodalIndexer:
    return MultimodalIndexer(vector_store=vector_store)

__all__ = ["IndexReport", "MultimodalIndexer", "make_default_indexer"]
