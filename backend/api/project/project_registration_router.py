from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.project.project_registration_api import (
    ProjectRegistrationAPI,
)


class ProjectRegistrationRouter:
    """
    FastAPI transport adapter for project registration API.

    Owns:
        - HTTP route registration
        - transport invocation
        - transport-level error projection

    Does not own:
        - project construction
        - project registry storage
        - project business rules
        - workspace construction
        - project-session logic
    """

    VERSION = "1.0"
    PREFIX = "/api/projects"

    def __init__(
        self,
        api: ProjectRegistrationAPI,
    ) -> None:
        if not isinstance(
            api,
            ProjectRegistrationAPI,
        ):
            raise TypeError(
                "api must ProjectRegistrationAPI"
            )

        if not api.ready():
            raise RuntimeError(
                "project registration api not ready"
            )

        self.api = api
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        self.router.post(
            self.PREFIX
        )(self.register)

        self.router.get(
            f"{self.PREFIX}/{{project_id}}"
        )(self.get)

        self.router.delete(
            f"{self.PREFIX}/{{project_id}}"
        )(self.remove)

    async def register(
        self,
        payload: dict[str, object],
    ) -> JSONResponse:
        return await self._call(
            self.api.register,
            payload,
        )

    async def get(
        self,
        project_id: str,
    ) -> JSONResponse:
        return await self._call(
            self.api.get,
            project_id,
        )

    async def remove(
        self,
        project_id: str,
    ) -> JSONResponse:
        return await self._call(
            self.api.remove,
            project_id,
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

            return JSONResponse(
                status_code=200,
                content=self._dump(result),
            )

        except (TypeError, ValueError) as error:
            return JSONResponse(
                status_code=400,
                content={
                    "error": str(error),
                },
            )

        except KeyError as error:
            return JSONResponse(
                status_code=404,
                content={
                    "error": str(error),
                },
            )

        except RuntimeError as error:
            return JSONResponse(
                status_code=503,
                content={
                    "error": str(error),
                },
            )

        except Exception as error:
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(error),
                },
            )

    @staticmethod
    def _dump(
        value: object,
    ) -> dict[str, object]:
        dump = getattr(
            value,
            "dump",
            None,
        )

        if not callable(dump):
            raise TypeError(
                "project result must expose dump()"
            )

        result = dump()

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                "project dump must dict"
            )

        return dict(result)

    def ready(self) -> bool:
        return (
            self.api.ready()
            and bool(
                self.router.routes
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "route_count": len(
                self.router.routes
            ),
            "ready": self.ready(),
            "api": self.api.dump(),
        }


__all__ = [
    "ProjectRegistrationRouter",
]
