"""MCP Client REST API。职责：协议解析 + 转发 runtime + envelope。
不实现业务、不持状态。"""
from __future__ import annotations
from typing import Any, Mapping

PREFIX = "/api/mcp_client"

def _mapping(raw: Any, name: str) -> Mapping:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must be mapping")
    return raw

def build_mcp_client_router() -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as e:
        raise RuntimeError("fastapi 未安装") from e

    from backend.mcp_client.contracts import ServerConfig
    from backend.mcp_client.runtime import (
        add_server, list_servers, reconnect_server, remove_server,
        server_tools, total_tool_count)

    router = APIRouter()

    async def _wrap(fn, *args, **kw):
        try:
            r = fn(*args, **kw)
            if hasattr(r, "__await__"):
                r = await r
            return {"ok": True, "data": r}
        except Exception as e:
            return {"ok": False, "error": {
                "code": type(e).__name__, "message": str(e)}}

    @router.get(f"{PREFIX}/servers")
    async def _list():
        return await _wrap(lambda: {
            "servers": list_servers(),
            "total": len(list_servers()),
            "tool_count": total_tool_count(),
        })

    @router.post(f"{PREFIX}/servers")
    async def _add(body: dict):
        def _do():
            m = _mapping(body, "body")
            cfg = ServerConfig.from_dict(m)
            return add_server(cfg)
        return await _wrap(_do)

    @router.delete(f"{PREFIX}/servers/{{sid}}")
    async def _del(sid: str):
        return await _wrap(remove_server, sid)

    @router.post(f"{PREFIX}/servers/{{sid}}/reconnect")
    async def _recon(sid: str):
        return await _wrap(reconnect_server, sid)

    @router.get(f"{PREFIX}/servers/{{sid}}/tools")
    async def _tools(sid: str):
        return await _wrap(lambda: {
            "server_id": sid, "tools": server_tools(sid),
            "count": len(server_tools(sid)),
        })

    return router

__all__ = ["build_mcp_client_router", "PREFIX"]
