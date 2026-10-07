"""Pipeline 入队门。职责：判断是否启用三阶段流水线；
若启用则调 scheduler 入队。worker.py 只调这里的一行函数。
不实现流水线（pipeline 管）、不实现 worker。
"""
from __future__ import annotations
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def try_submit(worker: Any, job: Any, *,
               file_path: str, filename: str,
               kb: str, lang: str) -> bool:
    """尝试走 pipeline 入队。True=已入队（调用方应 return）；
    False=走老路径。任何异常均返回 False。"""
    if os.environ.get("RAG_PIPELINE_ENABLED", "0") != "1":
        return False
    try:
        from backend.api.rag.pipeline_runtime import get_scheduler
        sched = get_scheduler()
        if sched is None:
            return False
        sched.submit_job(
            job.job_id, file_path=file_path, filename=filename,
            kb=kb, lang=lang, priority=0)
        return True
    except Exception as e:
        logger.warning("[worker] pipeline 入队失败，回退: %r", e)
        return False


__all__ = ["try_submit"]
