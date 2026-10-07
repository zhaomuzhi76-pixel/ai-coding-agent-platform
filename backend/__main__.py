from __future__ import annotations
from backend.core.observability.silent import swallow

from backend.api.system_monitor_router import router as _system_monitor_router

from backend.api.observability import (
    build_observability_router,
)
from backend.api.security import build_security_router
from backend.api.mcp import build_mcp_router
from backend.api.monitor import build_monitor_router
from backend.api.mcp_ext import build_mcp_ext_router
from backend.api.rag import build_rag_router
from backend.api.rag.multimodal_runtime import build_multimodal_rag_router
from backend.api.rag.ingest_runtime import build_ingest_router
from backend.api.rag.config_router import router as rag_config_router
from backend.api.rag.vector_admin_router import router as rag_vector_admin_router
from backend.api.rag.vector_admin_rename import (
    router as vector_admin_rename_router,
)
from backend.api.rag.ingest_detail_router import router as rag_ingest_detail_router
from backend.agent_tools.application_router import build_agent_tools_router
from backend.agent_tools.runtime import get_agent_tools_runtime
from backend.mcp_client.api_router import build_mcp_client_router
from backend.mcp_client.runtime import restore_enabled as mcp_restore
from backend.api.chatbot.application_router import build_chatbot_router
from backend.api.finetune import build_finetune_router
from backend.api.finetune.rag_bridge import router as finetune_rag_bridge_router
from backend.api.finetune.ws_router import router as finetune_ws_router
from backend.api.finetune.deploy_ws import router as finetune_deploy_ws_router
from backend.api.platform import build_platform_router
from backend.api.platform.apply_ws import router as platform_apply_ws_router
from backend.api.platform.ws import router as platform_ws_router
from backend.runtime.terminal.terminal_ws import router as terminal_router
from backend.api.ws_agent import router as ws_agent_router
from backend.api.cost import build_cost_router
from backend.providers.benchmark.api import (
    build_benchmark_router,
)
from backend.api.providers import build_provider_router
from backend.api.agent.approval_api import (
    router as agent_approval_router,
)
from backend.api.agent.audit_api import (
    router as agent_audit_router,
)
from backend.agent_learning.memory_router import build_memory_router
from backend.rag.ingest.review.api.review_router_factories import (
    build_review_ui_router,
    build_reranker_center_router,
    build_provider_center_router,
    build_recall_test_router,
)
from backend.core.model_registry.adapters.fastapi_adapter import (
    build_router as build_model_registry_router,
)
from backend.core.model_registry.adapters.fastapi_ext import (
    build_router_ext as build_model_registry_router_ext,
)
from backend.api.providers_catalog import build_providers_catalog_router
from backend.api.server.application_lifespan import (
    ApplicationLifespan,
)
from backend.assembly.fastapi_application import (
    create_application,
)
from backend.api.static_frontend import mount_frontend
from backend.application.agent_runtime.multiplex.entry import (
    shutdown_team as shutdown_multiplex,
)
from backend.bootstrap import bootstrap, shutdown
from backend.process_main.process_main_entry import (
    VERSION,
    main,
)



def _build_system_monitor_router():
    return _system_monitor_router

def create_process_application():
    _inner_lifespan = ApplicationLifespan(
        bootstrap=bootstrap,
        shutdown=shutdown,
    ).lifespan

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _lifespan_with_mcp(app):
        async with _inner_lifespan(app):
            # 应用启动完成后：后台异步恢复 MCP server（不阻塞）
            import asyncio as _aio
            async def _bg_restore():
                try:
                    r = await mcp_restore()
                    print(f"[mcp_client] restore done {r}", flush=True)
                except Exception as e:
                    print(f"[mcp_client] restore failed: {e}", flush=True)
            _task = _aio.create_task(_bg_restore())
            yield
            try:
                _task.cancel()
            except Exception as e:
                swallow("__main__:84", e)
    app = create_application(
        lifespan=_lifespan_with_mcp,
        routers=[
            build_observability_router(),
            build_security_router(),
            build_mcp_router(),
            build_monitor_router(),
            _build_system_monitor_router(),
            build_mcp_ext_router(),
            build_rag_router(),
            build_multimodal_rag_router(),
            build_ingest_router(),
            rag_config_router,
            rag_vector_admin_router,
            vector_admin_rename_router,
            rag_ingest_detail_router,
            build_agent_tools_router(get_agent_tools_runtime),
            build_mcp_client_router(),
            build_chatbot_router(),
            build_finetune_router(),
            finetune_ws_router,
            finetune_rag_bridge_router,
            finetune_deploy_ws_router,
            build_platform_router(),
            platform_apply_ws_router,
            build_cost_router(),
            build_benchmark_router(),
            build_provider_router(),
            platform_ws_router,
            terminal_router,
            ws_agent_router,
            agent_approval_router,
            agent_audit_router,
            build_review_ui_router(),
            build_reranker_center_router(),
            build_provider_center_router(),
            build_recall_test_router(),
            build_memory_router(),
            build_model_registry_router(),
            build_model_registry_router_ext(),
            build_providers_catalog_router(),
        ],
    )

    # [DUAL-SEARCH] 图文双路检索端点
    try:
        from backend.api.rag.dual_search_router import register_dual_search_routes
        from fastapi import APIRouter as _AR
        _dual = _AR()
        register_dual_search_routes(_dual)
        app.include_router(_dual)
        print("[dual-search] mounted /api/rag/dual-search", flush=True)
    except Exception as _e:
        print(f"[dual-search] mount failed: {_e!r}", flush=True)

    # [RAG-QA] 完整 RAG QA 端点
    try:
        from backend.api.rag.qa_router import register_qa_routes
        from fastapi import APIRouter as _AR
        _qa = _AR()
        register_qa_routes(_qa)
        app.include_router(_qa)
        print("[rag-qa] mounted /api/rag/qa", flush=True)
    except Exception as _e:
        print(f"[rag-qa] mount failed: {_e!r}", flush=True)

    mount_frontend(app)

    # [IMG-ROUTE] 挂载静态图片路由 /data/images/*
    try:
        from backend.api.images_router import register_images_routes
        register_images_routes(app)
        print("[img-route] mounted /data/images/*", flush=True)
    except Exception as _e:
        print(f"[img-route] mount failed: {_e!r}", flush=True)


    # [GPU-GOVERNOR] bootstrap（唯一入口）
    try:
        import os as _os
        if _os.environ.get("RAG_GPU_GOVERNOR", "0") == "1":
            from backend.rag.gpu_governor_wiring import bootstrap as _gpu_boot
            print(f"[gov] bootstrap -> {_gpu_boot(app)}", flush=True)
    except Exception as _e:
        import traceback as _tb
        print(f"[gov] bootstrap FAILED: {_e!r}", flush=True)
        _tb.print_exc()

    # 应用退出时清理 multiplex 子进程（防僵尸）
    @app.on_event("shutdown")
    async def _shutdown_multiplex():
        try:
            await shutdown_multiplex()
        except Exception as e:
            swallow("__main__:126", e)

    return app



def run() -> int:
    application = create_process_application()
    return main(application=application)


__all__ = [
    "VERSION",
    "create_process_application",
    "main",
    "run",
]


if __name__ == "__main__":
    run()
