"""异步采集 Job 查询 API。职责：列出/查询/取消 job。
不做业务、不持状态。端点前缀 /api/rag/ingest/jobs。
"""
from __future__ import annotations
from typing import Any, Callable

PREFIX = "/api/rag/ingest/jobs"

# [APPROVE_LOCK] 同 job 只允许一个 approve 线程
import threading as _th_lock
_APPROVE_LOCKS: dict = {}
_APPROVE_LOCKS_GUARD = _th_lock.Lock()

def _acquire_approve(job_id: str) -> bool:
    with _APPROVE_LOCKS_GUARD:
        if _APPROVE_LOCKS.get(job_id):
            return False
        _APPROVE_LOCKS[job_id] = True
        return True

def _release_approve(job_id: str) -> None:
    with _APPROVE_LOCKS_GUARD:
        _APPROVE_LOCKS.pop(job_id, None)



def register_jobs_routes(router: Any,
                         get_worker: Callable[[], Any]) -> None:
    try:
        from fastapi import APIRouter  # noqa: F401
    except ImportError as e:
        raise RuntimeError("fastapi 未安装") from e

    def _wrap(fn):
        def _inner(*a, **kw):
            try:
                return {"ok": True, "data": fn(*a, **kw)}
            except Exception as e:
                return {"ok": False, "error": {
                    "code": type(e).__name__, "message": str(e)}}
        return _inner

    @router.get(PREFIX)
    async def _list(limit: int = 20) -> dict:
        def _do():
            w = get_worker()
            from backend.rag.ingest.jobs.deleted_registry import (
                get_deleted_registry)
            dr = get_deleted_registry()
            jobs = w.registry.list_recent(limit=limit)
            visible = [j for j in jobs if not dr.is_deleted(j.job_id)]
            return {"total": len(visible),
                    "jobs": [j.to_dict() for j in visible]}
        return _wrap(_do)()

    @router.get(f"{PREFIX}/{{job_id}}")
    async def _get(job_id: str) -> dict:
        def _do():
            w = get_worker()
            j = w.registry.get(job_id)
            if j is None:
                raise KeyError(f"job not found: {job_id}")
            return j.to_dict()
        return _wrap(_do)()

    @router.get(f"{PREFIX}/{{job_id}}/chunks")
    async def _chunks(job_id: str, offset: int = 0, limit: int = 100) -> dict:
        def _do():
            w = get_worker()
            j = w.registry.get(job_id)
            if j is None:
                raise KeyError(f"job not found: {job_id}")
            if not j.origin_hash:
                return {"total": 0, "offset": offset, "limit": limit,
                        "chunks": [], "note": "job 无 origin_hash"}
            from backend.storage.vector_backend import get_vector_store
            from backend.storage.vector_config import VectorConfig
            cfg = VectorConfig()
            vs = get_vector_store(cfg)
            col = getattr(vs, "collection", None)
            if col is None:
                return {"total": 0, "offset": offset, "limit": limit,
                        "chunks": [], "note": "后端不支持（Qdrant 暂未实现）"}
            # Chroma：按 origin_hash 过滤
            try:
                all_ids = col.get(where={"origin_hash": j.origin_hash},
                                   include=[])["ids"]
                total = len(all_ids)
            except Exception:
                total = 0
            data = col.get(
                where={"origin_hash": j.origin_hash},
                limit=int(limit), offset=int(offset),
                include=["documents", "metadatas"])
            ids = data.get("ids") or []
            docs = data.get("documents") or []
            metas = data.get("metadatas") or []
            out = []
            for i, cid in enumerate(ids):
                out.append({
                    "chunk_id": str(cid),
                    "text": str(docs[i]) if i < len(docs) else "",
                    "metadata": dict(metas[i]) if i < len(metas) and metas[i] else {},
                })
            return {"total": total, "offset": offset, "limit": limit,
                    "chunks": out}
        return _wrap(_do)()

    @router.post(f"{PREFIX}/{{job_id}}/cancel")
    async def _cancel(job_id: str) -> dict:
        def _do():
            from backend.rag.ingest.jobs.approve_logic import cancel_job_safe
            return cancel_job_safe(get_worker(), job_id)
        return _wrap(_do)()

    @router.delete(f"{PREFIX}/{{job_id}}")
    async def _delete(job_id: str) -> dict:
        def _do():
            w = get_worker()
            from backend.rag.ingest.jobs.deleted_registry import (
                get_deleted_registry)
            dr = get_deleted_registry()
            try: w.cancel(job_id)
            except Exception: pass
            try: w.registry.remove(job_id)
            except Exception: pass
            dr.mark(job_id, "delete_user")
            return {"deleted": True, "job_id": job_id, "tombstone": True}
        return _wrap(_do)()

    @router.delete(PREFIX)
    async def _clear() -> dict:
        def _do():
            w = get_worker()
            from backend.rag.ingest.jobs.deleted_registry import (
                get_deleted_registry)
            dr = get_deleted_registry()
            jobs = w.registry.list_recent(limit=10000)
            for j in jobs: dr.mark(j.job_id, "clear_all")
            n = w.registry.count()
            try: w.registry.clear()
            except Exception: pass
            return {"cleared": n}
        return _wrap(_do)()


    @router.post(f"{PREFIX}/{{job_id}}/draft-approve")
    async def _draft_approve(job_id: str, body: dict | None = None) -> dict:
        # [ASYNC_APPROVE + APPROVE_LOCK] 后台线程 + 同 job 全局锁
        import threading as _th, logging as _lg
        if not _acquire_approve(job_id):
            return {"ok": True, "data": {
                "job_id": job_id, "status": "already_running",
                "note": "该 job 已在向量化中，忽略重复请求"}}
        def _bg():
            try:
                try:
                    from backend.rag.ingest.jobs.resume_support import (
                        approve_job_resumable as _fn)
                except ImportError:
                    from backend.rag.ingest.jobs.approve_logic import (
                        approve_job_safe as _fn)
                _fn(get_worker(), job_id, body)
            except Exception:
                _lg.getLogger(__name__).exception(
                    "[approve-bg] job=%s 崩溃", job_id)
            finally:
                _release_approve(job_id)
        _th.Thread(target=_bg, daemon=True,
                   name=f"approve-{job_id}").start()
        return {"ok": True, "data": {
            "job_id": job_id, "status": "running",
            "note": "后台向量化中，请轮询状态"}}


__all__ = ["register_jobs_routes", "PREFIX"]
