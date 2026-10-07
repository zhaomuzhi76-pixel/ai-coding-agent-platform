"""RAG 检索器（L1 · 向量检索 + 可选 reranker 精排）。"""
from __future__ import annotations
from backend.core.model_registry.embedding_resolver import resolve_embedding_model
from backend.core.observability.silent import swallow

from backend.config.constants.endpoints import (
    OLLAMA_URL,
    RERANKER_URL,
)

import httpx

from backend.storage.vector_backend import get_vector_store
from backend.storage.vector_config import VectorConfig

from ._retriever_parts import _apply_recall_config  # noqa: F401
from .spec import RagHit

_EMBED_TIMEOUT = 60.0
_RERANK_TIMEOUT = 120.0


class RagRetriever:
    VERSION = "1.0"

    def __init__(
        self,
        *,
        vector_config: VectorConfig | None = None,
        embed_base_url: str = "",
        embed_model: str = "",
        rerank_url: str = RERANKER_URL,
        rerank_enabled: bool = True,
    ) -> None:
        from .indexer import _load_embed_cfg_from_yaml
        cfg_base, cfg_model = _load_embed_cfg_from_yaml()

        self.vector_config = vector_config or VectorConfig()
        self.store = get_vector_store(self.vector_config)
        self.embed_base_url = (
            embed_base_url or cfg_base or OLLAMA_URL
        ).rstrip("/")
        self.embed_model = embed_model or cfg_model or resolve_embedding_model()
        self.rerank_url = rerank_url.rstrip("/")
        self.rerank_enabled = rerank_enabled

    async def query(
        self,
        query: str,
        *,
        top_k: int = 5,
        recall_k: int = 20,
        use_rerank: bool | None = None,
    ) -> list[RagHit]:
        if not query.strip():
            return []

        top_k, use_rerank = _apply_recall_config(top_k, use_rerank)

        # clear() 后 collection 句柄可能失效 → 每次 reload 拿最新
        self.store.reload()
        q_emb = await self._embed(query)

        want_rerank = (
            self.rerank_enabled if use_rerank is None else use_rerank
        )
        recall = max(top_k, recall_k) if want_rerank else top_k

        raw = self.store.search([q_emb], limit=recall)
        hits = self._parse_search(raw)

        if not hits:
            return []

        if want_rerank and len(hits) > top_k:
            try:
                hits = await self._rerank(query, hits, top_k)
            except Exception as exc:
                print(
                    f"[retriever] rerank failed: {exc}", flush=True
                )
                hits = hits[:top_k]
        else:
            hits = hits[:top_k]

        return hits

    _embed_cache: dict = {}
    _embed_cache_max: int = 64

    async def _embed(self, text: str) -> list[float]:
        import hashlib as _h
        key = _h.sha1(text.encode("utf-8")).hexdigest()[:16]
        cached = self._embed_cache.get(key)
        if cached is not None:
            return cached
        return await self._embed_uncached(text)

    async def _embed_uncached(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=_EMBED_TIMEOUT) as c:
            r = await c.post(
                f"{self.embed_base_url}/api/embed",
                json={"model": self.embed_model, "input": [text]},
            )
            r.raise_for_status()
            d = r.json()
        embs = d.get("embeddings") or []
        if not embs:
            raise RuntimeError("embedding empty")
        vec = embs[0]
        # 写缓存
        import hashlib as _h
        key = _h.sha1(text.encode("utf-8")).hexdigest()[:16]
        if len(self._embed_cache) >= self._embed_cache_max:
            self._embed_cache.clear()
        self._embed_cache[key] = vec
        return vec

    def _parse_search(self, raw: dict) -> list[RagHit]:
        ids = (raw.get("ids") or [[]])[0]
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        dists = (raw.get("distances") or [[]])[0]
        out: list[RagHit] = []
        for i, cid in enumerate(ids):
            text = docs[i] if i < len(docs) else ""
            md = (
                metas[i]
                if i < len(metas) and isinstance(metas[i], dict)
                else {}
            )
            dist = dists[i] if i < len(dists) else 1.0
            score = max(0.0, 1.0 - float(dist))
            out.append(RagHit(
                chunk_id=str(cid),
                text=str(text),
                score=score,
                source=str(md.get("source", "")),
                source_path=str(md.get("source_path", "")),
                line_no=int(md.get("line_no", 0) or 0),
                role=str(md.get("role", "")),
                metadata=dict(md),
            ))
        return out

    async def _rerank(
        self, query: str, hits: list[RagHit], top_k: int,
    ) -> list[RagHit]:
        docs = [h.text for h in hits]
        async with httpx.AsyncClient(timeout=_RERANK_TIMEOUT) as c:
            r = await c.post(
                f"{self.rerank_url}/rerank",
                json={
                    "query": query,
                    "documents": docs,
                    "top_k": top_k,
                },
            )
            r.raise_for_status()
            d = r.json()
        results = d.get("results") or []
        out: list[RagHit] = []
        for item in results:
            idx = int(item.get("index", 0))
            if 0 <= idx < len(hits):
                h = hits[idx]
                out.append(RagHit(
                    chunk_id=h.chunk_id,
                    text=h.text,
                    score=float(item.get("score", h.score)),
                    source=h.source,
                    source_path=h.source_path,
                    line_no=h.line_no,
                    role=h.role,
                    metadata=h.metadata,
                ))
        return out

    def count(self) -> int:
        try:
            self.store.reload()
            return int(self.store.count())
        except Exception:
            return 0

    _rerank_health_cache: dict = {}
    _rerank_health_ts: float = 0.0
    _RERANK_CACHE_TTL: float = 30.0   # 缓存 30 秒

    async def rerank_health(self) -> dict:
        """双路探测（带 30s 缓存 + 0.8s 超时）。
        避免前端轮询 /api/rag/status 时反复超时刷 warning。
        """
        import time as _time
        now = _time.monotonic()
        if (self._rerank_health_cache
                and (now - self._rerank_health_ts) < self._RERANK_CACHE_TTL):
            return self._rerank_health_cache

        result = await self._probe_rerank_health()
        self.__class__._rerank_health_cache = result
        self.__class__._rerank_health_ts = _time.monotonic()
        return result

    async def _probe_rerank_health(self) -> dict:
        # 1. 独立 HTTP 服务（超时 0.8s，够用且不刷屏）
        try:
            async with httpx.AsyncClient(timeout=0.8) as c:
                r = await c.get(f"{self.rerank_url}/health")
                if r.status_code == 200:
                    return {"ok": True, "mode": "http",
                            "url": self.rerank_url,
                            "status": r.status_code}
        except Exception as e:
            # [SILENT] 静默：只 debug 级别，不刷 warning
            import logging
            logging.getLogger(__name__).debug(
                "rerank 9033 探测失败（静默）: %r", e)

        # 2. L23 本地 loader（内存 gguf）
        try:
            from backend.rag.ingest.review.review.reranker_loader import (
                get_default_loader,
            )
            loader = get_default_loader()
            models = loader.list_models()
            if models:
                return {"ok": True, "mode": "local",
                        "models": [m["model_id"] for m in models],
                        "count": len(models)}
        except Exception as e:
            return {"ok": False, "error": f"local loader: {e}"}

        return {"ok": False, "error": "no reranker available (http + local)"}


__all__ = ["RagRetriever"]
