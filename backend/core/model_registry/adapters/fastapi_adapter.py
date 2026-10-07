"""FastAPI 适配层 - 把 framework-agnostic 路由挂到 FastAPI（零业务逻辑）"""
from typing import Any, Callable, Dict, List

from fastapi import APIRouter, Body, HTTPException

from ..api_routes_kinds import list_kinds as list_provider_kinds
from ..api_routes import (
    bind_role, create_provider, get_kpi, list_models, list_providers,
    list_roles, test_provider,
)

P = "/api/model-registry"


def _wrap(fn: Callable) -> Callable:
    """统一把 KeyError/ValueError 映射为 HTTP 400"""
    def _inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except KeyError as exc:
            raise HTTPException(400, f"missing field: {exc}")
        except ValueError as exc:
            raise HTTPException(400, str(exc))
    return _inner


def build_router() -> APIRouter:
    r = APIRouter(tags=["model-registry"])

    @r.get(f"{P}/providers")
    async def _list_providers() -> List[Dict[str, Any]]:
        return list_providers()

    @r.post(f"{P}/providers")
    async def _create_provider(
        payload: Dict[str, Any] = Body(...),
    ) -> Dict[str, Any]:
        return _wrap(create_provider)(payload)

    @r.get(f"{P}/providers/{{provider_id}}/models")
    async def _list_models(provider_id: str) -> List[Dict[str, Any]]:
        return list_models(provider_id)

    @r.post(f"{P}/providers/{{provider_id}}/test")
    async def _test_provider(provider_id: str) -> Dict[str, Any]:
        return test_provider(provider_id)

    @r.get(f"{P}/roles")
    async def _list_roles() -> List[Dict[str, Any]]:
        return list_roles()

    @r.post(f"{P}/roles")
    async def _bind_role(
        payload: Dict[str, Any] = Body(...),
    ) -> Dict[str, Any]:
        return _wrap(bind_role)(payload)

    @r.get(f"{P}/provider-kinds")
    async def _provider_kinds():
        return list_provider_kinds()

    @r.get(f"{P}/kpi")
    async def _get_kpi() -> Dict[str, Any]:
        return get_kpi()

    return r


def mount(app) -> None:
    """把 model_registry 挂到现有 FastAPI 应用"""
    app.include_router(build_router())
    try:
        from .fastapi_ext import build_router_ext
        app.include_router(build_router_ext())
    except ImportError:
        pass
