"""CLIP 多模态 RAG 真运行时（工业级）。

职责：组装 embedder + store + service，暴露 .service.search()。
模式：懒加载单例；RAG_MULTIMODAL_ENABLED=1 才启用。
不做：不改 hybrid_search 主链路；不调 LLM。
"""
from __future__ import annotations
import logging
import os

logger = logging.getLogger(__name__)

_ENV_ENABLED = "RAG_MULTIMODAL_ENABLED"
_ENV_PERSIST = "RAG_MULTIMODAL_PERSIST"


def _enabled() -> bool:
    return os.environ.get(_ENV_ENABLED, "0") == "1"


def _wrap_embed(emb):
    """兼容两种 embed_fn 调用：str→List[float]，List[str]→List[List[float]]。"""
    def _fn(x):
        if isinstance(x, str):
            return emb.encode_text(x)
        try:
            return emb.encode_texts(list(x))
        except Exception:
            return [emb.encode_text(t) for t in x]
    return _fn

class _Reply:
    def __init__(self, hits):
        self.hits = tuple(hits)


class _ServiceAdapter:
    """适配 service.search → .search(query, limit, where, rerank)。"""
    def __init__(self, service):
        self._svc = service

    def search(self, query, *, limit=10, where=None, rerank=True):
        # service.search() 返回 SearchReport（含 .hits）
        rep = self._svc.search(query, limit=limit)
        hits = getattr(rep, "hits", None)
        if hits is None:
            hits = rep if isinstance(rep, (list, tuple)) else []
        return _Reply(tuple(hits))

    def index_items(self, items, **kw):
        return self._svc.index_items(items, **kw)

    def index_text(self, text, **kw):
        return self._svc.index_text(text, **kw)

    def count(self):
        return self._svc.count()

    def status(self):
        try:
            return self._svc.status()
        except Exception:
            return None


class ClipRuntime:
    def __init__(self):
        self._service = None
        self._embedder = None

    def _build(self):
        if self._service is not None:
            return
        from backend.rag.multimodal.clip_embedder import get_embedder
        from backend.rag.multimodal.memory_store import make_store
        from backend.rag.multimodal.service import make_service
        self._embedder = get_embedder()
        persist = os.environ.get(_ENV_PERSIST) or None
        store = make_store(name="mm_clip", persist_path=persist)
        self._service = make_service(vector_store=store,
                                     embed_fn=_wrap_embed(self._embedder))
        logger.info("[mm] ClipRuntime ready (persist=%s)", persist)

    @property
    def service(self):
        self._build()
        return _ServiceAdapter(self._service)

    @property
    def embedder(self):
        self._build()
        return self._embedder


_singleton = None


def get_clip_runtime() -> ClipRuntime:
    global _singleton
    if _singleton is None:
        _singleton = ClipRuntime()
    return _singleton


def is_clip_enabled() -> bool:
    return _enabled()


__all__ = ["ClipRuntime", "get_clip_runtime", "is_clip_enabled"]
