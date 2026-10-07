"""GPU 空闲挂起器（工业级，自注册框架）。

职责：
  - 注册模型挂起/恢复回调
  - 空闲 N 分钟后自动挂起；请求打点后自动恢复
不做：
  - 不加载模型、不改模型内部、不杀进程
两种适配器：
  - TorchModelAdapter：torch 模型，.to('cpu') / .to('cuda')
  - HttpSuspendAdapter：HTTP 服务，POST /admin/{suspend,resume}

开关：RAG_GPU_GOVERNOR=1（默认关，保守）
"""
from __future__ import annotations
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

_ENV_ENABLED = "RAG_GPU_GOVERNOR"
_DEFAULT_INTERVAL = 60
_DEFAULT_IDLE = 300


def _enabled() -> bool:
    return os.environ.get(_ENV_ENABLED, "0") == "1"


# ---------- 适配器 ----------

class BaseAdapter:
    name: str = "base"

    def is_active(self) -> bool:
        return False

    def suspend(self) -> bool:
        return False

    def resume(self) -> bool:
        return False


class TorchModelAdapter(BaseAdapter):
    """PyTorch 模型挂起。holder 是可变 dict：
        {"model": model_or_none, "device": "cuda"|"cpu", "name": "..."}
    """
    def __init__(self, holder: Dict[str, Any]):
        self._h = holder
        self.name = holder.get("name", "torch_model")

    def is_active(self) -> bool:
        return self._h.get("device") == "cuda" and self._h.get("model") is not None

    def suspend(self) -> bool:
        if not self.is_active():
            return False
        try:
            m = self._h["model"]
            if m is not None and hasattr(m, "to"):
                m.to("cpu")
                self._h["device"] = "cpu"
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("[gov] suspend %s -> cpu", self.name)
            return True
        except Exception as e:
            logger.warning("[gov] suspend %s failed: %r", self.name, e)
            return False

    def resume(self) -> bool:
        if self._h.get("device") == "cuda" or self._h.get("model") is None:
            return False
        try:
            import torch
            if not torch.cuda.is_available():
                return False
            self._h["model"].to("cuda")
            self._h["device"] = "cuda"
            logger.info("[gov] resume %s -> cuda", self.name)
            return True
        except Exception as e:
            logger.warning("[gov] resume %s failed: %r", self.name, e)
            return False


class HttpSuspendAdapter(BaseAdapter):
    """外部进程：POST base_url/admin/{suspend,resume}。"""
    def __init__(self, name: str, base_url: str, timeout: float = 5.0):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._active = True

    def is_active(self) -> bool:
        return self._active

    def _post(self, path: str) -> bool:
        import urllib.request
        try:
            req = urllib.request.Request(
                self.base_url + path, method="POST",
                data=b"", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return 200 <= r.status < 300
        except Exception as e:
            logger.debug("[gov] %s %s failed: %r", self.name, path, e)
            return False

    def suspend(self) -> bool:
        ok = self._post("/admin/suspend")
        if ok:
            self._active = False
            logger.info("[gov] http suspend %s ok", self.name)
        return ok

    def resume(self) -> bool:
        ok = self._post("/admin/resume")
        if ok:
            self._active = True
            logger.info("[gov] http resume %s ok", self.name)
        return ok


# ---------- 调度器 ----------

class GpuGovernor:
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        self._lock = threading.Lock()
        self._last_touch = time.time()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._stats = {"suspend_ok": 0, "resume_ok": 0, "idle_hits": 0}

    def register(self, adapter: BaseAdapter) -> None:
        with self._lock:
            self._adapters[adapter.name] = adapter
        logger.info("[gov] register %s", adapter.name)

    def touch(self) -> None:
        """请求打点。"""
        self._last_touch = time.time()

    def _idle_seconds(self) -> float:
        return time.time() - self._last_touch

    def suspend_all(self) -> int:
        n = 0
        for a in list(self._adapters.values()):
            if a.is_active() and a.suspend():
                n += 1
        self._stats["suspend_ok"] += n
        return n

    def resume_all(self) -> int:
        n = 0
        for a in list(self._adapters.values()):
            if not a.is_active() and a.resume():
                n += 1
        self._stats["resume_ok"] += n
        return n

    def _loop(self, interval: int, idle: int) -> None:
        while not self._stop.wait(interval):
            if self._idle_seconds() >= idle:
                any_active = any(a.is_active() for a in self._adapters.values())
                if any_active:
                    self._stats["idle_hits"] += 1
                    n = self.suspend_all()
                    logger.info("[gov] idle>%ds suspend %d adapter(s)", idle, n)

    def start_daemon(self, interval: int = _DEFAULT_INTERVAL,
                     idle: int = _DEFAULT_IDLE) -> bool:
        if not _enabled():
            logger.info("[gov] disabled (set %s=1)", _ENV_ENABLED)
            return False
        if self._thread and self._thread.is_alive():
            return False
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, args=(interval, idle),
            name="gpu-governor", daemon=True)
        self._thread.start()
        logger.info("[gov] daemon started interval=%ds idle=%ds", interval, idle)
        return True

    def stop_daemon(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def status(self) -> Dict[str, Any]:
        out = {"idle_seconds": round(self._idle_seconds(), 1),
               "adapters": {}, "stats": dict(self._stats)}
        try:
            import torch
            if torch.cuda.is_available():
                out["gpu_allocated_mb"] = round(
                    torch.cuda.memory_allocated() / 1024 / 1024, 1)
                out["gpu_reserved_mb"] = round(
                    torch.cuda.memory_reserved() / 1024 / 1024, 1)
        except Exception:
            pass
        for name, a in self._adapters.items():
            out["adapters"][name] = {"active": a.is_active(),
                                      "kind": type(a).__name__}
        return out


_singleton: Optional[GpuGovernor] = None


def get_governor() -> GpuGovernor:
    global _singleton
    if _singleton is None:
        _singleton = GpuGovernor()
    return _singleton


__all__ = ["GpuGovernor", "get_governor",
           "TorchModelAdapter", "HttpSuspendAdapter", "BaseAdapter"]
