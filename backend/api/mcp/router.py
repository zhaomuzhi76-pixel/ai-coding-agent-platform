"""McpRouter: FastAPI transport for MCP data."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.mcp.binding import McpBinding


class McpRouter:
    VERSION = "1.0"
    PREFIX = "/api/mcp"

    def __init__(self, binding: McpBinding) -> None:
        if not isinstance(binding, McpBinding):
            raise TypeError("binding must McpBinding")
        self.binding = binding
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.get(f"{p}/summary")(self.summary)
        self.router.get(f"{p}/tools")(self.tools)
        self.router.get(f"{p}/servers")(self.servers)
        self.router.get(f"{p}/domains")(self.domains)

    async def summary(self) -> JSONResponse:
        return await self._wrap(self.binding.summary)

    async def tools(self) -> JSONResponse:
        return await self._wrap(self.binding.tools)

    async def servers(self) -> JSONResponse:
        return await self._wrap(self.binding.servers)

    async def domains(self) -> JSONResponse:
        return await self._wrap(self.binding.domains)

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


__all__ = ["McpRouter"]
