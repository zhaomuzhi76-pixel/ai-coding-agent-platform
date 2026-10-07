"""Pipeline runtime 装配。职责：从 ingest_runtime 拿 service/draft/embed/vector，
装配 PipelineScheduler 单例。只在 RAG_PIPELINE_ENABLED=1 时激活。
不实现流水线（pipeline 管）、不改 worker。
"""
from __future__ import annotations
import logging
import os
from typing import Any, Optional

from backend.rag.ingest.pipeline.scheduler import PipelineScheduler

logger = logging.getLogger(__name__)

_SCHED: Optional[PipelineScheduler] = None


def _make_options(*, job_id: str, file_path: str, filename: str,
                  kb: str, lang: str) -> Any:
    from backend.rag.ingest.service import IngestOptions
    return IngestOptions(
        kb=(kb or "general").strip() or "general",
        source=filename, batch_size=64, dry_run=False,
        extra_meta={"job_id": job_id})


def _on_done(job_id: str) -> None:
    try:
        from backend.rag.ingest.jobs.registry import (
            get_default_job_registry, JobStatus)
        r = get_default_job_registry()
        cur = r.get(job_id)
        if cur is None:
            return
        st = str(getattr(cur.status, "value", "")).lower()
        if st in ("done", "cancelled", "rejected"):
            return
        r.finish(job_id, status=JobStatus.DONE)
        print(f"[pipeline-runtime] job={job_id} → DONE", flush=True)
    except Exception as e:
        logger.warning("[pipeline-runtime] on_done %s: %r", job_id, e)


def _build() -> Optional[PipelineScheduler]:
    try:
        from backend.api.rag.ingest_runtime import get_ingest_runtime
        from backend.rag.ingest.jobs.draft_store import (
            get_default_draft_store)
        rt = get_ingest_runtime()
        from backend.rag.ingest.jobs.registry import get_default_job_registry
        sched = PipelineScheduler(
            service=rt.service,
            draft_store=get_default_draft_store(),
            embed_fn=rt.embed_fn,
            vector_store=rt.vector_store,
            on_job_done=_on_done,
            make_options=_make_options,
            registry=get_default_job_registry(),
        )
        # [LOCK_CLEAN] 启动时清残留 GPU 锁
        try:
            from backend.rag.ingest.ocr.gpu_lock_watchdog import (
                clean_stale as _clean)
            if _clean():
                print("[pipeline-runtime] 清理了残留 GPU 锁", flush=True)
        except Exception:
            pass
        # [LOCK_BG] 后台每分钟清一次
        import threading as _th
        def _bg_clean():
            import time as _t
            from backend.rag.ingest.ocr.gpu_lock_watchdog import (
                clean_stale as _cs)
            while True:
                _t.sleep(60)
                try: _cs()
                except Exception: pass
        _th.Thread(target=_bg_clean, daemon=True,
                   name="gpu-lock-wd").start()

        n = sched.recover()
        sched.start()
        logger.info("[pipeline-runtime] 已启动 (recover=%d)", n)
        print(f"[pipeline-runtime] 已启动 (recover={n})", flush=True)
        return sched
    except Exception as e:
        logger.error("[pipeline-runtime] 装配失败: %r", e)
        return None


def _resolve_pipeline_enabled() -> bool:
    """优先级：env RAG_PIPELINE_ENABLED > rag_config.json > 默认 true。
    这样无论后端怎么启动（哪怕没传 env），都能从配置读到开关。
    """
    raw = os.environ.get("RAG_PIPELINE_ENABLED")
    if raw is not None and str(raw).strip() != "":
        return str(raw).strip() == "1"
    try:
        import json
        p = os.path.expanduser("~/.biancheng/rag_config.json")
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            v = d.get("pipeline_enabled")
            if v is None:
                return True   # 配置里没写 → 默认开
            return bool(v)
    except Exception:
        pass
    return True   # 最终兜底：开


def get_scheduler() -> Optional[PipelineScheduler]:
    global _SCHED
    if _SCHED is None and _resolve_pipeline_enabled():
        _SCHED = _build()
    return _SCHED


def set_scheduler(s: Optional[PipelineScheduler]) -> None:
    global _SCHED
    _SCHED = s


__all__ = ["get_scheduler", "set_scheduler"]
