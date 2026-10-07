"""实时资源探测。职责：读 CPU/MEM/GPU 当前使用。
不重写探测（system_monitor_router 管），只做缓存 + 字段适配。
缓存避免高频判决时反复调 nvidia-smi。
环境变量（全部可调，无硬编码）：
  RAG_PROBE_CACHE_TTL=1.0   快照缓存秒数
"""
from __future__ import annotations
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

_CACHE_TTL = float(os.environ.get("RAG_PROBE_CACHE_TTL", "1.0"))
# [物理常量] GB ↔ MB 换算（不是可调阈值）
_MB_PER_GB = 1024

_lock = threading.RLock()
_cache: Optional["ResourceSnapshot"] = None
_cache_ts: float = 0.0

@dataclass(frozen=True)
class ResourceSnapshot:
    """一次资源快照（不可变，可安全跨线程传递）。"""
    ts: float
    cpu_percent: float
    cpu_cores: int
    cpu_load_1min: float
    mem_total_mb: int
    mem_used_mb: int
    mem_available_mb: int
    mem_percent: float
    gpu_ok: bool
    gpu_total_mb: int
    gpu_used_mb: int
    gpu_free_mb: int
    gpu_util: int
    gpu_temp_c: int
    error: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts": self.ts,
            "cpu": {"percent": self.cpu_percent, "cores": self.cpu_cores,
                    "load_1min": self.cpu_load_1min},
            "mem": {"total_mb": self.mem_total_mb,
                    "used_mb": self.mem_used_mb,
                    "available_mb": self.mem_available_mb,
                    "percent": self.mem_percent},
            "gpu": {"ok": self.gpu_ok, "total_mb": self.gpu_total_mb,
                    "used_mb": self.gpu_used_mb,
                    "free_mb": self.gpu_free_mb,
                    "util": self.gpu_util, "temp_c": self.gpu_temp_c},
            "error": self.error,
        }

def _build() -> ResourceSnapshot:
    """调用 system_monitor_router 的现成探测函数，做字段适配。"""
    from backend.api.system_monitor_router import _cpu_mem, _gpu
    cm = _cpu_mem() or {}
    g = _gpu() or {}

    cpu = cm.get("cpu") or {}
    mem = cm.get("memory") or {}

    # GB → MB 换算（system_monitor_router 用 GB）
    mem_total_mb = int(float(mem.get("total_gb", 0)) * _MB_PER_GB)
    mem_used_mb = int(float(mem.get("used_gb", 0)) * _MB_PER_GB)
    mem_avail_mb = int(float(mem.get("available_gb", 0)) * _MB_PER_GB)

    # GPU 字段适配（system_monitor_router 无 free_mb，用 total-used 计算）
    gpu_ok = bool(g.get("ok"))
    gpu_total = int(g.get("vram_total_mb", 0) or 0)
    gpu_used = int(g.get("vram_used_mb", 0) or 0)
    gpu_free = max(0, gpu_total - gpu_used)

    # 错误聚合
    err = ""
    if cm.get("error"):
        err = str(cm["error"])
    elif not gpu_ok and g.get("error"):
        err = str(g["error"])

    # CPU load_1min（system_monitor_router 返回 list）
    load_list = cpu.get("load") or [0.0]
    load_1min = float(load_list[0]) if load_list else 0.0

    return ResourceSnapshot(
        ts=time.time(),
        cpu_percent=float(cpu.get("percent", 0.0) or 0.0),
        cpu_cores=int(cpu.get("cores", 1) or 1),
        cpu_load_1min=load_1min,
        mem_total_mb=mem_total_mb,
        mem_used_mb=mem_used_mb,
        mem_available_mb=mem_avail_mb,
        mem_percent=float(mem.get("percent", 0.0) or 0.0),
        gpu_ok=gpu_ok,
        gpu_total_mb=gpu_total,
        gpu_used_mb=gpu_used,
        gpu_free_mb=gpu_free,
        gpu_util=int(g.get("util", 0) or 0),
        gpu_temp_c=int(g.get("temp_c", 0) or 0),
        error=err,
    )

def probe(force: bool = False) -> ResourceSnapshot:
    """读一次快照。force=True 绕过缓存。线程安全。"""
    global _cache, _cache_ts
    with _lock:
        now = time.time()
        if not force and _cache is not None and (now - _cache_ts) < _CACHE_TTL:
            return _cache
        _cache = _build()
        _cache_ts = _cache.ts
        return _cache

def invalidate() -> None:
    """强制下次 probe 重新采样。"""
    global _cache
    with _lock:
        _cache = None

__all__ = ["ResourceSnapshot", "probe", "invalidate"]
