from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.api.submission_route import (
    APISubmissionRoute,
)
from backend.core.result import (
    ResultSerializer,
)


class SubmissionAPIRouter:
    """
    FastAPI submission transport adapter.

    Owns:
        - FastAPI route registration
        - transport response serialization
        - transport-level error response

    Does not own:
        - submission logic
        - application capability resolution
        - execution
        - submission lifecycle
        - queue
        - scheduler
        - dispatch
        - retry
        - budget
        - rate limiting
    """

    VERSION = "1.0"
    PATH = "/api/submission"

    def __init__(
        self,
        route: APISubmissionRoute,
    ) -> None:
        if route is None:
            raise ValueError(
                "submission route required"
            )

        self.route = route
        self.router = APIRouter()
        self._register()

    def _register(
        self,
    ) -> None:
        self.router.add_api_route(
            self.PATH,
            self.execute,
            methods=["POST"],
        )

    async def execute(
        self,
        request: Request,
    ) -> JSONResponse:
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid JSON payload",
                },
            )

        if not isinstance(
            payload,
            dict,
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "payload must be object",
                },
            )

        session_id = payload.get(
            "session_id"
        )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "error": "session id required",
                },
            )

        transport_payload = dict(
            payload
        )
        transport_payload.pop(
            "session_id",
            None,
        )

        if not self.ready():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "submission route unavailable",
                },
            )

        try:
            result = await self.route.execute(
                transport_payload,
                session_id,
            )

            return JSONResponse(
                status_code=200,
                content=ResultSerializer.to_dict(
                    result
                ),
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            return JSONResponse(
                status_code=400,
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

    def ready(
        self,
    ) -> bool:
        return (
            self.route.ready()
            and ResultSerializer.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "path": self.PATH,
            "ready": self.ready(),
            "route": self.route.dump(),
        }


__all__ = [
    "SubmissionAPIRouter",
]
