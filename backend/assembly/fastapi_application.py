from __future__ import annotations

from collections.abc import Callable, Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


VERSION = "3.1"


def create_application(
    *,
    lifespan: Callable | None = None,
    routers: Iterable[object] = (),
) -> FastAPI:
    """
    Sole FastAPI construction owner.

    Owns only:
        - FastAPI object construction
        - CORS middleware binding
        - injected router registration
        - health endpoint
        - lifespan binding

    Does not own:
        - API router construction
        - ApplicationLifespan construction
        - bootstrap
        - runtime construction
        - process execution
        - WebSocket dependency construction
    """
    application = FastAPI(
        title="Biancheng AI Agent",
        version="2.0",
        lifespan=lifespan,
    )

    # [rag-embedded-mount] 嵌入式挂载 RAG 知识库插件（不修改原有逻辑）
    try:
        from rag_core.integration import mount_rag as _rag_mount
        if _rag_mount(application):
            import logging as _rag_log
            _rag_log.getLogger(__name__).info("[rag-embedded] RAG 知识库路由已挂载")
    except Exception as _rag_e:
        import logging as _rag_log
        _rag_log.getLogger(__name__).warning("[rag-embedded] 挂载失败: %s", _rag_e)


    # 允许 Electron file:// / 本地启动器 等所有 origin
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in routers:
        include_router = getattr(
            application,
            "include_router",
            None,
        )
        if not callable(include_router):
            raise TypeError(
                "FastAPI application must expose "
                "include_router()"
            )

        if router is None:
            raise ValueError(
                "router must not be None"
            )

        include_router(router)

    @application.get("/health")
    async def health():
        return {
            "status": "ok"
        }

    # [MW] 并发中间件（幂等 · RAG_MW_ENABLED 开关）
    try:
        from backend.api.middleware.install import install as _mw_install
        _mw_install(application)
    except Exception:
        import logging as _mw_log
        _mw_log.getLogger(__name__).warning('[MW] 挂载失败')

    # [Prom] /metrics 端点（幂等 · 独立文件 · 在函数内挂载）
    try:
        from backend.api.middleware.prometheus_exporter import (
            build_metrics_route as _build_prom,
        )
        _build_prom(application)
    except Exception:
        pass

    return application


__all__ = ["VERSION", "create_application"]
