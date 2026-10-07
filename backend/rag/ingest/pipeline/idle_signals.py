"""空闲信号判定。职责：任务层 + 硬件层双判定。
不做释放（idle_reaper 管）、不探测（resource_probe 管）。
4 种任务：
  1/2/4. Agent 编程 / AI 对话 / Reranker → 无活跃接口 → 用 GPU/CPU
  3.     向量化 → queue + registry 精确判定
环境变量：
  RAG_IDLE_GPU_UTIL_THRESHOLD=15
  RAG_IDLE_CPU_PERCENT_THRESHOLD=20
  RAG_IDLE_CHECK_OLLAMA=1
"""
from __future__ import annotations
import json
import os
import urllib.request
from typing import Any, Tuple

_GPU_UTIL_TH = int(os.environ.get("RAG_IDLE_GPU_UTIL_THRESHOLD", "15"))
_CPU_PCT_TH = float(os.environ.get("RAG_IDLE_CPU_PERCENT_THRESHOLD", "20"))
_CHECK_OLLAMA = os.environ.get("RAG_IDLE_CHECK_OLLAMA", "1") == "1"
_OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


def is_task_idle(queue: Any, registry: Any) -> bool:
    """任务层判定（向量化精确）。异常 → 保守 False。"""
    try:
        st = queue.stats() or {}
        for k, v in st.items():
            if (k.endswith(".pending") or k.endswith(".running")) and v > 0:
                return False
    except Exception:
        return False
    try:
        for j in registry.list_recent(limit=100):
            s = str(getattr(j.status, "value", j.status)).lower()
            if s in ("pending", "running", "pending_review"):
                return False
    except Exception:
        return False
    return True


def _check_ollama_loaded() -> bool:  # [INFO] 仅用于诊断，不再阻止释放
    """Ollama 是否有模型常驻显存。异常 → 保守 False（不阻止判定）。"""
    if not _CHECK_OLLAMA:
        return False
    try:
        with urllib.request.urlopen(
                f"{_OLLAMA_BASE}/api/ps", timeout=2) as r:
            d = json.load(r)
        return len(d.get("models", []) or []) > 0
    except Exception:
        return False


def check_hardware_idle(snapshot: Any) -> Tuple[bool, str]:
    """硬件层判定（覆盖 Agent/对话/Rerank）。
    - snapshot=None → (False, "probe_failed") 保守
    - GPU util > 阈值 → 忙
    - CPU% > 阈值 → 忙
    - Ollama 有模型 → 忙
    """
    if snapshot is None:
        return False, "probe_failed"
    if bool(getattr(snapshot, "gpu_ok", False)):
        util = int(getattr(snapshot, "gpu_util", 0) or 0)
        if util > _GPU_UTIL_TH:
            return False, f"gpu_util({util})>{_GPU_UTIL_TH}"
    cpu = float(getattr(snapshot, "cpu_percent", 0.0) or 0.0)
    if cpu > _CPU_PCT_TH:
        return False, f"cpu({cpu:.1f})>{_CPU_PCT_TH}"
    # [FIX] 不再把"Ollama 有模型"当"硬件忙"——
    # 第①层 is_task_idle() 已确保无活跃任务，此时 Ollama 模型
    # 是"残留"而非"在用"，应由 idle_reaper 主动卸载。
    # 有活跃 embed 任务时，第①层会拦截。
    return True, ""


__all__ = ["is_task_idle", "check_hardware_idle",
           "_GPU_UTIL_TH", "_CPU_PCT_TH", "_CHECK_OLLAMA"]
