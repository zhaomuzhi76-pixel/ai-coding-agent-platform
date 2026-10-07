from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.project_session.project_session_api import (
    ProjectSessionAPI,
)
from backend.api.project_session.project_session_api_router_support import (
    ProjectSessionAPIRouterSupport,
)


class ProjectSessionAPIRouter:
    """
    FastAPI transport adapter for ProjectSessionAPI.

    Owns:
        - HTTP route registration
        - transport invocation

    Does not own:
        - project/session business logic
        - registry state
        - lifecycle state
        - runtime construction
    """

    VERSION = "1.1"
    PREFIX = "/api/project-sessions"

    def __init__(
        self,
        api: ProjectSessionAPI,
        support: ProjectSessionAPIRouterSupport | None = None,
    ) -> None:
        if not isinstance(
            api,
            ProjectSessionAPI,
        ):
            raise TypeError(
                "api must ProjectSessionAPI"
            )

        self.api = api
        self.support = (
            support
            or ProjectSessionAPIRouterSupport()
        )
        self.router = APIRouter()
        self._register()

    def _register(
        self,
    ) -> None:
        self.router.post(
            self.PREFIX
        )(self.create)

        self.router.get(
            f"{self.PREFIX}/active"
        )(self.active)

        self.router.get(
            "/api/projects/{project_id}/sessions"
        )(self.project_sessions)

        self.router.get(
            f"{self.PREFIX}/{{session_id}}"
        )(self.get)

        self.router.post(
            f"{self.PREFIX}/{{session_id}}/start"
        )(self.start)

        self.router.post(
            f"{self.PREFIX}/{{session_id}}/close"
        )(self.close)

        self.router.delete(
            f"{self.PREFIX}/{{session_id}}"
        )(self.remove)

        self.router.post(
            f"{self.PREFIX}/execute"
        )(self.execute)

    async def create(
        self,
        payload: dict[str, object],
    ) -> JSONResponse:
        return await self._call(
            self.api.create,
            payload,
        )

    async def get(
        self,
        session_id: str,
    ) -> JSONResponse:
        return await self._call(
            self.api.get,
            session_id,
        )

    async def start(
        self,
        session_id: str,
    ) -> JSONResponse:
        return await self._call(
            self.api.start,
            session_id,
        )

    async def close(
        self,
        session_id: str,
    ) -> JSONResponse:
        return await self._call(
            self.api.close,
            session_id,
        )

    async def remove(
        self,
        session_id: str,
    ) -> JSONResponse:
        return await self._call(
            self.api.remove,
            session_id,
        )

    async def project_sessions(
        self,
        project_id: str,
    ) -> JSONResponse:
        return await self._call(
            self.api.project_sessions,
            project_id,
        )

    async def active(
        self,
    ) -> JSONResponse:
        return await self._call(
            self.api.active_sessions,
        )

    async def execute(
        self,
        payload: dict[str, object],
    ) -> JSONResponse:
        return await self._call(
            self.api.execute,
            payload,
        )

    async def _call(
        self,
        handler,
        *args: object,
    ) -> JSONResponse:
        try:
            result = handler(
                *args
            )

            if hasattr(
                result,
                "__await__",
            ):
                result = await result

            return self.support.ok(
                result
            )

        except Exception as error:
            return self.support.error(
                error
            )

    def ready(
        self,
    ) -> bool:
        return (
            self.api.ready()
            and self.support.ready()
            and bool(
                self.router.routes
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "route_count": len(
                self.router.routes
            ),
            "ready": self.ready(),
            "api": self.api.dump(),
            "support": self.support.dump(),
        }


__all__ = [
    "ProjectSessionAPIRouter",
]
