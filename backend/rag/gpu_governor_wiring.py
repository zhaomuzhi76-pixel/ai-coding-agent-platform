"""GPU Governor 与 backend 主进程的桥接层（单一职责）。

职责：注册已知单例 + reranker；给 lifespan 提供 start()，给 middleware 提供 touch()。
不做：不加载模型、不改模型、不管理 daemon（governor 管）。
默认关闭：RAG_GPU_GOVERNOR=0。
"""
from __future__ import annotations
import logging
import os
from typing import Any, Dict, Optional

from backend.rag.gpu_adapters import (
    _SingletonAdapter, _RerankerAdapter, _PaddlePoolAdapter,
)

logger = logging.getLogger(__name__)

_ENV_ENABLED = "RAG_GPU_GOVERNOR"
_ENV_IDLE = "RAG_GPU_GOVERNOR_IDLE_SEC"
_ENV_INT = "RAG_GPU_GOVERNOR_INTERVAL_SEC"
_ENV_RERANKER = "RAG_RERANKER_URL"

_DEFAULT_IDLE = 300
_DEFAULT_INTERVAL = 60
_DEFAULT_RERANKER = "http://127.0.0.1:9033"


def _enabled() -> bool:
    return os.environ.get(_ENV_ENABLED, "0") == "1"


# ---------- 公共 API ----------

def register_known_models() -> int:
    from backend.rag.gpu_governor import get_governor
    g = get_governor()
    n = 0
    specs = [
        ("backend.rag.multimodal.text_embedder",
         "_singleton", "_model", "_device", "text_embedder"),
        ("backend.rag.multimodal.clip_embedder",
         "_singleton", "_model", "_device", "clip_embedder"),
    ]
    for mod, sa, ma, da, name in specs:
        try:
            g.register(_SingletonAdapter(mod, sa, ma, da, name))
            n += 1
        except Exception as e:
            logger.debug("[gov] register %s failed: %r", name, e)
    # PaddleOCR 池（懒加载，未加载时不 active）
    try:
        g.register(_PaddlePoolAdapter())
        n += 1
    except Exception as e:
        logger.debug("[gov] register paddle pool failed: %r", e)
    return n


def register_reranker(url: Optional[str] = None) -> bool:
    from backend.rag.gpu_governor import get_governor
    u = url or os.environ.get(_ENV_RERANKER, _DEFAULT_RERANKER)
    try:
        get_governor().register(_RerankerAdapter(base_url=u))
        return True
    except Exception as e:
        logger.debug("[gov] register reranker failed: %r", e)
        return False


def start(interval: Optional[int] = None,
          idle: Optional[int] = None) -> bool:
    if not _enabled():
        return False
    from backend.rag.gpu_governor import get_governor
    n = register_known_models()
    register_reranker()
    iv = int(interval or os.environ.get(_ENV_INT, _DEFAULT_INTERVAL))
    idl = int(idle or os.environ.get(_ENV_IDLE, _DEFAULT_IDLE))
    ok = get_governor().start_daemon(interval=iv, idle=idl)
    print(f"[gov] wiring start registered={n} ok={ok} iv={iv} idle={idl}",
          flush=True)
    return ok


def touch() -> None:
    if not _enabled():
        return
    try:
        from backend.rag.gpu_governor import get_governor
        g = get_governor()
        g.touch()
        if any(not a.is_active() for a in g._adapters.values()):
            g.resume_all()
    except Exception:
        pass


def status() -> Dict[str, Any]:
    from backend.rag.gpu_governor import get_governor
    return get_governor().status()


def bootstrap(app: Any) -> bool:
    print(f"[gov] bootstrap._enabled()={_enabled()}", flush=True)
    if not _enabled():
        return False
    try:
        ok = start()
        print(f"[gov] start() -> {ok}", flush=True)
    except Exception as e:
        import traceback as _tb
        print(f"[gov] start() FAILED: {e!r}", flush=True)
        _tb.print_exc()
        return False
    try:
        @app.middleware("http")
        async def _gpu_touch_mw(request, call_next):
            touch()
            return await call_next(request)
        logger.info("[gov] touch middleware installed")
    except Exception as e:
        logger.warning("[gov] middleware install failed: %r", e)
    return ok


__all__ = ["start", "touch", "status", "bootstrap",
           "register_known_models", "register_reranker"]
