"""监控 API 路由"""
from typing import Any, Dict, List

from fastapi import APIRouter, Query

from backend.monitor.recorder import clear_calls, list_calls
from backend.monitor.stats import by_model, by_provider, summary, trend
from backend.monitor.pricing import list_pricing, set_pricing


def build_monitor_router() -> APIRouter:
    r = APIRouter(tags=["monitor"], prefix="/api/monitor")

    @r.get("/summary")
    async def _summary(hours: int = Query(24)) -> Dict[str, Any]:
        return summary(hours)

    @r.get("/trend")
    async def _trend(hours: int = Query(24),
                     granularity: str = Query("hour")) -> List[Dict[str, Any]]:
        return trend(hours, granularity)

    @r.get("/by-model")
    async def _by_model(hours: int = Query(24)) -> List[Dict[str, Any]]:
        return by_model(hours)

    @r.get("/by-provider")
    async def _by_provider(hours: int = Query(24)) -> List[Dict[str, Any]]:
        return by_provider(hours)

    @r.get("/calls")
    async def _calls(limit: int = Query(200),
                     since: float = Query(0),
                     provider: str = Query(""),
                     model: str = Query("")) -> List[Dict[str, Any]]:
        return list_calls(limit=limit, since=since or None,
                          provider=provider, model=model)

    @r.delete("/calls")
    async def _clear() -> Dict[str, Any]:
        return {"deleted": clear_calls()}

    @r.get("/pricing")
    async def _list_pricing() -> List[Dict[str, Any]]:
        return list_pricing()

    @r.post("/pricing")
    async def _set_pricing(payload: Dict[str, Any]) -> Dict[str, Any]:
        set_pricing(payload["model"],
                    payload.get("input", 0.0), payload.get("output", 0.0))
        return {"ok": True}

    return r
