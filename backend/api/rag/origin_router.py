"""原件下载 API。职责：按 hash 返回原文件。
不落盘、不解析、不做权限。端点：GET /api/rag/origin/{hash}。
"""
from __future__ import annotations
from typing import Any, Callable

PREFIX = "/api/rag/origin"


def register_origin_routes(router: Any) -> None:
    try:
        from fastapi import APIRouter  # noqa: F401
        from fastapi.responses import FileResponse
    except ImportError as e:
        raise RuntimeError("fastapi 未安装") from e

    @router.get(f"{PREFIX}/{{origin_hash}}")
    async def _download(origin_hash: str):
        from backend.storage.origin_store import get_default_origin_store
        store = get_default_origin_store()
        p = store.get_path(origin_hash)
        if p is None:
            return {"ok": False, "error": {
                "code": "NotFound",
                "message": f"origin not found: {origin_hash}"}}
        return FileResponse(p)

    @router.get(f"{PREFIX}/{{origin_hash}}/info")
    async def _info(origin_hash: str):
        from backend.storage.origin_store import get_default_origin_store
        store = get_default_origin_store()
        p = store.get_path(origin_hash)
        if p is None:
            return {"ok": False, "error": {
                "code": "NotFound",
                "message": f"origin not found: {origin_hash}"}}
        import os
        return {"ok": True, "data": {
            "hash": origin_hash, "path": p,
            "size": os.path.getsize(p),
            "filename": os.path.basename(p)}}


__all__ = ["register_origin_routes", "PREFIX"]
