"""Provider Router: 配置中心 HTTP 端点。"""
from __future__ import annotations

from typing import Any, Callable, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.providers.binding import ProviderBinding


class ProviderRouter:
    VERSION = "2.0"
    PREFIX = "/api/providers"

    def __init__(self, binding: ProviderBinding) -> None:
        if not isinstance(binding, ProviderBinding):
            raise TypeError("binding must ProviderBinding")
        self.binding = binding
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.get(f"{p}/config")(self.config)
        self.router.get(f"{p}/models")(self.models)
        self.router.get(f"{p}/local-models/{{name}}")(self.local_models)
        self.router.get(f"{p}/verified")(self.verified)
        self.router.get(f"{p}/health")(self.health)
        self.router.get(f"{p}/health/cached")(self.health_cached)
        self.router.get(f"{p}/cost")(self.cost)
        self.router.get(f"{p}/raw-yaml")(self.raw_yaml)
        self.router.post(f"{p}/upsert")(self.upsert)
        self.router.delete(f"{p}/{{name}}")(self.delete)
        self.router.post(f"{p}/test")(self.test)

    async def config(self) -> JSONResponse:
        return await self._wrap(self.binding.config)

    async def models(self) -> JSONResponse:
        return await self._wrap(self.binding.models)

    async def local_models(
        self, name: str, base_url: str = "",
    ) -> JSONResponse:
        return await self._wrap_async(
            lambda: self.binding.local_models(name, base_url=base_url)
        )

    async def verified(self) -> JSONResponse:
        return await self._wrap(self.binding.verified)

    async def health(self) -> JSONResponse:
        return await self._wrap_async(self.binding.health)

    async def health_cached(self) -> JSONResponse:
        return await self._wrap(self.binding.health_cached)

    async def cost(self) -> JSONResponse:
        return await self._wrap(self.binding.cost)

    async def raw_yaml(self) -> JSONResponse:
        return await self._wrap(self.binding.raw_yaml)

    async def upsert(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap(lambda: self.binding.upsert(payload))

    async def delete(self, name: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.delete(name))

    async def test(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap_async(lambda: self.binding.test(payload))

    async def _wrap(self, fn: Callable[[], Any]) -> JSONResponse:
        try:
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": fn()},
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": {
                    "code": "BAD_REQUEST", "message": str(exc)}},
            )
        except Exception as exc:
            return self._error(exc)

    async def _wrap_async(self, fn: Callable) -> JSONResponse:
        try:
            result = await fn()
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": result},
            )
        except Exception as exc:
            return self._error(exc)

    @staticmethod
    def _error(exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": {
                "code": "INTERNAL",
                "message": f"{type(exc).__name__}: {exc}"}},
        )

    def ready(self) -> bool:
        return self.binding.ready()

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }


__all__ = ["ProviderRouter"]
