"""提交前钩子。职责：清残留 GPU 锁 + 尝试 pipeline 入队。
worker.py 只调一个函数。不实现锁/流水线（各自负责）。
"""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


def before_submit(worker: Any, job: Any, *,
                  file_path: str, filename: str,
                  kb: str, lang: str) -> bool:
    """提交前的统一入口。返回 True 表示已通过 pipeline 入队
    （调用方应 return job，不再走原 self._pool.submit）。
    返回 False 表示走原路径。

    副作用：
      - 清残留 GPU 锁（异常静默，不影响主流程）
      - 若 RAG_PIPELINE_ENABLED=1 则尝试 pipeline 入队
    """
    # 1. 清残留 GPU 锁（兜底）
    try:
        from backend.rag.ingest.ocr.gpu_lock_watchdog import (
            clean_stale as _cs)
        _cs()
    except Exception:
        pass

    # 2. 尝试 pipeline 入队
    try:
        from backend.rag.ingest.jobs.pipeline_gate import try_submit
        return try_submit(worker, job, file_path=file_path,
                          filename=filename, kb=kb, lang=lang)
    except Exception as e:
        logger.warning("[submit-hooks] pipeline 入口异常: %r", e)
        return False


__all__ = ["before_submit"]
