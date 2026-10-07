"""图片检索器。职责：图搜图 / 文搜图，返回 ImageSearchReport。
不做编码细节（engine 管）、不做存储细节（store 管）、不做原件解析（origin 管）。
仅编排：query → CLIP 编码 → store 相似度检索 → 组装报告。
"""
from __future__ import annotations
import time
from typing import Any, Optional

from backend.rag.image_index.contracts import (
    ImageSearchHit, ImageSearchReport, SearchMode)

DEFAULT_TOP_K = 10


class ImageRetriever:
    def __init__(self, *, engine: Any, store: Any,
                 origin_store: Optional[Any] = None) -> None:
        if engine is None: raise ValueError("engine required")
        if store is None: raise ValueError("store required")
        self._engine = engine
        self._store = store
        self._origin = origin_store

    def search_by_image(self, image_path: str, *, top_k: int = DEFAULT_TOP_K,
                        where: Optional[dict] = None) -> ImageSearchReport:
        if top_k <= 0: raise ValueError("top_k must be > 0")
        t0 = time.time()
        q_vec = self._engine.encode_image(image_path)
        return self._do_search(image_path, q_vec, SearchMode.IMAGE_TO_IMAGE,
                                top_k, where, t0)

    def search_by_text(self, text: str, *, top_k: int = DEFAULT_TOP_K,
                       where: Optional[dict] = None) -> ImageSearchReport:
        if top_k <= 0: raise ValueError("top_k must be > 0")
        t = (text or "").strip()
        if not t: raise ValueError("text must not be empty")
        t0 = time.time()
        q_vec = self._engine.encode_text(t)
        return self._do_search(t, q_vec, SearchMode.TEXT_TO_IMAGE,
                                top_k, where, t0)

    def _do_search(self, query: str, q_vec, mode: SearchMode,
                   top_k: int, where, t0: float) -> ImageSearchReport:
        try:
            raw = self._store.search(q_vec, top_k=top_k, where=where)
        except Exception as e:
            return ImageSearchReport(
                query=query, mode=mode, hits=(),
                elapsed_ms=int((time.time() - t0) * 1000),
                meta={"error": f"{type(e).__name__}: {e}"})
        hits: list = []
        for iid, sim, meta in raw:
            hits.append(ImageSearchHit(
                image_id=iid, score=float(sim),
                origin_hash=str(meta.get("origin_hash", "") or ""),
                mime=str(meta.get("mime", "") or ""),
                text=str(meta.get("text", "") or ""),
                metadata=meta))
        return ImageSearchReport(
            query=query, mode=mode, hits=tuple(hits),
            candidates=len(hits),
            elapsed_ms=int((time.time() - t0) * 1000),
            meta={"where": where or {}})


def make_image_retriever(*, engine: Any, store: Any,
                         origin_store: Optional[Any] = None
                         ) -> ImageRetriever:
    return ImageRetriever(engine=engine, store=store,
                           origin_store=origin_store)


__all__ = ["ImageRetriever", "make_image_retriever", "DEFAULT_TOP_K"]
