"""RAG 向量库 详情（分块查看/删除） 端点。

职责：只此一类 详情（分块查看/删除） 相关端点。
helper 在 vector_common.py。
"""
from __future__ import annotations
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException

from backend.api.rag.vector_common import (
    _safe_images, _collection, _store, _delete_ids,
)

router = APIRouter()


@router.post("/vectors/source-detail")
async def source_detail(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """查看单个文档的所有分块详情"""
    chunk_ids: List[str] = payload.get("chunk_ids") or []
    match_values: List[str] = payload.get("match_values") or []
    coll = _collection()

    # 找该文档所有块
    all_ids: List[str] = list(chunk_ids)
    if not all_ids and match_values:
        for val in match_values:
            for field in ("source_path", "doc_path", "source", "doc_title"):
                got = coll.get(where={field: val}, include=[])
                ids = got.get("ids") or []
                if ids:
                    all_ids = ids
                    break
            if all_ids:
                break

    if not all_ids:
        raise HTTPException(404, "未找到该文档的分块")

    # 拉取完整数据
    res = coll.get(ids=all_ids, include=["metadatas", "documents"])
    ids_out = res.get("ids") or []
    metas = res.get("metadatas") or []
    docs = res.get("documents") or []

    # 尝试拿 embedding 维度（单独查一个）
    dim = 0
    try:
        one = coll.get(ids=[ids_out[0]], include=["embeddings"])
        embs = one.get("embeddings")
        if embs is not None and len(embs) > 0:
            dim = len(embs[0])
    except Exception:
        pass

    chunks = []
    for i, cid in enumerate(ids_out):
        m = metas[i] if i < len(metas) else {}
        text = docs[i] if i < len(docs) else ""
        chunks.append({
            "chunk_id": cid,
            "text": (text or "")[:2000],
            "text_len": (m or {}).get("text_len", len(text or "")),
            "page_no": (m or {}).get("page_no"),
            "line_no": (m or {}).get("line_no"),
            "section": (m or {}).get("section", ""),
            "doc_title": (m or {}).get("doc_title", ""),
            "doc_path": (m or {}).get("doc_path", ""),
            "source": (m or {}).get("source", ""),
            "source_path": (m or {}).get("source_path", ""),
            "origin_hash": (m or {}).get("origin_hash", ""),
            "image_count": (m or {}).get("image_count", 0),
            "kb": (m or {}).get("kb", ""),
            "role": (m or {}).get("role", ""),
            "doc_hash": (m or {}).get("doc_hash", ""),
            "images": _safe_images(m),           # [IMG_RETURN]
            "metadata": dict(m or {}),           # [IMG_RETURN] 原始 metadata
        })

    # 按 page_no 排序
    chunks.sort(key=lambda c: (c["page_no"] or 0, c["chunk_id"]))

    title = ""
    for c in chunks:
        if c["doc_title"]:
            title = c["doc_title"]
            break

    return {
        "ok": True,
        "title": title,
        "total": len(chunks),
        "embedding_dim": dim,
        "chunks": chunks,
    }



@router.post("/vectors/chunk/delete")
async def chunk_delete(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """删除单个分块"""
    chunk_id = (payload.get("chunk_id") or "").strip()
    if not chunk_id:
        raise HTTPException(400, "chunk_id required")
    coll = _collection()
    try:
        coll.delete(ids=[chunk_id])
    except Exception as e:
        raise HTTPException(500, f"删除失败: {e}")
    return {"ok": True, "chunk_id": chunk_id}


# ============================================================
# Curation：召回测试 → 人工筛选 → 固化 → AI 只用精选数据
# ============================================================

