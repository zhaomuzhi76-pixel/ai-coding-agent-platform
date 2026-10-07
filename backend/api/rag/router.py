"""RagRouter: FastAPI transport for RAG."""
from __future__ import annotations

from typing import Any, Callable, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.rag.binding import RagBinding


class RagRouter:
    VERSION = "1.0"
    PREFIX = "/api/rag"

    def __init__(self, binding: RagBinding) -> None:
        if not isinstance(binding, RagBinding):
            raise TypeError("binding must RagBinding")
        self.binding = binding
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.get(f"{p}/status")(self.status)
        self.router.get(f"{p}/count")(self.count)
        self.router.post(f"{p}/index/dataset")(self.index_dataset)
        self.router.post(f"{p}/index/texts")(self.index_texts)
        self.router.post(f"{p}/query")(self.query)
        self.router.post(f"{p}/clear")(self.clear)
        self.router.get(f"{p}/finetune-datasets")(self.list_finetune_datasets)
        self.router.post(f"{p}/index/all-finetune-datasets")(
            self.index_all_finetune_datasets
        )

    async def status(self) -> JSONResponse:
        return await self._wrap(lambda: self.binding.status())

    async def count(self) -> JSONResponse:
        return await self._wrap(lambda: self.binding.count())

    async def index_dataset(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.index_dataset(payload)
        )

    async def index_texts(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.index_texts(payload)
        )

    async def query(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap(lambda: self.binding.query(payload))

    async def clear(self) -> JSONResponse:
        return await self._wrap(lambda: self.binding.clear())

    async def list_finetune_datasets(self) -> JSONResponse:
        return await self._wrap(self.binding.list_finetune_datasets)

    async def index_all_finetune_datasets(self) -> JSONResponse:
        return await self._wrap(self.binding.index_all_finetune_datasets)

    async def _wrap(self, fn) -> JSONResponse:
        try:
            import asyncio
            r = fn()
            if asyncio.iscoroutine(r):
                r = await r
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": r},
            )
        except ValueError as exc:
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

    async def _wrap_async(self, fn) -> JSONResponse:
        return await self._wrap(fn)



    def ready(self) -> bool:
        return self.binding.ready()

    def dump(self) -> Dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION}


__all__ = ["RagRouter"]
