from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.code_intelligence.api import CodeIntelligenceAPI
from backend.core.code_intelligence.contracts import CodeIntelligenceRequest
from backend.core.result import ResultSerializer


class CodeIntelligenceRouter:
    VERSION = "1.0"
    PATH = "/api/code-intelligence/inspect"

    def __init__(
        self,
        api: CodeIntelligenceAPI,
    ) -> None:
        if not isinstance(
            api,
            CodeIntelligenceAPI,
        ):
            raise TypeError(
                "api must CodeIntelligenceAPI"
            )
        if not api.ready():
            raise RuntimeError(
                "code intelligence api not ready"
            )

        self.api = api
        self.router = APIRouter()
        self.router.post(self.PATH)(self.inspect)

    async def inspect(
        self,
        payload: dict[str, object],
    ) -> JSONResponse:
        try:
            result = await self.api.inspect(
                self._request(payload)
            )
            return JSONResponse(
                status_code=200,
                content=ResultSerializer.to_dict(result),
            )
        except (TypeError, ValueError) as error:
            return JSONResponse(
                status_code=400,
                content={"error": str(error)},
            )
        except FileNotFoundError as error:
            return JSONResponse(
                status_code=404,
                content={"error": str(error)},
            )
        except RuntimeError as error:
            return JSONResponse(
                status_code=503,
                content={"error": str(error)},
            )
        except Exception as error:
            return JSONResponse(
                status_code=500,
                content={"error": str(error)},
            )

    @staticmethod
    def _request(
        payload: object,
    ) -> CodeIntelligenceRequest:
        if not isinstance(payload, dict):
            raise TypeError(
                "code intelligence payload must dict"
            )

        query = payload.get("query")
        workspace = payload.get("workspace", ".")
        path = payload.get("path")
        metadata = payload.get("metadata", {})

        if not isinstance(query, str):
            raise TypeError("query must str")
        if not isinstance(workspace, str):
            raise TypeError("workspace must str")
        if path is not None and not isinstance(path, str):
            raise TypeError("path must str or None")
        if not isinstance(metadata, dict):
            raise TypeError("metadata must dict")

        return CodeIntelligenceRequest(
            query=query,
            workspace=workspace,
            path=path,
            metadata=metadata,
        )

    def ready(self) -> bool:
        return (
            self.api.ready()
            and bool(self.router.routes)
            and ResultSerializer.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "path": self.PATH,
            "ready": self.ready(),
            "route_count": len(self.router.routes),
            "api": self.api.dump(),
        }


__all__ = ["CodeIntelligenceRouter"]
