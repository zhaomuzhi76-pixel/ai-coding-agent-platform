"""Pipeline 空闲状态 + 释放历史 HTTP API。
PREFIX = /api/rag/pipeline
"""
from __future__ import annotations
import traceback
from typing import Any, Dict, Callable

PREFIX = "/api/rag/pipeline"


def _safe(fn):
    try:
        return {"ok": True, "data": fn()}
    except Exception as e:
        return {"ok": False, "error": str(e),
                "trace": traceback.format_exc()[:500]}


def register_pipeline_idle_routes(router: Any,
                                   get_scheduler: Callable[[], Any]) -> None:
    try:
        from fastapi import APIRouter  # noqa: F401
    except ImportError as e:
        raise RuntimeError("fastapi 未安装") from e

    @router.get(f"{PREFIX}/idle-stats")
    def idle_stats() -> Dict[str, Any]:
        def _do():
            from backend.rag.ingest.pipeline.idle_reaper import (
                _GRACE_S, _RECHECK_S, _CONSECUTIVE,
                _MIN_RELEASE_INTERVAL_S)
            from backend.rag.ingest.pipeline.idle_signals import (
                _GPU_UTIL_TH, _CPU_PCT_TH, is_task_idle,
                check_hardware_idle)
            from backend.rag.ingest.pipeline.resource_probe import probe
            from backend.rag.ingest.pipeline.release_history import (
                get_history, _resolve_history_days)

            sched = None
            try: sched = get_scheduler()
            except Exception: pass

            reaper = getattr(sched, "_reaper", None) if sched else None
            snap = probe()
            sched_active = bool(sched and getattr(sched, "_started", False))
            # 未启用 pipeline 时，task_idle/hw_idle 返回中性 None
            task_idle: Any = None
            hw_idle: Any = None
            hw_reason = ""
            if sched_active:
                try:
                    task_idle = is_task_idle(sched.queue, sched._registry)
                    hw_idle, hw_reason = check_hardware_idle(snap)
                except Exception:
                    pass

            hist = get_history()
            return {
                "scheduler_active": sched_active,
                "task_idle": task_idle,
                "hw_idle": hw_idle,
                "hw_block_reason": hw_reason,
                "hw_streak": int(reaper.hw_streak) if reaper else 0,
                "idle_since": reaper.idle_since if reaper else None,
                "last_release_ts": (
                    float(reaper.last_release_ts) if reaper else 0.0),
                "last_block_reason": (
                    reaper.last_block_reason if reaper else ""),
                "config": {
                    "grace_s": _GRACE_S, "recheck_s": _RECHECK_S,
                    "consecutive": _CONSECUTIVE,
                    "gpu_util_th": _GPU_UTIL_TH,
                    "cpu_pct_th": _CPU_PCT_TH,
                    "min_release_interval_s": _MIN_RELEASE_INTERVAL_S,
                    "retention_days": _resolve_history_days(),
                },
                "snapshot": snap.to_dict() if snap else None,
                "db_path": hist.db_path,
                "stats_24h": hist.stats(24),
            }
        return _safe(_do)

    @router.get(f"{PREFIX}/release-history")
    def release_history(hours: int = 24, limit: int = 100) -> Dict[str, Any]:
        def _do():
            from backend.rag.ingest.pipeline.release_history import (
                get_history)
            hist = get_history()
            return {"hours": int(hours),
                    "items": hist.list_recent(hours=hours, limit=limit),
                    "stats": hist.stats(hours)}
        return _safe(_do)

    @router.post(f"{PREFIX}/purge-history")
    def purge_history(days: int = 0) -> Dict[str, Any]:
        def _do():
            from backend.rag.ingest.pipeline.release_history import (
                get_history, _resolve_history_days)
            hist = get_history()
            used = days if days > 0 else _resolve_history_days()
            n = hist.purge_old(used)
            return {"purged": n, "used_days": used}
        return _safe(_do)


__all__ = ["register_pipeline_idle_routes", "PREFIX"]
