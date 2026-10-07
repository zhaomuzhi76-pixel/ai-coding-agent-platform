"""ObservabilityRouter: FastAPI transport for observability data."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.observability.binding import ObservabilityBinding


class ObservabilityRouter:
    VERSION = "1.0"
    PREFIX = "/api/observability"

    def __init__(self, binding: ObservabilityBinding) -> None:
        if not isinstance(binding, ObservabilityBinding):
            raise TypeError("binding must ObservabilityBinding")
        self.binding = binding
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.get(f"{p}/summary")(self.summary)
        self.router.get(f"{p}/spans")(self.spans)
        self.router.get(f"{p}/spans/by-name/{{name}}")(self.by_name)
        self.router.get(f"{p}/errors")(self.errors)
        self.router.get(f"{p}/alerts")(self.alerts)
        self.router.get(f"{p}/report")(self.report)
        self.router.post(f"{p}/reset")(self.reset)

    async def summary(self) -> JSONResponse:
        return await self._wrap(self.binding.summary)

    async def spans(self, limit: int = 200) -> JSONResponse:
        return await self._wrap(lambda: self.binding.spans(limit))

    async def by_name(self, name: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.by_name(name))

    async def errors(self) -> JSONResponse:
        return await self._wrap(self.binding.errors)

    async def alerts(self) -> JSONResponse:
        return await self._wrap(self.binding.alerts)

    async def report(self, buckets: int = 8) -> JSONResponse:
        return await self._wrap(lambda: self.binding.report(buckets))

    async def reset(self) -> JSONResponse:
        return await self._wrap(self.binding.reset)

    async def _wrap(
        self, fn: Callable[[], Any],
    ) -> JSONResponse:
        try:
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": fn()},
            )
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": {
                        "code": "INTERNAL",
                        "message": f"{type(exc).__name__}: {exc}",
                    },
                },
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


__all__ = ["ObservabilityRouter"]
