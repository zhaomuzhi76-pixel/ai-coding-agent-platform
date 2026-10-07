"""并发守卫（限流 + 排队 + 超时降级 + 指标）。

职责：单一（信号量限流）。
不做：缓存、观测聚合、路由。
"""
from __future__ import annotations
import asyncio
import time
from typing import Optional


class ConcurrencyGuard:
    """asyncio.Semaphore + 排队超时 + 降级（不抛异常）。"""

    def __init__(self, max_concurrent: int = 8, timeout_s: float = 30.0):
        if max_concurrent < 1:
            raise ValueError("max_concurrent >= 1")
        if timeout_s <= 0:
            raise ValueError("timeout_s > 0")
        self._max = max_concurrent
        self._timeout = timeout_s
        self._sem: Optional[asyncio.Semaphore] = None
        self._active = 0
        self._queued = 0
        self._rejected = 0
        self._served = 0
        self._total_wait_ms = 0.0

    def _sem_or_create(self) -> asyncio.Semaphore:
        """延迟创建，避免 import 期 require event loop。"""
        if self._sem is None:
            self._sem = asyncio.Semaphore(self._max)
        return self._sem

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """获取许可。超时返回 False（降级），不抛异常。"""
        t = self._timeout if timeout is None else timeout
        self._queued += 1
        t0 = time.time()
        try:
            await asyncio.wait_for(self._sem_or_create().acquire(), timeout=t)
            self._queued -= 1
            self._active += 1
            self._total_wait_ms += (time.time() - t0) * 1000.0
            return True
        except asyncio.TimeoutError:
            self._queued -= 1
            self._rejected += 1
            return False

    def release(self) -> None:
        if self._active > 0:
            self._active -= 1
            self._served += 1
        if self._sem is not None:
            self._sem.release()

    def snapshot(self) -> dict:
        avg = self._total_wait_ms / max(1, self._served)
        return {
            "max_concurrent": self._max,
            "timeout_s": self._timeout,
            "active": self._active,
            "queued": self._queued,
            "rejected": self._rejected,
            "served": self._served,
            "avg_wait_ms": round(avg, 2),
        }
