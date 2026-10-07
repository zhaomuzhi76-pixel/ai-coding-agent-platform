"""MCP 扩展端点：自定义工具 CRUD + 启用/禁用"""
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

from backend.mcp.custom_registry import (
    delete_custom, list_custom, list_disabled, register_custom, toggle_tool,
)

P = "/api/mcp"


def build_mcp_ext_router() -> APIRouter:
    r = APIRouter(tags=["mcp-ext"])

    @r.get(P + "/custom-tools")
    async def _list() -> Dict[str, Any]:
        disabled = set(list_disabled())
        tools = []
        for t in list_custom():
            item = dict(t)
            item["disabled"] = t["name"] in disabled
            tools.append(item)
        return {"tools": tools, "count": len(tools)}

    @r.post(P + "/custom-tools")
    async def _create(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            return {"ok": True, "tool": register_custom(payload)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @r.delete(P + "/custom-tools/{name}")
    async def _delete(name: str) -> Dict[str, Any]:
        if not delete_custom(name):
            raise HTTPException(404, f"工具不存在: {name}")
        return {"ok": True, "name": name}

    @r.post(P + "/tools/{name}/toggle")
    async def _toggle(name: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        enabled = bool(payload.get("enabled", True))
        toggle_tool(name, enabled)
        return {"ok": True, "name": name, "enabled": enabled}

    @r.get(P + "/tools/disabled")
    async def _disabled() -> Dict[str, Any]:
        return {"disabled": list_disabled()}

    return r
