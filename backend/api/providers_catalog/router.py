"""GET /api/providers/catalog —— 给 Agent 工作区前端提供 chat 模型清单

数据源：Model Registry 的 verified 列表。
若 verified 为空，则对已 connected 的 Provider 自动触发验证（一次性），
保持与启动探测一致，避免重启后下拉变空。
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from backend.core.model_registry.registry import get_registry


def _auto_verify_connected(reg) -> None:
    """对已连接但未验证的 Provider 自动触发验证（保持门禁语义：
    只有启动探测通过 / 人工测试过的才在列）"""
    try:
        health = reg.health()
    except Exception:
        return
    for pid, ok in health.items():
        if not ok:
            continue
        provider_models = [m.id for m in reg.models.values()
                           if m.provider_id == pid]
        # 全部已 verified 就跳过
        if provider_models and all(
            reg.verification.is_verified(mid) for mid in provider_models
        ):
            continue
        try:
            reg.test_and_verify(pid)
        except Exception:
            continue


def _build_snapshot() -> Dict[str, Any]:
    try:
        reg = get_registry()
    except Exception:
        return {"defaultModelId": "", "models": []}

    if not reg.verification.list_verified():
        _auto_verify_connected(reg)

    verified = reg.verification.list_verified()
    models: List[Dict[str, Any]] = []
    for mid in verified:
        m = reg.models.get(mid)
        if not m:
            continue
        if not reg._is_chat_model(m.id, m.display_name):
            continue
        models.append({
            "id": m.id,
            "provider": m.provider_id,
            "displayName": f"{m.id} · {m.provider_id}",
            "contextWindow": m.context_window,
            "isDefault": False,
        })

    route = reg.roles.get("code")
    default_id = ""
    if route and any(x["id"] == route.primary for x in models):
        default_id = route.primary
        for x in models:
            if x["id"] == default_id:
                x["isDefault"] = True
    elif models:
        default_id = models[0]["id"]
        models[0]["isDefault"] = True

    return {"defaultModelId": default_id, "models": models}


def build_providers_catalog_router() -> APIRouter:
    r = APIRouter(tags=["providers-catalog"])

    @r.get("/api/providers/catalog")
    async def catalog() -> Dict[str, Any]:
        return _build_snapshot()

    return r
