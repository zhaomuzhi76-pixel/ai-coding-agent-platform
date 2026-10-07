"""GPU 预算守护 + 任务权重账本。
职责：
  - 静态预算：OCR/Embed 各自预留多少显存
  - 动态账本：记录正在跑的任务（level/weight），供准入判决
环境变量：
  RAG_GPU_TOTAL_MB=8192
  RAG_GPU_OCR_MB=2000       Paddle 预留
  RAG_GPU_OLLAMA_MB=3500    qwen3-embedding:4b 预留
  RAG_GPU_SAFETY_MB=500     安全垫
  RAG_LIGHT_MAX_CONCURRENT=2  light 任务并发上限
"""
from __future__ import annotations
import os
import threading
from typing import Dict, Optional

_TOTAL = int(os.environ.get("RAG_GPU_TOTAL_MB", "8192"))
_OCR_MB = int(os.environ.get("RAG_GPU_OCR_MB", "2000"))
_OLLAMA_MB = int(os.environ.get("RAG_GPU_OLLAMA_MB", "3500"))
_SAFETY_MB = int(os.environ.get("RAG_GPU_SAFETY_MB", "500"))

class GpuBudget:
    """GPU 预算 + 任务账本。线程安全。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._ocr_running: Dict[str, str] = {}   # job_id -> level
        self._embed_running: int = 0

    # ── 静态预算查询（旧接口，保持兼容）──
    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            ocr_n = len(self._ocr_running)
            used = (_OCR_MB if ocr_n > 0 else 0) + self._embed_running * _OLLAMA_MB
            return {
                "total_mb": _TOTAL,
                "used_mb": used,
                "free_mb": max(0, _TOTAL - used - _SAFETY_MB),
                "ocr_running": ocr_n,
                "embed_running": self._embed_running,
            }

    # ── 任务账本（新增）──
    def register_ocr(self, job_id: str, level: str) -> None:
        with self._lock:
            self._ocr_running[job_id] = level

    def unregister_ocr(self, job_id: str) -> None:
        with self._lock:
            self._ocr_running.pop(job_id, None)

    @staticmethod
    # ── 旧接口（保持兼容 stage_ocr 现有调用）──
    def release_ocr(self) -> None:
        with self._lock:
            self._ocr_running.pop("_legacy", None)

    def acquire_embed(self) -> None:
        with self._lock:
            self._embed_running += 1

    def release_embed(self) -> None:
        with self._lock:
            self._embed_running = max(0, self._embed_running - 1)

    def max_embed_workers(self) -> int:
        budget = (_TOTAL - _OCR_MB - _SAFETY_MB) // max(1, _OLLAMA_MB)
        return max(1, min(int(budget), 4))

_budget: Optional[GpuBudget] = None
_guard = threading.Lock()

def get_budget() -> GpuBudget:
    global _budget
    if _budget is None:
        with _guard:
            if _budget is None:
                _budget = GpuBudget()
    return _budget

__all__ = ["GpuBudget", "get_budget",
           "_TOTAL", "_OCR_MB", "_OLLAMA_MB", "_SAFETY_MB", "_MAX_SLOTS"]
