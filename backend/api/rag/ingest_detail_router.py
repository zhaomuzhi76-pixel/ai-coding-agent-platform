"""RAG Ingest 详细状态 + 分块审核 + 召回测试"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

router = APIRouter(prefix="/api/rag/ingest", tags=["rag-ingest-detail"])

DRAFT_DIR = Path(os.path.expanduser("~/.cache/agent_knowledge/drafts"))


def _find_draft(job_id: str) -> Path | None:
    if not DRAFT_DIR.exists():
        return None
    for f in DRAFT_DIR.glob(f"{job_id}*.jsonl"):
        return f
    for f in DRAFT_DIR.glob(f"{job_id}*.json"):
        return f
    return None


@router.get("/jobs/{job_id}/detail")
async def job_detail(job_id: str) -> Dict[str, Any]:
    draft = _find_draft(job_id)
    detail = {"job_id": job_id, "draft_exists": draft is not None,
              "draft_path": str(draft) if draft else ""}
    if draft:
        try:
            lines = draft.read_text(encoding="utf-8").splitlines()
            detail["draft_count"] = len(lines)
            detail["preview"] = [json.loads(l) for l in lines[:3] if l.strip()]
        except Exception as e:
            detail["error"] = str(e)
    return {"ok": True, "data": detail}


@router.get("/jobs/{job_id}/draft-chunks")
async def job_chunks(job_id: str, limit: int = 500) -> Dict[str, Any]:
    draft = _find_draft(job_id)
    if not draft:
        raise HTTPException(404, f"draft 不存在: {job_id}")
    chunks = []
    try:
        for i, line in enumerate(draft.read_text(encoding="utf-8").splitlines()):
            if i >= limit:
                break
            if not line.strip():
                continue
            d = json.loads(line)
            chunks.append({
                "index": i,
                "text": (d.get("text") or d.get("content") or "")[:500],
                "page_start": d.get("page_start", d.get("page", 0)),
                "page_end": d.get("page_end", d.get("page", 0)),
                "source": d.get("source") or d.get("file_path", ""),
                "metadata": d.get("metadata", {}),
            })
    except Exception as e:
        raise HTTPException(500, f"读取 draft 失败: {e}")
    return {"ok": True, "job_id": job_id, "chunks": chunks, "count": len(chunks)}


@router.post("/jobs/{job_id}/draft-approve")
async def approve_chunks(job_id: str,
                         payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    accepted = payload.get("accepted_indices")
    draft = _find_draft(job_id)
    if not draft:
        raise HTTPException(404, f"draft 不存在: {job_id}")
    try:
        lines = draft.read_text(encoding="utf-8").splitlines()
        approved = []
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            if accepted is None or i in accepted:
                approved.append(json.loads(line))
    except Exception as e:
        raise HTTPException(500, f"读取失败: {e}")
    # 提取文本（保留文档标题和页码作为上下文）
    texts: list = []
    for i, c in enumerate(approved):
        t = (c.get("text") or c.get("content") or "").strip()
        if not t:
            continue
        title = c.get("doc_title") or c.get("metadata", {}).get("doc_title") or ""
        page = c.get("page_no") or c.get("line_no") or 0
        prefix = f"[{title} p.{page}]\n" if title or page else ""
        texts.append(prefix + t)

    if not texts:
        raise HTTPException(400, "无有效分块")

    # 从草稿读真实文件名（doc_title / filename）
    doc_title = ""
    for c in approved[:3]:
        for k in ("doc_title", "filename", "source", "source_path"):
            v = c.get(k) or c.get("metadata", {}).get(k) or ""
            if v and "reviewed_" not in str(v):
                doc_title = str(v).split("/")[-1]
                break
        if doc_title:
            break
    if not doc_title:
        doc_title = f"reviewed_{job_id}"

    try:
        from backend.api.rag.binding import RagBinding
        b = RagBinding()
        r = await b.index_texts({
            "texts": texts,
            "source": doc_title,
        })
    except Exception as e:
        raise HTTPException(500, f"入库失败: {type(e).__name__}: {e}")
    return {"ok": True, "job_id": job_id, "approved": len(approved), "result": r}


@router.post("/jobs/{job_id}/draft-reject")
async def reject_chunks(job_id: str) -> Dict[str, Any]:
    draft = _find_draft(job_id)
    if draft and draft.exists():
        draft.unlink()
    return {"ok": True, "job_id": job_id, "rejected": True}


@router.post("/recall-test")
async def recall_test(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    query = (payload.get("query") or "").strip()
    if not query:
        raise HTTPException(400, "query required")
    top_k = int(payload.get("top_k", 5))
    use_rerank = bool(payload.get("rerank", True))

    # 优先走 recall_test_router 的实现
    try:
        from backend.rag.ingest.review.api.recall_test_router import _get_service
        svc = _get_service()
        if svc is not None:
            r = svc.test(query=query, top_k=top_k, rerank=use_rerank)
            if hasattr(r, "__await__"):
                r = await r
            return {"ok": True, "query": query, "top_k": top_k,
                    "rerank": use_rerank, "hits": r.get("hits", r) if isinstance(r, dict) else r,
                    "source": "recall_test_router"}
    except Exception:
        pass

    # 兜底：走 RAG 查询服务
    try:
        from backend.api.rag.binding import RagBinding
        b = RagBinding()
        for meth in ("recall", "query", "search"):
            fn = getattr(b, meth, None)
            if callable(fn):
                r = fn({"query": query, "top_k": top_k, "rerank": use_rerank})
                if hasattr(r, "__await__"):
                    r = await r
                hits = r.get("hits", r) if isinstance(r, dict) else r
                return {"ok": True, "query": query, "top_k": top_k,
                        "rerank": use_rerank, "hits": hits,
                        "source": f"binding.{meth}"}
    except Exception as e:
        raise HTTPException(500, f"召回失败: {type(e).__name__}: {e}")

    raise HTTPException(500, "无可用召回接口")

@router.post("/jobs/{job_id}/draft-delete")
async def draft_delete(job_id: str) -> Dict[str, Any]:
    """取消/删除待审核草稿（不动向量库）"""
    draft = _find_draft(job_id)
    if draft and draft.exists():
        draft.unlink()
    # 标记 job 为 cancelled
    try:
        from backend.rag.ingest.jobs.registry import get_registry as _jr
        _jr().update_status(job_id, "cancelled")
    except Exception:
        pass
    return {"ok": True, "job_id": job_id, "deleted": True}


@router.post("/jobs/{job_id}/vector-delete")
async def vector_delete(job_id: str,
                       payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """按 job 删除已入库向量（用于不满意时回滚）"""
    deleted = 0
    errors: list = []
    # 通过 source_file 过滤删除
    draft = _find_draft(job_id)
    source_path = ""
    if draft and draft.exists():
        try:
            first = json.loads(draft.read_text(encoding="utf-8").splitlines()[0])
            source_path = first.get("source_path") or first.get("source") or ""
        except Exception:
            pass

    try:
        from backend.rag.indexer import get_indexer
        idx = get_indexer()
        coll = getattr(idx, "store", None) or getattr(idx, "collection", None)
        # Chroma 支持 where 过滤删除
        if hasattr(coll, "delete"):
            try:
                if source_path:
                    coll.delete(where={"source_path": source_path})
                else:
                    coll.delete(where={"job_id": job_id})
                deleted = 1
            except Exception as e:
                errors.append(f"delete where: {e}")
    except Exception as e:
        errors.append(f"get_indexer: {e}")

    # 删草稿
    if draft and draft.exists():
        draft.unlink()

    # 删标记文件
    marker = draft.with_suffix(".approved.marker") if draft else None
    if marker and marker.exists():
        marker.unlink()

    return {"ok": True, "job_id": job_id,
            "deleted": deleted, "source_path": source_path,
            "errors": errors}

@router.post("/jobs/{job_id}/purge")
async def purge_job(job_id: str) -> Dict[str, Any]:
    """一键清理：删草稿 + 删向量 + 删 job 记录（不可逆）"""
    result: Dict[str, Any] = {"ok": True, "job_id": job_id,
                              "draft_deleted": False,
                              "vectors_deleted": 0,
                              "job_deleted": False}

    # 1) 查 job，收集所有可用于匹配向量的值
    match_values = set()
    try:
        from backend.rag.ingest.jobs.registry import get_registry as _jr
        reg = _jr()
        j = reg.get(job_id) if hasattr(reg, "get") else None
        if j:
            for attr in ("filename", "draft_path", "origin_hash"):
                v = getattr(j, attr, "")
                if v:
                    match_values.add(v)
    except Exception:
        pass

    # 2) 找草稿，读 source/doc_path 进匹配集
    draft = _find_draft(job_id)
    if draft and draft.exists():
        try:
            for line in draft.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                d = json.loads(line)
                for k in ("source_path", "doc_path", "source", "doc_title"):
                    v = d.get(k) or d.get("metadata", {}).get(k)
                    if v:
                        match_values.add(v)
                break
        except Exception:
            pass

    # 3) 删向量
    try:
        from backend.storage.vector_backend import get_vector_store
        from backend.storage.vector_config import VectorConfig
        store = get_vector_store(VectorConfig())
        coll = store.collection
        deleted = 0
        for val in match_values:
            for field in ("source_path", "doc_path", "source", "doc_title"):
                got = coll.get(where={field: val}, include=[])
                ids = got.get("ids") or []
                if ids:
                    coll.delete(ids=ids)
                    deleted += len(ids)
                    break
        result["vectors_deleted"] = deleted
        result["match_values"] = sorted(match_values)
    except Exception as e:
        result["vector_error"] = f"{type(e).__name__}: {e}"

    # 4) 删草稿 + 相关文件
    if draft and draft.exists():
        draft.unlink()
        result["draft_deleted"] = True
    for suffix in (".approved.jsonl", ".approved.marker"):
        fp = draft.with_suffix(suffix) if draft else None
        if fp and fp.exists():
            fp.unlink()

    # 5) 删 job 持久化文件（真删，最重要）
    try:
        import os as _os
        from pathlib import Path as _P
        jobs_dir = _P(_os.path.expanduser("~/.cache/agent_knowledge/jobs"))
        if jobs_dir.exists():
            for f in jobs_dir.glob(f"{job_id}*"):
                try:
                    f.unlink()
                    result["job_file_deleted"] = True
                except Exception:
                    pass
        # 兜底：任何包含该 job_id 的文件
        for f in jobs_dir.glob(f"*{job_id}*"):
            try:
                f.unlink()
                result["job_file_deleted"] = True
            except Exception:
                pass
    except Exception:
        pass

    # 6) 从内存注册表移除
    try:
        from backend.rag.ingest.jobs.registry import get_default_job_registry
        reg = get_default_job_registry()
        if reg is not None:
            for meth in ("remove", "delete", "discard", "forget", "unregister"):
                fn = getattr(reg, meth, None)
                if callable(fn):
                    try:
                        fn(job_id)
                        result["job_memory_removed"] = meth
                        break
                    except Exception:
                        continue
            # 部分实现有 _jobs dict，直接删
            jobs_dict = getattr(reg, "_jobs", None)
            if isinstance(jobs_dict, dict) and job_id in jobs_dict:
                del jobs_dict[job_id]
                result["job_memory_removed"] = "_jobs.pop"
    except Exception as e:
        result["job_memory_error"] = f"{type(e).__name__}: {e}"

    print(f"[purge] {result}", flush=True)
    return result
