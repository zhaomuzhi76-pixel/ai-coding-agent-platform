"""hybrid 检索接入 RAG（优先 hybrid，失败降级纯向量）"""
from typing import Any, List, Mapping, Optional




def _normalize_scores(hits: list) -> list:
    """有 rerank 分（>0.1）→ 保留；无 → RRF 分数归一化 + has_rerank=False"""
    if not hits:
        return hits
    has_rerank = any(float(h.get("rerank_score") or 0.0) > 0.1
                     for h in hits)
    if has_rerank:
        for h in hits:
            rr = float(h.get("rerank_score") or 0.0)
            h["_raw_score"] = rr
            h["score"] = rr
            h["has_rerank"] = True
        return hits
    top = max((float(h.get("fused_score") or h.get("score") or 0.0)
               for h in hits), default=0.0)
    if top > 0:
        for h in hits:
            raw = float(h.get("fused_score") or h.get("score") or 0.0)
            h["_raw_score"] = raw
            h["score"] = raw / top
            h["has_rerank"] = False
    return hits


def _get_hybrid_retriever() -> Optional[Any]:
    """从 runtime 动态获取 hybrid retriever（兼容多个属性名）"""
    try:
        from backend.rag.hybrid.runtime import get_hybrid_runtime
        rt = get_hybrid_runtime()
        if rt is None:
            return None
        for attr in ("retriever", "hybrid_retriever", "hybrid", "ret"):
            r = getattr(rt, attr, None)
            if r is not None and hasattr(r, "search"):
                return r
    except Exception:
        return None
    return None


def _hit_to_dict(h: Any) -> dict:
    """HybridHit / dict → dict（保留 rerank_score=0 语义）"""
    if isinstance(h, Mapping):
        d = dict(h)
    else:
        d = {}
        for k in ("chunk_id", "text", "source", "score", "fused_score",
                  "rerank_score", "rerank_rank", "vector_score",
                  "bm25_score", "page", "page_no", "metadata",
                  "doc_title", "source_path", "line_no"):
            v = getattr(h, k, None)
            if v is not None:
                d[k] = v
    if "score" not in d and "fused_score" in d:
        d["score"] = d["fused_score"]
    return d


def _fallback_vector(query: str, limit: int,
                     where: Optional[Mapping] = None,
                     rerank: bool = True) -> List[dict]:
    """降级：纯向量检索"""
    try:
        from backend.rag.multimodal.runtime import get_multimodal_rag_runtime
        rt = get_multimodal_rag_runtime()
        rep = rt.service.search(query, limit=limit, where=where,
                                rerank=rerank)
        hits = list(getattr(rep, "hits", ()) or ())
        return [_hit_to_dict(h) for h in hits if _hit_to_dict(h).get("chunk_id")]
    except Exception as e:
        print(f"[rag_integration] fallback failed: {type(e).__name__}: {e}",
              flush=True)
        return []


def hybrid_search(query: str, *, limit: int = 5,
                  where: Optional[Mapping] = None,
                  rerank: bool = True) -> List[dict]:
    """统一入口：优先 hybrid（BM25+向量+RRF+Rerank），失败降级纯向量。
    返回 list[dict]：chunk_id/text/score/rerank_score/source/page
    """
    q = (query or "").strip()
    if not q:
        return []

    ret = _get_hybrid_retriever()
    if ret is None:
        return _normalize_scores(_fallback_vector(q, limit, where, rerank))

    try:
        raw = ret.search(q, top_k=limit, where=where, rerank=rerank)
        if hasattr(raw, "hits"):
            raw = list(raw.hits or [])
        elif isinstance(raw, (list, tuple)):
            raw = list(raw)
        else:
            raw = []

        out = []
        for h in raw:
            d = _hit_to_dict(h)
            if d.get("chunk_id") or d.get("id"):
                out.append(d)

        if not out:
            return _normalize_scores(_fallback_vector(q, limit, where, rerank))
        return _normalize_scores(out)
    except TypeError:
        # 兼容不支持 where 的签名
        try:
            raw = ret.search(q, top_k=limit, rerank=rerank)
            out = []
            for h in list(raw.hits if hasattr(raw, "hits") else raw or []):
                d = _hit_to_dict(h)
                if d.get("chunk_id") or d.get("id"):
                    out.append(d)
            return _normalize_scores(out or _fallback_vector(q, limit, where, rerank))
        except Exception as e:
            print(f"[hybrid_search] no-where failed: {e}", flush=True)
            return _normalize_scores(_fallback_vector(q, limit, where, rerank))
    except Exception as e:
        print(f"[hybrid_search] failed: {type(e).__name__}: {e}",
              flush=True)
        return _normalize_scores(_fallback_vector(q, limit, where, rerank))


__all__ = ["hybrid_search"]
