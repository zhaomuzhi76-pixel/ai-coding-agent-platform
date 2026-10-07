"""召回测试 API —— 重排序 + 召回可视化后端。"""
from __future__ import annotations

import importlib
import time
from typing import Any, Optional

from backend.rag.hybrid.contracts import FusionStrategy
from backend.rag.hybrid.fusion import (
    DEFAULT_BM25_WEIGHT, DEFAULT_RRF_K, DEFAULT_VECTOR_WEIGHT, fuse,
)

DEFAULT_FETCH_K = 10  # 精排候选池（越大越慢）
DEFAULT_TOP_K = 10
_BUILTIN_RR = "builtin-qwen3-reranker"


class RecallTestApi:
    def __init__(self, retriever: Any = None, bm25_index: Any = None) -> None:
        self._retriever = retriever
        self._bm25 = bm25_index if bm25_index is not None else _resolve_bm25()

    def models(self) -> dict:
        return {
            "models": [
                {"model_id": _BUILTIN_RR, "label": "Qwen3-Reranker-4B（内置）",
                 "backend_kind": "builtin", "selectable": True},
                {"model_id": "none", "label": "不精排（仅 RRF）",
                 "backend_kind": "none", "selectable": True},
            ],
            "default": _BUILTIN_RR,
        }

    async def query(self, *, query: str, top_k: int = DEFAULT_TOP_K,
                    use_reranker: bool = True,
                    reranker_model_id: str = _BUILTIN_RR,
                    rrf_k: int = DEFAULT_RRF_K,
                    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
                    bm25_weight: float = DEFAULT_BM25_WEIGHT,
                    strategy: str = "rrf") -> dict:
        q = (query or "").strip()
        if not q:
            return _err("empty query")
        t0 = time.monotonic()

        vec_hits, vec_err = await self._fetch_vector(q)
        bm25_hits, bm25_err = self._fetch_bm25(q)

        try:
            fused = fuse(query=q, vector_hits=vec_hits, bm25_hits=bm25_hits,
                         strategy=FusionStrategy(strategy), top_k=max(top_k, 5),  # 精排池 = 用户 top_k（最少 5）
                         rrf_k=rrf_k, vector_weight=vector_weight,
                         bm25_weight=bm25_weight)
        except Exception as e:
            return _err(f"fusion failed: {e}")

        rerank_map, reranked, rr_err = _do_rerank(q, fused, use_reranker,
                                                  reranker_model_id)
        if rr_err:
            bm25_err = (bm25_err + " | " + rr_err) if bm25_err else rr_err

        ordered = (sorted(fused, key=lambda h: -rerank_map.get(h.chunk_id, 0.0))
                   if reranked else list(fused))
        top = ordered[:top_k]

        v_max = max((h.vector_score for h in fused), default=0.0)
        b_max = max((h.bm25_score for h in fused), default=0.0)
        r_max = max(rerank_map.values(), default=0.0) if rerank_map else 0.0

        hits = []
        for rank, h in enumerate(top, 1):
            hits.append({
                "chunk_id": h.chunk_id, "content": h.text,
                "source": h.source, "line_no": h.line_no,
                "vector": round(h.vector_score, 4),
                "vector_rank": h.vector_rank,
                "vector_bar": _norm(h.vector_score, v_max),
                "bm25": round(h.bm25_score, 4),
                "bm25_rank": h.bm25_rank,
                "bm25_bar": _norm(h.bm25_score, b_max),
                "rerank": round(rerank_map.get(h.chunk_id, 0.0), 4),
                "rerank_rank": rank if reranked else None,
                "rerank_bar": _norm(rerank_map.get(h.chunk_id, 0.0), r_max),
                "fused": round(h.fused_score, 6),
                "fused_rank": rank,
            })

        return {
            "query": q,
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
            "params_used": {
                "top_k": top_k, "use_reranker": use_reranker,
                "reranker_model_id": reranker_model_id,
                "rrf_k": rrf_k, "vector_weight": vector_weight,
                "bm25_weight": bm25_weight, "strategy": strategy,
            },
            "counts": {
                "vector": len(vec_hits), "bm25": len(bm25_hits),
                "fused": len(fused), "returned": len(hits),
            },
            "reranked": reranked,
            "errors": {"vector": vec_err, "bm25": bm25_err},
            "hits": hits,
        }

    async def _fetch_vector(self, query: str) -> tuple[list, str]:
        if self._retriever is None:
            return [], "retriever unavailable"
        try:
            q_emb = await self._retriever._embed(query)
            self._retriever.store.reload()
            raw = self._retriever.store.search([q_emb], limit=DEFAULT_FETCH_K)
            return list(self._retriever._parse_search(raw)), ""
        except Exception as e:
            return [], f"{type(e).__name__}: {e}"

    def _fetch_bm25(self, query: str) -> tuple[list, str]:
        if self._bm25 is None:
            return [], "bm25 unavailable"
        try:
            return list(self._bm25.search(query, top_k=DEFAULT_FETCH_K)), ""
        except Exception as e:
            return [], f"{type(e).__name__}: {e}"


def _do_rerank(query: str, fused: list, use: bool,
               model_id: str) -> tuple[dict, bool, str]:
    if not use or not fused or model_id == "none":
        return {}, False, ""
    try:
        from backend.rag.ingest.review.review.reranker_loader import (
            get_default_loader,
        )
        loader = get_default_loader()
        if loader.has(model_id):
            scores = loader.rerank(model_id, query, [h.text for h in fused])
        else:
            from backend.rag.ingest.review.review.reranker_adapter import (
                build_reranker,
            )
            rr = build_reranker()
            if rr.backend != "real":
                return {}, False, f"model {model_id} not available"
            scores = rr.rerank(query, [h.text for h in fused])
        mp = {fused[i].chunk_id: float(scores[i])
              for i in range(min(len(fused), len(scores)))}
        if all(v == 0.0 for v in mp.values()):
            return {}, False, "reranker returned all zeros"
        return mp, True, ""
    except Exception as e:
        return {}, False, f"rerank: {e}"


def _norm(v: float, mx: float) -> float:
    return 0.0 if mx <= 0 else min(v / mx, 1.0)


def _err(msg: str) -> dict:
    return {"query": "", "elapsed_ms": 0, "params_used": {},
            "counts": {"vector": 0, "bm25": 0, "fused": 0, "returned": 0},
            "reranked": False, "errors": {"vector": msg, "bm25": ""},
            "hits": []}


def _resolve_bm25() -> Optional[Any]:
    candidates = (
        ("backend.rag.hybrid.bm25_sync", "get_default_bm25"),
        ("backend.rag.hybrid.bm25_sync", "get_bm25"),
        ("backend.rag.indexer", "get_bm25_index"),
        ("backend.rag.hybrid.bm25_index", "make_bm25_index"),
    )
    for mod_name, fn_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            try:
                inst = fn()
                if inst is not None:
                    return inst
            except Exception:
                continue
    return None


def build_default() -> RecallTestApi:
    try:
        from backend.rag.retriever import RagRetriever
        return RecallTestApi(retriever=RagRetriever())
    except Exception:
        return RecallTestApi()
