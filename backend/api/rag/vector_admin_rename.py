"""向量源重命名端点。职责：给某个 source 的所有 chunk 打 user_title。
独立文件，挂载到 vector_admin_router 的 router 上。
"""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/rag", tags=["rag-vector-rename"])


class RenameBody(BaseModel):
    match_values: list[str] = []      # 从 sources 返回的 match_values 里选
    chunk_ids: list[str] = []          # 或直接给 chunk_ids
    new_title: str


def _collection():
    from backend.storage.vector_backend import get_vector_store
    from backend.storage.vector_config import VectorConfig
    store = get_vector_store(VectorConfig())
    coll = getattr(store, "collection", None)
    if coll is None:
        raise RuntimeError(f"{type(store).__name__} 无 .collection")
    return coll, store


@router.post("/vectors/source-rename")
async def rename_source(body: RenameBody) -> Dict[str, Any]:
    """把命中 match_values / chunk_ids 的所有 chunk 的 user_title 设为 new_title。"""
    if not body.new_title.strip():
        raise HTTPException(400, "new_title 不能为空")
    coll, store = _collection()

    # 1. 收集目标 chunk_ids
    target_ids: set[str] = set(body.chunk_ids or [])
    if body.match_values:
        # Lite: 遍历全部；Chroma: 用 where
        try:
            all_data = coll.get()
        except Exception as e:
            raise HTTPException(500, f"读取失败: {e}")
        ids = all_data.get("ids") or []
        metas = all_data.get("metadatas") or []
        for i, m in enumerate(metas):
            m = m or {}
            for k in ("source_path", "doc_path", "source",
                      "filename", "doc_title"):
                v = str(m.get(k, ""))
                if v and v in body.match_values:
                    target_ids.add(ids[i]); break
    if not target_ids:
        raise HTTPException(404, "无匹配的 chunk")

    # 2. 逐个更新 user_title（Lite / Chroma 通用）
    target_ids = list(target_ids)
    updated = 0
    if hasattr(store, "_conn"):   # Lite 分支：直接 SQL
        import json
        cur = store._conn.cursor()
        for cid in target_ids:
            row = cur.execute(
                "SELECT metadata FROM docs WHERE id=?", (cid,)).fetchone()
            if not row: continue
            try: meta = json.loads(row[0] or "{}")
            except Exception: meta = {}
            meta["user_title"] = body.new_title
            cur.execute("UPDATE docs SET metadata=? WHERE id=?",
                        (json.dumps(meta, ensure_ascii=False), cid))
            updated += 1
        store._conn.commit()
        store._cache = None
    else:                          # Chroma 分支：读-改-写 metadata
        got = coll.get(ids=target_ids)
        ids_g = got.get("ids") or []
        docs_g = got.get("documents") or [""] * len(ids_g)
        metas_g = got.get("metadatas") or [{}] * len(ids_g)
        embs = None
        try:
            eg = coll.get(ids=target_ids, include=["embeddings"])
            embs = eg.get("embeddings")
        except Exception:
            pass
        new_metas = []
        for m in metas_g:
            m = dict(m or {}); m["user_title"] = body.new_title
            new_metas.append(m)
        if embs:
            coll.update(ids=ids_g, metadatas=new_metas, embeddings=embs)
        else:
            coll.update(ids=ids_g, metadatas=new_metas)
        updated = len(ids_g)

    return {"ok": True, "updated": updated, "new_title": body.new_title}


__all__ = ["router"]
