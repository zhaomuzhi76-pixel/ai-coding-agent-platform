"""GPU Governor 适配器（单一职责：只定义 suspend/resume 协议实现）。

三种来源：
  - _SingletonAdapter ：模块级 _singleton._model / ._device（懒加载单例）
  - _RerankerAdapter  ：llama.cpp HTTP /unload（reranker_server）
  - _PaddlePoolAdapter：OCR 引擎池 OcrEnginePool（逐引擎 release）
不做：不注册、不起 daemon、不打点（wiring / governor 管）。
"""
from __future__ import annotations
import logging
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_RERANKER = "http://127.0.0.1:9033"


class _SingletonAdapter:
    """适配 module._singleton._model / ._device 形态。"""

    def __init__(self, module_name: str, singleton_attr: str,
                 model_attr: str, device_attr: str, name: str):
        self._mod = module_name
        self._sa = singleton_attr
        self._ma = model_attr
        self._da = device_attr
        self.name = name

    def _obj(self):
        try:
            import importlib
            return getattr(importlib.import_module(self._mod),
                           self._sa, None)
        except Exception:
            return None

    def _model(self):
        o = self._obj()
        return getattr(o, self._ma, None) if o is not None else None

    def _device(self) -> Optional[str]:
        o = self._obj()
        if o is None:
            return None
        d = getattr(o, self._da, None)
        return str(d) if d else None

    def is_active(self) -> bool:
        m = self._model()
        if m is None:
            return False
        d = self._device() or ""
        return d.startswith("cuda")

    def suspend(self) -> bool:
        m = self._model()
        if m is None or not hasattr(m, "to"):
            return False
        try:
            m.to("cpu")
            o = self._obj()
            if o is not None:
                setattr(o, self._da, "cpu")
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("[gov] suspend %s -> cpu", self.name)
            return True
        except Exception as e:
            logger.warning("[gov] suspend %s: %r", self.name, e)
            return False

    def resume(self) -> bool:
        m = self._model()
        if m is None or not hasattr(m, "to"):
            return False
        if (self._device() or "").startswith("cuda"):
            return False
        try:
            import torch
            if not torch.cuda.is_available():
                return False
            m.to("cuda")
            o = self._obj()
            if o is not None:
                setattr(o, self._da, "cuda")
            logger.info("[gov] resume %s -> cuda", self.name)
            return True
        except Exception as e:
            logger.warning("[gov] resume %s: %r", self.name, e)
            return False


class _RerankerAdapter:
    """reranker_server 现成 /unload（下次 /rerank 自动 reload）。"""

    def __init__(self, base_url: str = _DEFAULT_RERANKER,
                 name: str = "reranker"):
        self.base_url = base_url.rstrip("/")
        self.name = name
        self._state = "loaded"

    def is_active(self) -> bool:
        return self._state == "loaded"

    def _post(self, path: str, timeout: float = 5.0) -> bool:
        try:
            req = urllib.request.Request(
                self.base_url + path, method="POST", data=b"",
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return 200 <= r.status < 300
        except Exception as e:
            logger.debug("[gov] reranker %s failed: %r", path, e)
            return False

    def suspend(self) -> bool:
        if self._state != "loaded":
            return False
        if self._post("/unload"):
            self._state = "unloaded"
            logger.info("[gov] reranker unloaded")
            return True
        return False

    def resume(self) -> bool:
        self._state = "loaded"
        return False


class _PaddlePoolAdapter:
    """PaddleOCR 池适配器：hook OcrEnginePool._engines。

    释放：遍历每个 PaddleOcrEngine，调其 _release_engine()，
         然后池 _engines.clear()。
    恢复：不主动恢复（下次 pool.get(lang) 懒加载）。
    """

    def __init__(self,
                 module_name: str = "backend.rag.ingest.ocr.engine_pool",
                 pool_getter: str = "get_default_pool",
                 name: str = "paddle_ocr"):
        self._mod = module_name
        self._get = pool_getter
        self.name = name
        self._suspended = False

    def _pool(self):
        try:
            import importlib
            mod = importlib.import_module(self._mod)
            getter = getattr(mod, self._get, None)
            return getter() if callable(getter) else None
        except Exception:
            return None

    def is_active(self) -> bool:
        if self._suspended:
            return False
        p = self._pool()
        if p is None:
            return False
        engines = getattr(p, "_engines", None) or {}
        return any(getattr(e, "_ocr", None) is not None
                   for e in engines.values())

    def suspend(self) -> bool:
        p = self._pool()
        if p is None:
            return False
        engines = getattr(p, "_engines", None)
        if not engines:
            return False
        released = 0
        for lang, e in list(engines.items()):
            fn = getattr(e, "_release_engine", None)
            if callable(fn):
                try:
                    fn()
                    released += 1
                except Exception as ex:
                    logger.debug("[gov] release %s failed: %r", lang, ex)
        try:
            engines.clear()
        except Exception:
            pass
        if released:
            self._suspended = True
            logger.info("[gov] paddle pool released %d engine(s)", released)
            return True
        return False

    def resume(self) -> bool:
        # 不主动恢复：下次 get(lang) 自动 _ensure_ocr()
        self._suspended = False
        return False


__all__ = ["_SingletonAdapter", "_RerankerAdapter", "_PaddlePoolAdapter"]
