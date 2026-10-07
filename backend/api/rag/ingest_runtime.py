"""RAG Ingest runtime 单例。职责：装配 IngestService 所需的
chunker / indexer（复用现有向量库 + embed），暴露单例 + router builder。
不实现解析、不实现 HTTP handler、不落盘非向量库文件。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

from backend.rag.ingest.parsers import get_default_dispatcher
from backend.rag.ingest.service import IngestService, make_ingest_service
from backend.rag.multimodal.chunker import make_default_chunker
from backend.rag.multimodal.indexer import MultimodalIndexer

@dataclass(frozen=True)
class IngestRuntime:
    service: IngestService
    vector_store: Any
    embed_fn: Any

def build_ingest_runtime() -> IngestRuntime:
    """复用 multimodal_runtime 的 vector_store + embed_fn，避免双份连接。"""
    from backend.api.rag.multimodal_runtime import get_multimodal_rag_runtime
    mm = get_multimodal_rag_runtime()
    vs = mm.vector_store
    embed = mm.embed_client
    chunker = make_default_chunker()
    indexer = MultimodalIndexer(vector_store=vs, chunker=chunker,
                                embed_fn=embed)
    svc = make_ingest_service(chunker=chunker, indexer=indexer,
                              dispatcher=get_default_dispatcher())
    return IngestRuntime(service=svc, vector_store=vs, embed_fn=embed)

_RT: Optional[IngestRuntime] = None

def get_ingest_runtime() -> IngestRuntime:
    global _RT
    if _RT is None:
        _RT = build_ingest_runtime()
    return _RT

def set_ingest_runtime(rt: Optional[IngestRuntime]) -> None:
    global _RT
    _RT = rt

def build_ingest_router() -> Any:
    from backend.api.rag.ingest_router import register_ingest_routes
    from backend.api.rag.upload_router import register_upload_routes
    from backend.api.rag.jobs_router import register_jobs_routes
    try:
        from fastapi import APIRouter
    except ImportError as e:
        raise RuntimeError("fastapi 未安装") from e
    from backend.api.rag.origin_router import register_origin_routes
    from backend.api.rag.pipeline_idle_router import (
        register_pipeline_idle_routes)
    from backend.api.rag.pipeline_runtime import get_scheduler
    router = APIRouter()
    _svc = lambda: get_ingest_runtime().service
    register_ingest_routes(router, _svc)
    register_upload_routes(router, get_worker)
    register_origin_routes(router)
    register_jobs_routes(router, get_worker)
    register_pipeline_idle_routes(router, get_scheduler)
    return router


def _build_worker() -> Any:
    """装配 IngestWorker（绑定 service + origin_store）。
    启动时加载磁盘上的历史 job，前端能拉到（刷新/重启后不丢）。"""
    from backend.rag.ingest.jobs import (
        IngestWorker, get_default_job_registry)
    from backend.storage.origin_store import get_default_origin_store
    svc = get_ingest_runtime().service
    origin = get_default_origin_store()
    registry = get_default_job_registry()
    try:
        n = registry.load_from_disk()
        if n:
            import sys as _sys
            print(f"[ingest_runtime] 恢复历史 job: {n} 条",
                  file=_sys.stderr)
    except Exception as e:
        import sys as _sys
        print(f"[ingest_runtime] 历史恢复失败: {e}", file=_sys.stderr)
    worker = IngestWorker(service=svc, origin_store=origin, registry=registry)

    # [SEM_RESET] 启动时重置信号量（防泄漏）
    try:
        from backend.rag.ingest.jobs import worker as _wmod
        _wmod._OCR_SEM._value = _wmod._OCR_MAX_CONCURRENT
        import sys as _sys
        print(f"[SEM_RESET] 信号量重置为 {_wmod._OCR_MAX_CONCURRENT}",
              file=_sys.stderr)
    except Exception as _e:
        pass


    # [L2_GPU_HEAL] 启动时清理僵尸 GPU 进程 + 显存
    try:
        from backend.rag.ingest.ocr.gpu_self_heal import heal_on_startup
        _heal = heal_on_startup()
        _n_killed = len(_heal.get("killed", []))
        _n_ollama = len(_heal.get("ollama_unloaded", []))
        if _n_killed or _n_ollama:
            import sys as _sys
            print(f"[gpu-heal] 清理僵尸进程={_n_killed} "
                  f"卸载模型={_n_ollama}", file=_sys.stderr)
    except Exception as _e:
        import sys as _sys
        print(f"[gpu-heal] 失败: {_e}", file=_sys.stderr)

    # [L5_ZOMBIE] 启动时清理僵尸 job/数据（必须在 resume 前，避免续跑僵尸）
    try:
        from backend.rag.ingest.jobs.zombie_cleaner import full_scan
        # [NO_RECURSION] 显式传 worker，避免 full_scan 里调 get_worker 递归
        _z = full_scan(dry_run=False, worker=worker)
        _n_proc = _z.get("processes", {}).get("killed", 0)
        _n_job = _z.get("jobs", {}).get("marked", 0)
        _n_draft = _z.get("drafts", {}).get("deleted", 0)
        _n_ck = _z.get("checkpoints", {}).get("deleted", 0)
        _n_vec = _z.get("vectors", {}).get("deleted", 0)
        _n_tomb = _z.get("tombstones", {}).get("deleted", 0)
        if any([_n_proc, _n_job, _n_draft, _n_ck, _n_vec, _n_tomb]):
            import sys as _sys
            print(f"[zombie-clean] 启动清理: 进程={_n_proc} job={_n_job} "
                  f"draft={_n_draft} ckpt={_n_ck} vec={_n_vec} "
                  f"tomb={_n_tomb}", file=_sys.stderr)
    except Exception as _e:
        import sys as _sys
        print(f"[zombie-clean] 失败: {_e}", file=_sys.stderr)
    # [RESUME] 后台扫描未完成 job，自动续跑
    try:
        from backend.rag.ingest.jobs.resume_support import resume_all
        import threading as _th
        def _bg():
            import time as _t
            _t.sleep(3)
            try: resume_all(worker)
            except Exception: pass
        _th.Thread(target=_bg, daemon=True, name="rag-resume").start()
    except Exception:
        pass
    return worker

_WORKER: Any = None

def get_worker() -> Any:
    global _WORKER
    if _WORKER is None:
        _WORKER = _build_worker()
    return _WORKER

def set_worker(w: Any) -> None:
    global _WORKER
    _WORKER = w

__all__ = ["IngestRuntime", "build_ingest_runtime", "get_ingest_runtime",
           "set_ingest_runtime", "build_ingest_router",
           "get_worker", "set_worker"]
