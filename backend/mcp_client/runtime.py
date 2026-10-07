"""MCP Client runtime 单例 + agent_tools 挂载协调。
职责：持有 manager + registry；把 MCP 远端工具接入 agent_tools。
不实现协议（底层 mcp/* 管）、不落盘（registry 管）、不做 REST（api_router 管）。"""
from __future__ import annotations
from typing import Any, Optional

from backend.mcp_client.contracts import ServerConfig, ServerStatus
from backend.mcp_client.executor_provider import McpToolProvider
from backend.mcp_client.registry import (
    ServerRegistry, get_default_registry, set_default_registry)
from backend.mcp_client.session_manager import (
    SessionManager, get_default_manager, set_default_manager)
from backend.mcp_client.tool_adapter import route_to_descriptor

def get_manager() -> SessionManager:
    return get_default_manager()

def get_registry() -> ServerRegistry:
    return get_default_registry()

def attach_to_agent_tools() -> int:
    """幂等：provider 挂一次；工具 descriptors 每次刷新。
    返回已注册的 MCP 工具数。"""
    from backend.agent_tools.runtime import get_agent_tools_runtime
    rt = get_agent_tools_runtime()
    mgr = get_manager()
    existing = rt.executor.providers() if hasattr(rt.executor, "providers") else []
    if not any(isinstance(p, McpToolProvider) for p in existing):
        rt.executor.add_provider(McpToolProvider(mgr))
    n = 0
    for name in mgr.tool_names():
        target = mgr.resolve(name)
        if target is None:
            continue
        rt.registry.register(route_to_descriptor(target, description=""))
        n += 1
    return n

def detach_tools(sid: str) -> int:
    """从 agent_tools 摘掉某个 server 的所有工具。"""
    try:
        from backend.agent_tools.runtime import get_agent_tools_runtime
        return get_agent_tools_runtime().registry.unregister_by_server(sid)
    except Exception:
        return 0

# ─── 编排操作 ─────────────────────────────────────────────
async def add_server(config: ServerConfig, *,
                     persist: bool = True) -> Any:
    mgr = get_manager()
    state = await mgr.add(config)
    if persist:
        get_registry().add(config)
    if state.status is ServerStatus.ONLINE:
        attach_to_agent_tools()
    return state.to_dict()

async def remove_server(sid: str, *, persist: bool = True) -> bool:
    mgr = get_manager()
    removed = await mgr.remove(sid)
    if persist:
        get_registry().remove(sid)
    detach_tools(sid)
    return removed

async def reconnect_server(sid: str) -> Any:
    reg = get_registry()
    cfg = reg.get(sid)
    if cfg is None:
        raise KeyError(f"server config not found: {sid}")
    return await add_server(cfg, persist=False)

async def close_all() -> None:
    await get_manager().close_all()
    try:
        from backend.agent_tools.runtime import get_agent_tools_runtime
        rt = get_agent_tools_runtime()
        for s in get_manager().states():
            rt.registry.unregister_by_server(s.server_id)
    except Exception:  # silent-ok
        pass

# ─── 查询视图 ─────────────────────────────────────────────
def list_servers() -> list[dict]:
    reg = get_registry()
    mgr = get_manager()
    out: list[dict] = []
    for c in reg.all():
        st = mgr.state(c.id)
        out.append({
            "config": c.to_dict(),
            "status": st.to_dict() if st is not None else {
                "server_id": c.id, "status": "disconnected",
                "tool_count": 0, "error": "", "started_at": 0,
                "server_info": {},
            },
        })
    return out

def server_tools(sid: str) -> list[dict]:
    mgr = get_manager()
    out: list[dict] = []
    for name in mgr.tool_names():
        t = mgr.resolve(name)
        if t is None or t.server_id != sid:
            continue
        out.append({"namespaced_name": t.namespaced_name,
                    "raw_name": t.raw_name, "server_id": t.server_id})
    return out

def total_tool_count() -> int:
    return len(get_manager().tool_names())

async def restore_enabled() -> dict:
    """启动时并发重连所有 enabled server。"""
    import asyncio as _aio
    reg = get_registry()
    configs = reg.enabled()
    results = await _aio.gather(
        *[add_server(c, persist=False) for c in configs],
        return_exceptions=True,
    )
    def _is_online(r):
        if isinstance(r, Exception):
            return False
        if isinstance(r, dict):
            return r.get("status") == "online"
        return getattr(r, "status", None) is ServerStatus.ONLINE

    online = sum(1 for r in results if _is_online(r))
    return {"online": online, "failed": len(configs) - online,
            "total": len(configs)}

__all__ = ["get_manager", "get_registry", "attach_to_agent_tools",
           "detach_tools", "add_server", "remove_server",
           "reconnect_server", "close_all", "list_servers",
           "server_tools", "total_tool_count", "restore_enabled"]
