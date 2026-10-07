"""BM25 ↔ 向量库 同步。职责：
  ① 从 Chroma（vector_store）全量拉数据灌入 BM25
  ② 提供增量 upsert/delete 接口
不做检索（retriever 管）、不索引（bm25_index 管）、不切块。
"""
from __future__ import annotations
from typing import Any, Optional


def _iterate_chroma(vs: Any, *, batch: int = 500) -> list:
    """从 Chroma collection 全量拉 (id, text, metadata)。"""
    col = getattr(vs, "collection", None)
    if col is None:
        raise RuntimeError("vector_store 没有 collection 属性")
    total = col.count()
    if total == 0:
        return []
    out: list = []
    offset = 0
    while offset < total:
        data = col.get(limit=batch, offset=offset,
                       include=["documents", "metadatas"])
        ids = data.get("ids") or []
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        for i, cid in enumerate(ids):
            out.append({
                "chunk_id": str(cid),
                "text": str(docs[i]) if i < len(docs) else "",
                "metadata": dict(metas[i]) if i < len(metas) and metas[i] else {},
            })
        offset += len(ids)
        if not ids:
            break
    return out


class BM25Sync:
    """把向量库内容同步到 BM25 索引。"""

    def __init__(self, *, vector_store: Any, bm25_index: Any,
                 batch: int = 500) -> None:
        if vector_store is None:
            raise ValueError("vector_store required")
        if bm25_index is None:
            raise ValueError("bm25_index required")
        if batch <= 0:
            raise ValueError("batch must be > 0")
        self._vs = vector_store
        self._bm25 = bm25_index
        self._batch = batch

    def rebuild(self) -> dict:
        """清空 BM25 后全量重建。返回统计。"""
        self._bm25.clear()
        items = _iterate_chroma(self._vs, batch=self._batch)
        n = self._bm25.add_many(items)
        return {"rebuilt": True, "total": n}

    def sync_incremental(self) -> dict:
        """只补向量库里有、BM25 里没有的（不清空）。"""
        items = _iterate_chroma(self._vs, batch=self._batch)
        # bm25 里现有 chunk_id（通过内部属性；属于白盒操作）
        existing = set(getattr(self._bm25, "_docs", {}).keys())
        new_items = [it for it in items if it["chunk_id"] not in existing]
        n = self._bm25.add_many(new_items) if new_items else 0
        return {"total_in_vector": len(items),
                "added": n, "skipped": len(items) - n}

    def upsert(self, chunk_id: str, text: str, *,
               metadata: Optional[dict] = None) -> None:
        """索引/更新单条（indexer upsert 时调用）。"""
        self._bm25.add(chunk_id, text, metadata=metadata)

    def delete(self, chunk_id: str) -> bool:
        return self._bm25.remove(chunk_id)

    def count(self) -> int:
        return self._bm25.count()


def make_bm25_sync(*, vector_store: Any, bm25_index: Any,
                   batch: int = 500) -> BM25Sync:
    return BM25Sync(vector_store=vector_store, bm25_index=bm25_index,
                    batch=batch)


__all__ = ["BM25Sync", "make_bm25_sync"]
