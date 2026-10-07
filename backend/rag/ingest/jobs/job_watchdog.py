"""[L4 job 级看门狗] 监控每个 job 的进度时间戳，超时则中断 + 释放。
集成进 L3 gpu_watchdog，也可独立运行。
超时阈值可通过环境变量覆盖。
"""
from __future__ import annotations
import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 环境变量可覆盖
OCR_PAGE_TIMEOUT = int(os.environ.get("RAG_WD_OCR_PAGE_TIMEOUT", "180"))
OCR_BATCH_TIMEOUT = int(os.environ.get("RAG_WD_OCR_BATCH_TIMEOUT", "600"))
EMBED_BATCH_TIMEOUT = int(os.environ.get("RAG_WD_EMBED_BATCH_TIMEOUT", "180"))
APPROVE_TOTAL_TIMEOUT = int(os.environ.get("RAG_WD_APPROVE_TIMEOUT", "1800"))


class JobTracker:
    """记录每个 job 的最后进度时间戳。"""
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def on_progress(self, job_id: str, phase: str, current: int,
                    total: int = 0) -> None:
        """worker 每次进度更新时调用。"""
        now = time.monotonic()
        prev = self._jobs.get(job_id)
        if prev is None:
            self._jobs[job_id] = {
                "phase": phase, "current": current, "total": total,
                "first_seen": now, "last_progress": now,
                "last_value": current,
            }
            return
        # 进度真的涨了 → 刷新时间
        if current != prev.get("last_value"):
            prev["last_value"] = current
            prev["last_progress"] = now
        prev["phase"] = phase
        prev["current"] = current
        prev["total"] = total

    def check(self, job_id: str) -> Optional[str]:
        """返回 None（正常）或原因（超时原因）。"""
        info = self._jobs.get(job_id)
        if info is None:
            return None
        now = time.monotonic()
        idle = now - info["last_progress"]
        phase = info.get("phase", "")
        # OCR 页级：180 秒无进展
        if phase in ("parsing", "ocr") and idle > OCR_PAGE_TIMEOUT:
            return f"OCR 无进展 {idle:.0f}s > {OCR_PAGE_TIMEOUT}s"
        # 向量化：180 秒
        if phase == "embedding" and idle > EMBED_BATCH_TIMEOUT:
            return f"向量化无进展 {idle:.0f}s > {EMBED_BATCH_TIMEOUT}s"
        # 总耗时：30 分钟
        total_elapsed = now - info["first_seen"]
        if total_elapsed > APPROVE_TOTAL_TIMEOUT:
            return f"总耗时 {total_elapsed:.0f}s > {APPROVE_TOTAL_TIMEOUT}s"
        return None

    def cleanup(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    def list_stuck(self) -> Dict[str, str]:
        """返回 {job_id: 原因}。"""
        out = {}
        for jid in list(self._jobs.keys()):
            reason = self.check(jid)
            if reason:
                out[jid] = reason
        return out


# 单例
_tracker: Optional[JobTracker] = None


def get_tracker() -> JobTracker:
    global _tracker
    if _tracker is None:
        _tracker = JobTracker()
    return _tracker


__all__ = ["JobTracker", "get_tracker",
           "OCR_PAGE_TIMEOUT", "OCR_BATCH_TIMEOUT",
           "EMBED_BATCH_TIMEOUT", "APPROVE_TOTAL_TIMEOUT"]
