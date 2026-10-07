"""PlatformRouter: FastAPI transport adapter for PlatformBinding."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.platform.binding import PlatformBinding


class PlatformRouter:
    """Owns HTTP route registration and error projection.

    不重造 platform 逻辑；只做 transport 层。
    """

    VERSION = "1.0"
    PREFIX = "/api/platform"

    def __init__(self, binding: PlatformBinding) -> None:
        if not isinstance(binding, PlatformBinding):
            raise TypeError("binding must PlatformBinding")
        if not binding.ready():
            raise RuntimeError("platform binding not ready")
        self.binding = binding
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.post(f"{p}/sessions")(self.create_session)
        self.router.get(f"{p}/sessions/{{session_id}}")(self.get_session)
        self.router.post(f"{p}/propose")(self.propose)
        self.router.post(f"{p}/approve")(self.approve)
        self.router.post(f"{p}/reject")(self.reject)
        self.router.post(f"{p}/apply")(self.apply)
        self.router.post(f"{p}/verify")(self.verify)
        self.router.post(f"{p}/learn")(self.learn)
        self.router.get(f"{p}/proposals")(self.list_proposals)
        self.router.delete(f"{p}/proposals/{{proposal_id}}")(self.delete_proposal)
        self.router.get(f"{p}/models")(self.list_models)
        self.router.get(f"{p}/domains")(self.list_domains)
        self.router.get(f"{p}/routing")(self.get_routing)
        self.router.put(f"{p}/routing")(self.put_routing)
        self.router.post(f"{p}/routing/reset")(self.reset_routing)

    # ─── handlers ───────────────────────────────────────────
    async def create_session(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._call(self.binding.create_session, payload)

    async def get_session(self, session_id: str) -> JSONResponse:
        return await self._call(self.binding.get_session, session_id)

    async def propose(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._call(self.binding.propose, payload)

    async def approve(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._call(self.binding.approve, payload)

    async def reject(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._call(self.binding.reject, payload)

    async def apply(
        self, payload: Dict[str, Any], wait: bool = True,
    ) -> JSONResponse:
        if hasattr(self.binding, "apply_adapter"):
            return await self._call(
                lambda: self.binding.apply_adapter(payload, wait=wait))
        return await self._call(self.binding.apply, payload)

    async def verify(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._call(self.binding.verify, payload)

    async def learn(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._call(self.binding.learn, payload)

    async def list_proposals(self) -> JSONResponse:
        return await self._call(self.binding.list_proposals, {})

    async def delete_proposal(self, proposal_id: str) -> JSONResponse:
        return await self._call(
            self.binding.delete_proposal, proposal_id)

    async def list_models(self) -> JSONResponse:
        return await self._call(self.binding.list_models)

    async def list_domains(self) -> JSONResponse:
        return await self._call(self.binding.list_domains)

    async def get_routing(self, user_id: str = "default") -> JSONResponse:
        return await self._call(
            lambda: self.binding.get_routing(user_id)
        )

    async def put_routing(
        self, payload: Dict[str, Any],
    ) -> JSONResponse:
        uid = str(payload.pop("user_id", "default") or "default")
        return await self._call(
            lambda: self.binding.set_routing(uid, payload)
        )

    async def reset_routing(
        self, user_id: str = "default",
    ) -> JSONResponse:
        return await self._call(
            lambda: self.binding.reset_routing(user_id)
        )

    # ─── error projection ───────────────────────────────────
    async def _call(self, fn, *args) -> JSONResponse:
        try:
            result = fn(*args)
            if hasattr(result, "__await__"):
                result = await result
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": result},
            )
        except KeyError as exc:
            return self._error(404, "NOT_FOUND", str(exc))
        except PermissionError as exc:
            return self._error(403, "FORBIDDEN", str(exc))
        except (ValueError, TypeError) as exc:
            return self._error(400, "BAD_REQUEST", str(exc))
        except Exception as exc:
            return self._error(
                500, "INTERNAL", f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _error(status: int, code: str, msg: str) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            content={
                "ok": False,
                "error": {"code": code, "message": msg},
            },
        )

    def ready(self) -> bool:
        return self.binding.ready()

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }


__all__ = ["PlatformRouter"]
