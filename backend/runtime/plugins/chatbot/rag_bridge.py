"""Chatbot ↔ RAG 桥。职责：调 L7.4 service 检索 → 生成 context_text + ImageArtifact。
不做 HTTP、不做向量、不做切片、不组装最终响应。"""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional

from backend.providers.multimodal.contracts import ImageArtifact, ImageSource

# 默认值（从 backend/config/rag_governance 读；env 可覆盖）
from backend.config.rag_governance import get_rag_config as _get_rag_cfg
_CFG = _get_rag_cfg()
DEFAULT_TOP_K = _CFG.default_top_k
MAX_CONTEXT_CHARS = _CFG.max_context_chars

@dataclass(frozen=True)
class RagContext:
    query: str
    context_text: str
    images: tuple
    hit_count: int
    meta: Mapping[str, Any] = field(default_factory=dict)
    raw_hits: tuple = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))

    @property
    def has_context(self) -> bool:
        return bool(self.context_text) and self.hit_count > 0


def _get(h, key: str, default=None):
    """hits 可能是 dict 或对象，统一取字段"""
    if isinstance(h, dict):
        return h.get(key, default)
    return getattr(h, key, default)

def _empty(query: str, **meta: Any) -> RagContext:
    return RagContext(query=query, context_text="", images=(),
                      hit_count=0, meta=meta)

def _img_ref_to_artifact(ref: Any, idx: int) -> Optional[ImageArtifact]:
    try:
        return ImageArtifact(
            id=getattr(ref, "id", None) or f"rag-{idx}",
            mime=getattr(ref, "mime", None) or "image/png",
            source=ImageSource.RETRIEVED,
            url=getattr(ref, "url", None),
            b64=getattr(ref, "b64", None),
            alt_text=getattr(ref, "alt_text", "") or "",
        )
    except Exception:
        return None

def _enrich_curated(hits: list) -> None:
    """给每个 hit 补 curated 标记（从 Chroma metadata 读）"""
    try:
        from backend.storage.vector_backend import get_vector_store
        from backend.storage.vector_config import VectorConfig
        store = get_vector_store(VectorConfig())
        coll = store.collection
        ids = []
        for h in hits:
            cid = getattr(h, "chunk_id", None) or getattr(h, "id", None)
            if cid:
                ids.append(cid)
        if not ids:
            return
        got = coll.get(ids=ids, include=["metadatas"])
        curated_map = {}
        for i, cid in enumerate(got.get("ids") or []):
            m = (got.get("metadatas") or [{}])[i] or {}
            curated_map[cid] = m.get("curated", True) is not False
        for h in hits:
            cid = getattr(h, "chunk_id", None) or getattr(h, "id", None)
            if cid in curated_map:
                try:
                    setattr(h, "_curated", curated_map[cid])
                except Exception:
                    pass
    except Exception:
        pass


def _hit_field(h: Any, *names, default=""):
    for n in names:
        v = (h.get(n) if isinstance(h, dict) else getattr(h, n, None))
        if v not in (None, "", 0.0):
            return v
    return default


def _format_hit(idx: int, h: Any) -> str:
    text = str(_hit_field(h, "text", "content") or "").strip()
    src = _hit_field(h, "source", "source_path", "doc_title") or ""
    score = float(_hit_field(h, "rerank_score", "fused_score",
                             "score", default=0.0) or 0.0)
    page = _hit_field(h, "page", "page_no", "line_no", default=0) or 0
    head = f"[{idx + 1}]"
    if src:
        head += f" {src}"
    if page:
        head += f" p.{page}"
    head += f" score={score:.3f}"
    return f"{head}\n{text}" if text else head

class RagBridge:
    def __init__(self, service: Any, top_k: int = DEFAULT_TOP_K,
                 max_context_chars: int = MAX_CONTEXT_CHARS) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be > 0")
        if max_context_chars <= 0:
            raise ValueError("max_context_chars must be > 0")
        self._svc = service
        self._top_k = top_k
        self._max = max_context_chars

    def _fallback_vector_search(self, q: str, limit: int,
                                 where=None, rerank: bool = True) -> list:
        """降级：直接调 service.search 拿 hits"""
        try:
            rep = self._svc.search(q, limit=limit, rerank=rerank,
                                    where=where)
        except TypeError:
            rep = self._svc.search(q, limit=limit, rerank=rerank)
        except Exception as e:
            print(f"[rag_bridge] fallback failed: {e}", flush=True)
            return []
        raw = list(getattr(rep, "hits", ()) or ())
        out = []
        for h in raw:
            if isinstance(h, dict):
                out.append(dict(h))
                continue
            item = {}
            for k in ("chunk_id", "text", "source", "score",
                      "rerank_score", "page", "page_no"):
                v = getattr(h, k, None)
                if v is not None:
                    item[k] = v
            if item.get("chunk_id"):
                out.append(item)
        return out

    def retrieve(self, query: str, *, rerank: bool = True,
                 domains=None, curated_first: bool = True) -> RagContext:
        q = (query or "").strip()
        if not q:
            return _empty(q, skipped="empty_query")
        if self._svc is None:
            return _empty(q, skipped="no_service")

        # 领域过滤（空 = 全领域）
        where = None
        if domains:
            dlist = [d for d in domains if d]
            if dlist:
                where = {"kb": {"$in": dlist}}

        # 多拉候选（用于 curated 加权后截断）
        fetch_n = self._top_k * 3 if curated_first else self._top_k

        # ★ 优先 hybrid（BM25+向量+RRF+Rerank），失败降级纯向量
        try:
            from backend.rag.hybrid.rag_integration import hybrid_search
            hybrid_hits = hybrid_search(q, limit=fetch_n, where=where,
                                        rerank=rerank)
        except Exception as e:
            print(f"[rag_bridge] hybrid import/call failed: {e}", flush=True)
            hybrid_hits = []

        if hybrid_hits:
            hits = hybrid_hits
        else:
            hits = self._fallback_vector_search(q, fetch_n, where, rerank)

        if not hits:
            return _empty(q, empty=True)

        # curated 优先排序
        if curated_first and len(hits) > 1:
            _enrich_curated(hits)
            def _sort_key(h):
                base = float(getattr(h, "score", 0.0) or 0.0)
                cur = getattr(h, "_curated", None)
                bonus = 0.15 if cur is True else (0.0 if cur is None else -0.05)
                return -(base + bonus)
            hits.sort(key=_sort_key)
            hits = hits[:self._top_k]
        parts = [_format_hit(i, h) for i, h in enumerate(hits)]
        ctx = "\n\n".join(parts)
        if len(ctx) > self._max:
            ctx = ctx[:self._max] + "..."
        imgs: list = []
        for i, h in enumerate(hits):
            for j, ref in enumerate(getattr(h, "images", ()) or ()):
                a = _img_ref_to_artifact(ref, i * 100 + j)
                if a is not None:
                    imgs.append(a)
        return RagContext(query=q, context_text=ctx, images=tuple(imgs),
                          hit_count=len(hits),
                          raw_hits=tuple(hits),
                          meta={"reranked": bool(hits and hits[0].get("rerank_score"))})

def make_rag_bridge(service: Any, top_k: int = DEFAULT_TOP_K) -> RagBridge:
    return RagBridge(service=service, top_k=top_k)

__all__ = ["RagContext", "RagBridge", "make_rag_bridge"]
