"""RAG 向量库 管理（源列表/删除） 端点。

职责：只此一类 管理（源列表/删除） 相关端点。
helper 在 vector_common.py。
"""
from __future__ import annotations
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException

from backend.api.rag.vector_common import (
    _safe_images, _collection, _store, _delete_ids,
)

router = APIRouter()


@router.get("/vectors/sources")
async def list_sources() -> Dict[str, Any]:
    """列出所有已入库文档（按 source_path / doc_path 分组）"""
    coll = _collection()
    try:
        data = coll.get(include=["metadatas"])
    except Exception as e:
        raise HTTPException(500, f"Chroma 读取失败: {e}")

    metadatas: List[dict] = data.get("metadatas") or []
    # [PENDING_FILTER] 过滤未完成 job 的 chunk
    _metadatas_raw = metadatas
    metadatas = [m for m in _metadatas_raw
                 if not (m or {}).get("_job_pending")]
    _skipped = len(_metadatas_raw) - len(metadatas)
    ids: List[str] = data.get("ids") or []

    # 过滤函数：临时文件名视为无效
    def _is_temp(v: str) -> bool:
        return (not v) or v.startswith("ragup_") or v.startswith("/tmp/")

    def _clean(v: str) -> str:
        """取文件名部分"""
        if not v:
            return ""
        return v.split("/")[-1]

    groups: Dict[str, Dict[str, Any]] = {}
    for i, m in enumerate(metadatas):
        m = m or {}

        # 分组键优先级（人类可读优先）：
        #   filename > user_title > doc_title > doc_hash > ...
        fn = (m.get("filename") or "").strip()           # [FIX] 上传原文件名
        ut = (m.get("user_title") or "").strip()         # [FIX] 用户自定义名
        dt = (m.get("doc_title") or "").strip()
        dh = (m.get("doc_hash") or "").strip()
        dp = (m.get("doc_path") or "").strip()
        sp = (m.get("source_path") or "").strip()
        sc = (m.get("source") or "").strip()

        if ut:                                            # 用户手工命名最优先
            key = "user:" + ut
            title = ut
        elif fn and not _is_temp(fn):                     # 真实上传文件名
            key = "file:" + fn
            title = fn
        elif dt and not _is_temp(dt):
            key = "title:" + dt
            title = dt
        elif dh:
            key = "hash:" + dh
            title = dt or _clean(dp) or _clean(sp) or _clean(sc) or "未命名"
        elif dp and not _is_temp(dp):
            key = "path:" + dp
            title = _clean(dp)
        elif sp and not _is_temp(sp):
            key = "spath:" + sp
            title = _clean(sp)
        else:
            key = "src:" + (sc or "unknown")
            title = _clean(sc) or "未命名"

        g = groups.setdefault(key, {
            "key": key,
            "title": title,
            "kb": m.get("kb", ""),
            "domain": m.get("domain", ""),
            "chunks": 0,
            "ids": [],
            "pages": set(),
            "all_match_values": set(),
        })
        g["chunks"] += 1
        if i < len(ids):
            g["ids"].append(ids[i])
        if m.get("page_no") is not None:
            g["pages"].add(m["page_no"])

        # 收集所有可能用于删除的字段值
        for v in (sp, dp, sc):
            if v:
                g["all_match_values"].add(v)

    out = []
    for g in groups.values():
        pages = sorted(g["pages"])
        out.append({
            "key": g["key"],
            "title": g["title"],
            "kb": g["kb"],
            "domain": g["domain"],
            "chunks": g["chunks"],
            "page_min": pages[0] if pages else None,
            "page_max": pages[-1] if pages else None,
            "match_values": sorted(g["all_match_values"]),
            "chunk_ids": g["ids"],
        })
    out.sort(key=lambda x: (-x["chunks"], x["title"]))
    return {"ok": True, "sources": out, "total": len(out),
            "total_chunks": len(ids)}


def _delete_ids(ids: List[str]) -> int:
    coll = _collection()
    if not ids:
        return 0
    try:
        coll.delete(ids=ids)
        return len(ids)
    except Exception:
        # 回退：按 where source 删
        return 0



@router.post("/vectors/delete")
async def delete_one(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """单删：{chunk_ids: [...]} 或 {match_values: [...]}"""
    chunk_ids: List[str] = payload.get("chunk_ids") or []
    match_values: List[str] = payload.get("match_values") or []
    coll = _collection()
    deleted = 0
    try:
        # 优先按 chunk_ids 精确删
        if chunk_ids:
            coll.delete(ids=chunk_ids)
            deleted = len(chunk_ids)
        elif match_values:
            # 逐个字段尝试
            for val in match_values:
                for field in ("source_path", "doc_path", "source", "doc_title"):
                    got = coll.get(where={field: val}, include=[])
                    ids_got = got.get("ids") or []
                    if ids_got:
                        coll.delete(ids=ids_got)
                        deleted += len(ids_got)
                        break
                if deleted > 0:
                    break
    except Exception as e:
        raise HTTPException(500, f"删除失败: {e}")
    return {"ok": True, "deleted": deleted}



@router.post("/vectors/delete-batch")
async def delete_batch(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """批删：{sources: ["...", "..."]}"""
    sources: List[str] = payload.get("sources") or []
    if not sources:
        raise HTTPException(400, "sources required")
    coll = _collection()
    total = 0
    results = []
    for s in sources:
        try:
            n = 0
            for field in ("source_path", "doc_path", "source"):
                got = coll.get(where={field: s}, include=[])
                ids = got.get("ids") or []
                if ids:
                    coll.delete(ids=ids)
                    n = len(ids)
                    break
            results.append({"source": s, "deleted": n})
            total += n
        except Exception as e:
            results.append({"source": s, "deleted": 0, "error": str(e)})
    return {"ok": True, "total_deleted": total, "results": results}


