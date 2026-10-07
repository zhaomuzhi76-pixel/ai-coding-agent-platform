"""Cost Router."""
from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.cost.binding import CostBinding


class CostRouter:
    VERSION = "2.0"
    PREFIX = "/api/cost"

    def __init__(self, binding: CostBinding) -> None:
        if not isinstance(binding, CostBinding):
            raise TypeError("binding must CostBinding")
        self.binding = binding
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.get(f"{p}/summary")(self.summary)
        self.router.get(f"{p}/stats")(self.stats)
        self.router.get(f"{p}/by-model")(self.by_model)
        self.router.get(f"{p}/by-provider")(self.by_provider)
        self.router.get(f"{p}/recent")(self.recent)
        self.router.get(f"{p}/prices")(self.prices)
        self.router.post(f"{p}/reset")(self.reset)

    async def summary(self) -> JSONResponse:
        return await self._wrap(self.binding.summary)

    async def stats(
        self,
        days: Optional[int] = None,
        since: Optional[float] = None,
        until: Optional[float] = None,
    ) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.stats(
                since=since, until=until, days=days,
            )
        )

    async def by_model(
        self, days: Optional[int] = None,
    ) -> JSONResponse:
        return await self._wrap(lambda: self.binding.by_model(days))

    async def by_provider(
        self, days: Optional[int] = None,
    ) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.by_provider(days)
        )

    async def recent(self, limit: int = 50) -> JSONResponse:
        return await self._wrap(lambda: self.binding.recent(limit))

    async def prices(self) -> JSONResponse:
        return await self._wrap(self.binding.prices)

    async def reset(self) -> JSONResponse:
        return await self._wrap(self.binding.reset)

    async def _wrap(self, fn: Callable[[], Any]) -> JSONResponse:
        try:
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": fn()},
            )
        except Exception as exc:
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


__all__ = ["CostRouter"]
