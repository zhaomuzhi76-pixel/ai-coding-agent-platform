"""Reranker GPU 守卫：加载模型前抢锁，驱逐 Ollama。
独立插件。
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


def acquire_before_reranker_load(need_mb: int = 4000) -> bool:
    try:
        from backend.rag.ingest.ocr.gpu_lock import acquire
        return acquire("reranker", need_mb=need_mb, wait_s=15)
    except Exception as e:
        logger.warning("[reranker-guard] %r", e)
        return True


__all__ = ["acquire_before_reranker_load"]
