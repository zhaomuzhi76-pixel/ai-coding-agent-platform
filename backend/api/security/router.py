"""SecurityRouter: FastAPI transport for security data."""
from __future__ import annotations

from typing import Any, Callable, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.security.binding import SecurityBinding


class SecurityRouter:
    VERSION = "1.0"
    PREFIX = "/api/security"

    def __init__(self, binding: SecurityBinding) -> None:
        if not isinstance(binding, SecurityBinding):
            raise TypeError("binding must SecurityBinding")
        self.binding = binding
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.get(f"{p}/summary")(self.summary)
        self.router.get(f"{p}/roles")(self.roles)
        self.router.get(f"{p}/roles/{{name}}")(self.role)
        self.router.post(f"{p}/check")(self.check)

    async def summary(self) -> JSONResponse:
        return await self._wrap(self.binding.summary)

    async def roles(self) -> JSONResponse:
        return await self._wrap(self.binding.roles)

    async def role(self, name: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.role(name))

    async def check(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap(lambda: self.binding.check(payload))

    async def _wrap(
        self, fn: Callable[[], Any],
    ) -> JSONResponse:
        try:
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": fn()},
            )
        except KeyError as exc:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": {
                    "code": "NOT_FOUND", "message": str(exc)}},
            )
        except (ValueError, TypeError) as exc:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": {
                    "code": "BAD_REQUEST", "message": str(exc)}},
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


__all__ = ["SecurityRouter"]
