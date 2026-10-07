"""Agent Tools FastAPI APIRouter 装配。
职责：创建 router + 挂端点 + envelope 包装。不实现 handler、不持有 runtime。"""
from __future__ import annotations
from typing import Any, Callable

from backend.agent_tools.router import (
    PREFIX, chat_handler_async, clear_session_handler,
    get_mounts_handler, list_tools_handler, set_mounts_handler)

def build_agent_tools_router(runtime_provider: Callable[[], Any]) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as e:
        raise RuntimeError("fastapi 未安装") from e

    router = APIRouter()

    async def _wrap(fn):
        try:
            r = fn()
            if hasattr(r, "__await__"):
                r = await r
            return {"ok": True, "data": r}
        except Exception as e:
            return {"ok": False, "error": {
                "code": type(e).__name__, "message": str(e)}}

    @router.get(f"{PREFIX}/tools")
    async def _list_tools():
        rt = runtime_provider()
        return await _wrap(lambda: list_tools_handler(rt.registry))

    @router.get(f"{PREFIX}/{{session_id}}/tools")
    async def _get_mounts(session_id: str):
        rt = runtime_provider()
        return await _wrap(lambda: get_mounts_handler(
            rt.mounts, rt.registry, session_id))

    @router.post(f"{PREFIX}/{{session_id}}/tools")
    async def _set_mounts(session_id: str, body: dict):
        rt = runtime_provider()
        return await _wrap(lambda: set_mounts_handler(
            rt.mounts, rt.registry, session_id, body))

    @router.post(f"{PREFIX}/{{session_id}}/chat")
    async def _chat(session_id: str, body: dict):
        rt = runtime_provider()
        return await _wrap(lambda: chat_handler_async(
            mounts=rt.mounts, registry=rt.registry,
            executor=rt.executor, history=rt.history,
            gateway=rt.gateway, sid=session_id, body=body))

    @router.delete(f"{PREFIX}/{{session_id}}")
    async def _clear(session_id: str):
        rt = runtime_provider()
        return await _wrap(lambda: clear_session_handler(
            rt.mounts, rt.history, session_id))

    return router

__all__ = ["build_agent_tools_router"]
