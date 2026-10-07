"""Agent Tools API handlers（框架无关）。职责：协议解析 + 转发。
不实现业务、不做路由、不持有 runtime（依赖注入）。"""
from __future__ import annotations
from typing import Any, Callable, Mapping

PREFIX = "/api/agent"

def _mapping(raw: Any, name: str) -> Mapping:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must be mapping")
    return raw

def _require_sid(sid: str) -> str:
    if not isinstance(sid, str) or not sid.strip():
        raise ValueError("session_id required")
    return sid

def list_tools_handler(registry) -> dict:
    groups: dict[str, list] = {}
    for d in registry.all():
        key = f"{d.category.value}.{d.domain.value}"
        groups.setdefault(key, []).append({
            "name": d.name, "description": d.description,
            "category": d.category.value, "domain": d.domain.value,
            "server": d.server, "tags": list(d.tags),
        })
    return {"total": registry.count(), "groups": groups}

def get_mounts_handler(mounts, registry, sid: str) -> dict:
    sid = _require_sid(sid)
    enabled = mounts.resolve(sid, registry)
    return {"session_id": sid, "enabled": sorted(enabled),
            "total": registry.count(), "enabled_count": len(enabled)}

def set_mounts_handler(mounts, registry, sid: str, body: Any) -> dict:
    sid = _require_sid(sid)
    m = _mapping(body, "body")
    if "enable" in m:
        names = m["enable"]
        if not isinstance(names, (list, tuple)):
            raise ValueError("enable must be list")
        mounts.set(sid, [str(x) for x in names], registry)
    elif "add" in m or "remove" in m:
        if "add" in m:
            adds = m["add"]
            if not isinstance(adds, (list, tuple)):
                raise ValueError("add must be list")
            mounts.add(sid, [str(x) for x in adds], registry)
        if "remove" in m:
            rms = m["remove"]
            if not isinstance(rms, (list, tuple)):
                raise ValueError("remove must be list")
            mounts.remove(sid, [str(x) for x in rms], registry)
    else:
        raise ValueError("body must contain enable | add | remove")
    return get_mounts_handler(mounts, registry, sid)

async def chat_handler_async(*, mounts, registry, executor, history,
                              gateway: Any, sid: str, body: Any) -> dict:
    from backend.agent_tools.chat_loop import run_chat_turn
    from backend.agent_tools.trigger.loop import (
        run_chat_turn_with_prefetch)
    from backend.agent_tools.mounts import WhitelistExecutor
    from backend.agent_tools.registry import ToolRegistry

    sid = _require_sid(sid)
    m = _mapping(body, "body")
    text = m.get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text required")
    enabled = mounts.resolve(sid, registry)

    filtered = ToolRegistry()
    for name in enabled:
        d = registry.get(name)
        if d: filtered.register(d)

    wrapped = WhitelistExecutor(executor, enabled)
    if gateway is None:
        raise RuntimeError("gateway not available")

    result = await run_chat_turn_with_prefetch(
        session_id=sid, user_text=text.strip(),
        gateway=gateway,
        provider=str(m.get("provider", "")), model=str(m.get("model", "")),
        executor=wrapped, registry=filtered, history=history)
    return {"ok": result.ok, "answer": result.answer,
            "error": result.error, "steps": result.steps,
            "tool_trace": [dict(t) for t in result.tool_trace],
              "images": list(getattr(result, "images", ()) or ())}

def clear_session_handler(mounts, history, sid: str) -> dict:
    sid = _require_sid(sid)
    mounts.clear_session(sid)
    history.drop(sid)
    return {"cleared": True, "session_id": sid}

__all__ = ["PREFIX", "list_tools_handler", "get_mounts_handler",
           "set_mounts_handler", "chat_handler_async", "clear_session_handler"]
