"""ASGI 中间件安装器（幂等 · FastAPI/Starlette/裸 ASGI 兼容）。

职责：单一（把并发守卫挂到 app）。
不做：限流逻辑、缓存逻辑、路由。

零硬编码：
  · 所有参数从 config.load() 读
  · Retry-After 从 retry_policy.compute() 动态算
  · 白名单路径从 cfg.whitelist_paths 读
"""
from __future__ import annotations
from typing import Optional

from backend.api.middleware import retry_policy as _rp
from backend.api.middleware.config import MWConfig, load as _load_cfg


def _is_whitelisted(path: str, cfg: MWConfig) -> bool:
    """按前缀匹配免限流路径。"""
    p = path or ""
    for w in cfg.whitelist_paths:
        if w and p.startswith(w):
            return True
    return False


class ConcurrencyGuardMiddleware:
    """标准 ASGI 中间件（供 FastAPI/Starlette add_middleware 使用）。"""

    def __init__(self, app, max_concurrent: Optional[int] = None,
                 timeout_s: Optional[float] = None,
                 cfg: Optional[MWConfig] = None):
        from backend.api.middleware.concurrency_guard import ConcurrencyGuard
        self.cfg = cfg or _load_cfg()
        mc = max_concurrent if max_concurrent is not None else self.cfg.max_concurrent
        ts = timeout_s if timeout_s is not None else self.cfg.timeout_s
        self.app = app
        self.guard = ConcurrencyGuard(max_concurrent=mc, timeout_s=ts)
        self.max_concurrent = mc
        self.timeout_s = ts

    def _build_503(self):
        """动态生成 503 body + Retry-After。"""
        snap = self.guard.snapshot()
        return _rp.build_503_payload(snap, self.cfg)

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        if _is_whitelisted(scope.get("path", ""), self.cfg):
            await self.app(scope, receive, send)
            return
        if not await self.guard.acquire():
            body, ra, _hint = self._build_503()
            await send({"type": "http.response.start", "status": 503,
                        "headers": [(b"content-type", b"application/json"),
                                    (b"retry-after", str(ra).encode())]})
            await send({"type": "http.response.body", "body": body})
            return
        try:
            await self.app(scope, receive, send)
        finally:
            self.guard.release()


def install(app, *, max_concurrent: Optional[int] = None,
            timeout_s: Optional[float] = None, force: bool = False,
            cfg: Optional[MWConfig] = None):
    """幂等安装并发守卫（FastAPI 优先，裸 ASGI 回退）。"""
    if getattr(app, "_rag_mw_installed", False):
        return app
    app._rag_mw_installed = True

    effective_cfg = cfg or _load_cfg()
    if not effective_cfg.enabled and not force:
        app._rag_mw_guard = None
        return app

    mc = max_concurrent if max_concurrent is not None else effective_cfg.max_concurrent
    ts = timeout_s if timeout_s is not None else effective_cfg.timeout_s

    if hasattr(app, "add_middleware"):
        app.add_middleware(ConcurrencyGuardMiddleware,
                           max_concurrent=mc, timeout_s=ts,
                           cfg=effective_cfg)
        app._rag_mw_guard = None
        app._rag_mw_cfg = (mc, ts)
        return app

    from backend.api.middleware.concurrency_guard import ConcurrencyGuard
    guard = ConcurrencyGuard(max_concurrent=mc, timeout_s=ts)

    async def wrapped(scope, receive, send):
        if scope.get("type") != "http":
            await app(scope, receive, send)
            return
        if _is_whitelisted(scope.get("path", ""), effective_cfg):
            await app(scope, receive, send)
            return
        if not await guard.acquire():
            body, ra, _hint = _rp.build_503_payload(guard.snapshot(), effective_cfg)
            await send({"type": "http.response.start", "status": 503,
                        "headers": [(b"content-type", b"application/json"),
                                    (b"retry-after", str(ra).encode())]})
            await send({"type": "http.response.body", "body": body})
            return
        try:
            await app(scope, receive, send)
        finally:
            guard.release()

    app._rag_mw_guard = guard
    app._rag_mw_wrapped = wrapped
    return app


def is_installed(app) -> bool:
    return bool(getattr(app, "_rag_mw_installed", False))
