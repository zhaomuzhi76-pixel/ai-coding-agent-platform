"""GPU 统一协商器（V2）。所有请求走跨进程文件锁。
确保：谁做任务谁独占 GPU，其他组件被驱逐。
"""
from __future__ import annotations
import logging
from typing import Set

from backend.rag.ingest.ocr.gpu_lock import (
    acquire as _lock_acquire, release as _lock_release,
    holder as _lock_holder, status as _lock_status)

logger = logging.getLogger(__name__)
_HOLDERS: Set[str] = set()


def acquire(component: str, need_mb: int = 1500,
            wait_s: float = 30.0) -> bool:
    ok = _lock_acquire(component, need_mb=need_mb, wait_s=wait_s)
    if ok:
        _HOLDERS.add(component)
    return ok


def release(component: str) -> None:
    _HOLDERS.discard(component)
    _lock_release(component)


def holders() -> Set[str]:
    return set(_HOLDERS)


def free_mb() -> int:
    return _lock_status().get("free_mb", -1)


__all__ = ["acquire", "release", "holders", "free_mb"]
