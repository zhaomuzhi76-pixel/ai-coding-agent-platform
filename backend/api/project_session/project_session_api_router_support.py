from __future__ import annotations

from fastapi.responses import JSONResponse

from backend.core.result import ResultSerializer


class ProjectSessionAPIRouterSupport:
    """
    FastAPI response/status support.

    Owns:
        - successful result serialization
        - success response creation
        - exception-to-status mapping
        - error response creation

    Does not own:
        - business operations
        - API service delegation
        - result serialization rules
        - route registration
    """

    VERSION = "1.1"

    @staticmethod
    def ok(
        payload: object,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content=ProjectSessionAPIRouterSupport._serialize(
                payload
            ),
        )

    @staticmethod
    def error(
        error: Exception,
    ) -> JSONResponse:
        if isinstance(
            error,
            (TypeError, ValueError),
        ):
            status_code = 400
        elif isinstance(
            error,
            KeyError,
        ):
            status_code = 404
        elif isinstance(
            error,
            RuntimeError,
        ):
            status_code = 503
        else:
            status_code = 500

        return JSONResponse(
            status_code=status_code,
            content={
                "error": str(error),
            },
        )

    @staticmethod
    def _serialize(
        payload: object,
    ) -> dict[str, object]:
        if isinstance(
            payload,
            dict,
        ):
            return payload

        return ResultSerializer.to_dict(
            payload
        )

    def ready(
        self,
    ) -> bool:
        return ResultSerializer.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "serializer": ResultSerializer.dump(),
        }


__all__ = [
    "ProjectSessionAPIRouterSupport",
]
