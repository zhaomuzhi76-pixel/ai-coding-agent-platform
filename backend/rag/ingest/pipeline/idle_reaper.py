"""空闲资源回收器（4 种任务全覆盖）。
判定链（严格优先）：
  ① 任务层：queue/registry 有活跃 → 不释放
  ② 硬件层：GPU/CPU/Ollama 任一异常 → 不释放
  ③ 连续采样 N 次通过 → 启动 grace
  ④ 满 grace 秒 → 释放（调现有接口）
信号判定见 idle_signals。
环境变量：
  RAG_IDLE_GRACE_S=60           连续空闲多久后释放
  RAG_IDLE_RECHECK_S=30         检查周期
  RAG_IDLE_CONSECUTIVE=3        连续采样 N 次
  RAG_IDLE_RELEASE_PADDLE=1     释放 Paddle
  RAG_IDLE_RELEASE_OLLAMA=1     卸载 Ollama
  RAG_IDLE_LOG_DELTA=1          记录 before/after
"""
from __future__ import annotations
import logging
import os
import threading
import time
from typing import Any, Callable, Optional

from backend.rag.ingest.pipeline.idle_signals import (
    is_task_idle, check_hardware_idle)

logger = logging.getLogger(__name__)

_GRACE_S = float(os.environ.get("RAG_IDLE_GRACE_S", "60"))
_RECHECK_S = float(os.environ.get("RAG_IDLE_RECHECK_S", "30"))
_CONSECUTIVE = int(os.environ.get("RAG_IDLE_CONSECUTIVE", "3"))
_RELEASE_PADDLE = os.environ.get("RAG_IDLE_RELEASE_PADDLE", "1") == "1"
_RELEASE_OLLAMA = os.environ.get("RAG_IDLE_RELEASE_OLLAMA", "1") == "1"
_LOG_DELTA = os.environ.get("RAG_IDLE_LOG_DELTA", "1") == "1"
_MIN_RELEASE_INTERVAL_S = float(
    os.environ.get("RAG_IDLE_MIN_RELEASE_INTERVAL_S", "60"))


def _do_release() -> dict:
    """调现有接口释放。返回 freed + before/after（真实探测）。"""
    info: dict = {"freed": [], "before": None, "after": None,
                  "ts": time.time()}
    try:
        from backend.rag.ingest.pipeline.resource_probe import probe
        info["before"] = probe(force=True).to_dict()
    except Exception:
        pass
    if _RELEASE_PADDLE:
        try:
            from backend.rag.ingest.parsers.pdf_ocr_parser_batch import (
                _release_gpu_memory)
            _release_gpu_memory()
            info["freed"].append("paddle_cuda")
        except Exception as e:
            logger.warning("[idle-reaper] 释放 Paddle 失败: %r", e)
    if _RELEASE_OLLAMA:
        try:
            from backend.providers.runtime.ollama_embed import unload_model
            if unload_model():
                info["freed"].append("ollama_model")
        except Exception as e:
            logger.warning("[idle-reaper] 卸载 Ollama 失败: %r", e)
    try:
        import gc
        gc.collect()
        info["freed"].append("gc")
    except Exception:
        pass
    try:
        from backend.rag.ingest.pipeline.resource_probe import probe
        info["after"] = probe(force=True).to_dict()
    except Exception:
        pass
    # [HISTORY] 持久化到 SQLite
    try:
        from backend.rag.ingest.pipeline.release_history import get_history
        get_history().record(info, trigger="auto")
    except Exception as e:
        logger.warning("[idle-reaper] record 失败: %r", e)
    return info


class IdleReaper:
    """空闲回收器：4 种任务 + 硬件双判定，连续 N 次空闲才释放。"""

    def __init__(self, queue: Any, registry: Any, *,
                 grace_s: float = _GRACE_S,
                 recheck_s: float = _RECHECK_S,
                 on_release: Optional[Callable[[dict], None]] = None
                 ) -> None:
        self._queue = queue
        self._registry = registry
        self._grace = max(0.0, float(grace_s))
        self._recheck = max(1.0, float(recheck_s))
        self._on_release = on_release
        self._idle_since: Optional[float] = None
        self._hw_streak: int = 0
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._last_release_ts: float = 0.0
        self._last_block_reason: str = ""

    @property
    def idle_since(self) -> Optional[float]:
        with self._lock:
            return self._idle_since

    @property
    def hw_streak(self) -> int:
        with self._lock:
            return self._hw_streak

    @property
    def last_release_ts(self) -> float:
        with self._lock:
            return self._last_release_ts

    @property
    def last_block_reason(self) -> str:
        with self._lock:
            return self._last_block_reason

    def _probe(self) -> Any:
        try:
            from backend.rag.ingest.pipeline.resource_probe import probe
            return probe()
        except Exception as e:
            logger.warning("[idle-reaper] probe 失败: %r", e)
            return None

    def tick_once(self) -> bool:
        """一次检查。返回 True 表示触发释放。"""
        now = time.time()
        # ① 任务层
        if not is_task_idle(self._queue, self._registry):
            with self._lock:
                self._idle_since = None
                self._hw_streak = 0
                self._last_block_reason = "task_active"
            return False
        # ② 硬件层
        snap = self._probe()
        hw_idle, hw_reason = check_hardware_idle(snap)
        if not hw_idle:
            with self._lock:
                self._idle_since = None
                self._hw_streak = 0
                self._last_block_reason = hw_reason
            return False
        # ③ 连续采样 + grace
        with self._lock:
            self._hw_streak += 1
            if self._hw_streak < _CONSECUTIVE:
                self._last_block_reason = (
                    f"hw_streak({self._hw_streak})<{_CONSECUTIVE}")
                return False
            if self._idle_since is None:
                self._idle_since = now
            if (now - self._idle_since) < self._grace:
                return False
        # ④ 幂等闸门：距上次释放至少 MIN_RELEASE_INTERVAL_S
        with self._lock:
            if (now - self._last_release_ts) < _MIN_RELEASE_INTERVAL_S:
                self._last_block_reason = (
                    f"min_interval({_MIN_RELEASE_INTERVAL_S}s)")
                return False
        info = _do_release()
        info["reasons"] = [f"hw_streak={_CONSECUTIVE}",
                           f"grace={self._grace}s"]
        with self._lock:
            self._last_release_ts = now
            self._idle_since = None
            self._hw_streak = 0
        if _LOG_DELTA and info.get("before") and info.get("after"):
            b, a = info["before"], info["after"]
            logger.info(
                "[idle-reaper] 释放: %s  gpu %s→%s MB (util %s→%s%%), "
                "cpu %s→%s %%, mem %s→%s %%",
                info["freed"],
                b["gpu"]["used_mb"], a["gpu"]["used_mb"],
                b["gpu"]["util"], a["gpu"]["util"],
                b["cpu"]["percent"], a["cpu"]["percent"],
                b["mem"]["percent"], a["mem"]["percent"])
        else:
            logger.info("[idle-reaper] 释放: %s", info.get("freed"))
        if self._on_release:
            try: self._on_release(info)
            except Exception: pass
        return True

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick_once()
            except Exception as e:
                logger.warning("[idle-reaper] tick 异常: %r", e)
            self._stop.wait(self._recheck)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="idle-reaper", daemon=True)
        self._thread.start()
        logger.info(
            "[idle-reaper] 启动 (grace=%ss, recheck=%ss, consecutive=%s)",
            self._grace, self._recheck, _CONSECUTIVE)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)


__all__ = ["IdleReaper", "_do_release",
           "_GRACE_S", "_RECHECK_S", "_CONSECUTIVE",
           "_MIN_RELEASE_INTERVAL_S"]
