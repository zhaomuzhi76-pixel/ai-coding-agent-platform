"""FastAPI 扩展路由适配"""
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

from ..api_routes_ext import (
    _delete, _export, _import, _kpi, _models, _update,
    _verified_models, _verify,
)
from ..probe import probe_provider
from ..api_routes_role_ext import _cost, _test

P = "/api/model-registry"


def build_router_ext() -> APIRouter:
    r = APIRouter(tags=["model-registry-ext"])

    @r.get(P + "/models")
    async def _m():
        return _models()

    @r.patch(P + "/providers/{pid}")
    async def _u(pid: str, payload: Dict[str, Any] = Body(...)):
        try:
            return _update(pid, payload)
        except KeyError as e:
            raise HTTPException(404, str(e))

    @r.delete(P + "/providers/{pid}")
    async def _d(pid: str):
        try:
            return _delete(pid)
        except KeyError as e:
            raise HTTPException(404, str(e))

    @r.get(P + "/kpi/usage")
    async def _k():
        return _kpi()

    @r.get(P + "/config/export")
    async def _ex():
        return _export("json")

    @r.get(P + "/config/export/yaml")
    async def _ey():
        return _export("yaml")

    @r.post(P + "/config/import")
    async def _im(payload: Dict[str, Any] = Body(...)):
        try:
            return _import(payload)
        except ValueError as e:
            raise HTTPException(400, str(e))

    @r.post(P + "/providers/{pid}/verify")
    async def _v(pid: str):
        return _verify(pid)

    @r.get(P + "/verified-models")
    async def _vm():
        return _verified_models()

    @r.post(P + "/providers/probe")
    async def _probe(payload: Dict[str, Any] = Body(...)):
        return probe_provider(payload)

    @r.get(P + "/cost-estimate")
    async def _ce():
        return _cost()

    @r.post(P + "/roles/{role}/test")
    async def _rt(role: str):
        return await _test(role)

    return r
