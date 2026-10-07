"""RAG 向量库 召回测试 端点。

职责：只此一类 召回测试 相关端点。
helper 在 vector_common.py。
"""
from __future__ import annotations
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException

from backend.api.rag.vector_common import (
    _safe_images, _collection, _store, _delete_ids,
)

router = APIRouter()


@router.post("/recall-filtered")
async def recall_filtered(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """召回测试：支持 domains 过滤 + sources 过滤 + curated 过滤"""
    query = (payload.get("query") or "").strip()
    if not query:
        raise HTTPException(400, "query required")
    top_k = int(payload.get("top_k", 5))
    use_rerank = bool(payload.get("rerank", True))
    source_filter: List[str] = payload.get("sources") or []
    only_curated = bool(payload.get("only_curated", False))
    domains: List[str] = payload.get("domains") or []

    coll = _collection()

    # 1) 通过 embedding 直接 Chroma query（带 where 过滤）
    hits: List[Dict[str, Any]] = []
    try:
        import httpx
        from backend.core.model_registry.embedding_resolver import resolve_embedding_model
        model_name = resolve_embedding_model()
        async with httpx.AsyncClient(timeout=60) as client:
            er = await client.post(
                "http://127.0.0.1:11434/api/embeddings",
                json={"model": model_name, "prompt": query},
            )
            emb = er.json().get("embedding")
        if not emb:
            raise RuntimeError("embedding 为空")

        kwargs: Dict[str, Any] = {
            "query_embeddings": [emb],
            "n_results": max(top_k * 5, 30),
        }
        # domains 过滤：Chroma 层直接过滤
        if domains:
            kwargs["where"] = {"kb": {"$in": domains}}
        # [CONTRACT] 用统一契约（后端无关）
        from backend.storage.vector_contract import query as _vq
        _st = _store()
        # [HYBRID] 混合检索（向量 + BM25 + RRF）；失败降级纯向量
        try:
            import os as _os_h
            _mult = int(_os_h.environ.get("RAG_RECALL_FETCH_MULT", "20"))
            _n_src = max(1, len(source_filter))
            _min_k = int(_os_h.environ.get("RAG_RECALL_MIN_FETCH_K", "100"))
            _per_src = int(_os_h.environ.get("RAG_RECALL_PER_SRC_K", "20"))
            # [SRC] 有源过滤时，融合后目标源可能排位很靠后（RRF 融合不稳定），
            #       fetch_k 需要更大，确保覆盖所有选中源的命中
            _with_src_k = int(_os_h.environ.get(
                "RAG_RECALL_FETCH_WITH_SRC_K", "2000"))
            if source_filter:
                _fetch_k = max(top_k * _mult, _min_k,
                               _n_src * _per_src, _with_src_k)
            else:
                _fetch_k = max(top_k * _mult, _min_k)
            print(f"[recall] top_k={top_k} n_src={_n_src} fetch_k={_fetch_k}",
                  flush=True)
            from backend.rag.hybrid.rag_integration import hybrid_search
            try:
                from backend.rag.hybrid.runtime import ensure_synced
                ensure_synced()
            except Exception:
                pass
            _where_h = {"kb": {"$in": domains}} if domains else None
            _hy = hybrid_search(query, limit=_fetch_k,
                                where=_where_h, rerank=False)

            def _enrich(h):
                m = dict(h.get("metadata") or {})
                for _k in ("doc_title", "user_title", "filename",
                           "source_path", "doc_path", "page_no",
                           "kb", "domain", "curated",
                           "__images_json__"):  # [RECALL_IMG] 让 images 透传
                    if _k not in m and h.get(_k) is not None:
                        m[_k] = h.get(_k)
                return m

            res = {
                "ids": [[(h.get("chunk_id") or h.get("id") or "") for h in _hy]],
                "metadatas": [[_enrich(h) for h in _hy]],
                "documents": [[(h.get("text") or "") for h in _hy]],
                "distances": [[(1.0 - float(h.get("score") or 0)) for h in _hy]],
            }
        except Exception as _e:
            print(f"[recall] hybrid 失败，降级纯向量: {_e}", flush=True)
            res = _vq(_st, query_embeddings=[emb],
                      n_results=max(top_k * 5, 30),
                      where=kwargs.get('where'))

        ids = (res.get("ids") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for i, cid in enumerate(ids):
            m = metas[i] if i < len(metas) else {}
            hits.append({
                "chunk_id": cid,
                "score": 1.0 - (dists[i] if i < len(dists) else 1.0),
                "text": docs[i] if i < len(docs) else "",
                "images": _safe_images(m),  # [RECALL_IMG] 统一契约：无图返回 []
                "kb": m.get("kb", ""),
                "domain": m.get("domain", ""),
                "curated": m.get("curated", True) is not False,
                # [TITLE] 优先用户友好名
                "doc_title": (
                    m.get("user_title")
                    or (m.get("filename") or "").rsplit(".", 1)[0]
                    or m.get("doc_title")
                    or ""
                ),
                "page": m.get("page_no"),
                "source": m.get("source_path") or m.get("doc_path") or "",
                # [MATCH] 供过滤用的全部候选字段
                "_match_text": " ".join([
                    str(m.get("source_path") or ""),
                    str(m.get("doc_path") or ""),
                    str(m.get("doc_title") or ""),
                    str(m.get("user_title") or ""),
                    str(m.get("filename") or ""),
                ]).lower(),
            })
    except Exception as e:
        raise HTTPException(500, f"Chroma 检索失败: {type(e).__name__}: {e}")

    # 2) Python 层再兜底过滤（防止 Chroma where 不生效）
    filtered = []
    for h in hits:
        if domains:
            hit_kb = (h.get("kb") or "").strip()
            hit_dom = (h.get("domain") or "").strip()
            if hit_kb not in domains and hit_dom not in domains:
                continue
        if source_filter:
            # [FIX] 用 _match_text 匹配任意字段
            # [TOKEN] 单词边界匹配（避免 "1" 误匹配 "11"）
            import re as _re
            _mt = h.get("_match_text") or ""
            _hit = False
            for sv in source_filter:
                # 边界：字符串首尾 / 空格 / 分隔符
                if _re.search(r'(^|[\s|])' + _re.escape(sv.lower())
                              + r'($|[\s|])', _mt):
                    _hit = True
                    break
            if not _hit:
                continue
        filtered.append(h)
    # 3) 重排序（可选）
    if use_rerank and filtered:
        try:
            from backend.rag.ingest.review.review.reranker_loader import get_reranker
            rr = get_reranker()
            texts = [h.get("text", "") for h in filtered]
            scores = rr.rerank(query, texts)
            for h, s in zip(filtered, scores):
                h["rerank_score"] = float(s)
        except Exception:
            pass

    # 4) 排序 + 截断
    filtered.sort(key=lambda x: -(
        x.get("rerank_score") if x.get("rerank_score") is not None
        else (x.get("score") or 0)
    ))
    filtered = filtered[:top_k]

    return {
        "ok": True,
        "query": query,
        "top_k": top_k,
        "rerank": use_rerank,
        "hits": filtered,
        "source_filter": source_filter,
        "only_curated": only_curated,
        "domains": domains,
        "total_candidates": len(hits),
    }
