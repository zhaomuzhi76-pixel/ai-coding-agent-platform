"""RAG 向量库 策展（curate） 端点。

职责：只此一类 策展（curate） 相关端点。
helper 在 vector_common.py。
"""
from __future__ import annotations
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException

from backend.api.rag.vector_common import (
    _safe_images, _collection, _store, _delete_ids,
)

router = APIRouter()


@router.post("/curate/commit")
async def curate_commit(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """把选中的 chunk 标记为 curated=true（AI 助手只用这些）"""
    keep_ids: List[str] = payload.get("keep_ids") or []
    filter_ids: List[str] = payload.get("filter_ids") or []
    coll = _collection()

    kept = 0
    filtered = 0
    # 先全部重置本次涉及的 chunk 的 curated
    try:
        if keep_ids:
            got = coll.get(ids=keep_ids, include=["metadatas"])
            metas = got.get("metadatas") or []
            new_metas = []
            for m in metas:
                mm = dict(m or {})
                mm["curated"] = True
                new_metas.append(mm)
            coll.update(ids=keep_ids, metadatas=new_metas)
            kept = len(keep_ids)
        if filter_ids:
            got = coll.get(ids=filter_ids, include=["metadatas"])
            metas = got.get("metadatas") or []
            new_metas = []
            for m in metas:
                mm = dict(m or {})
                mm["curated"] = False
                new_metas.append(mm)
            coll.update(ids=filter_ids, metadatas=new_metas)
            filtered = len(filter_ids)
    except Exception as e:
        raise HTTPException(500, f"curate 失败: {e}")

    return {"ok": True, "kept": kept, "filtered": filtered}



@router.post("/curate/reset")
async def curate_reset(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """重置：把 chunk 的 curated 恢复为 true（默认全用）"""
    chunk_ids: List[str] = payload.get("chunk_ids") or []
    coll = _collection()
    if not chunk_ids:
        return {"ok": True, "reset": 0}
    try:
        got = coll.get(ids=chunk_ids, include=["metadatas"])
        metas = got.get("metadatas") or []
        new_metas = []
        for m in metas:
            mm = dict(m or {})
            mm["curated"] = True
            new_metas.append(mm)
        coll.update(ids=chunk_ids, metadatas=new_metas)
    except Exception as e:
        raise HTTPException(500, f"reset 失败: {e}")
    return {"ok": True, "reset": len(chunk_ids)}



@router.get("/curate/stats")
async def curate_stats() -> Dict[str, Any]:
    """统计 curated / filtered 数量"""
    coll = _collection()
    try:
        r = coll.get(include=["metadatas"])
        metas = r.get("metadatas") or []
        total = len(metas)
        curated = 0
        filtered = 0
        for m in metas:
            m = m or {}
            if m.get("curated") is False:
                filtered += 1
            else:
                curated += 1
        return {"ok": True, "total": total,
                "curated": curated, "filtered": filtered}
    except Exception as e:
        raise HTTPException(500, f"stats 失败: {e}")


