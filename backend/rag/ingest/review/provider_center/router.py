"""provider_center FastAPI 路由 —— /api/config/provider/{kind}/*。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.provider_center.api import ProviderCenterApi
from backend.rag.ingest.review.provider_center.spec import SUPPORTED_KINDS

ROUTE_PREFIX = "/api/config/provider/{kind}"
KIND_PATTERN = "|".join(SUPPORTED_KINDS)


def build_router(api: ProviderCenterApi | None = None) -> Any:
    try:
        from fastapi import APIRouter, Body, Path  # type: ignore
    except Exception:
        return None
    _api = api or ProviderCenterApi()
    router = APIRouter()

    @router.get(f"{ROUTE_PREFIX}/cards")
    def cards(kind: str = Path(..., pattern=f"^({KIND_PATTERN})$")) -> dict:
        return _api.cards(kind)

    @router.get(f"{ROUTE_PREFIX}/selectable")
    def selectable(kind: str = Path(..., pattern=f"^({KIND_PATTERN})$")) -> dict:
        return _api.selectable(kind)

    @router.get(f"{ROUTE_PREFIX}/yaml")
    def yaml_text(kind: str = Path(..., pattern=f"^({KIND_PATTERN})$")) -> dict:
        return _api.yaml(kind)

    @router.get(f"{ROUTE_PREFIX}/all")
    def list_all(kind: str = Path(..., pattern=f"^({KIND_PATTERN})$")) -> dict:
        return _api.list_all(kind)

    @router.post(f"{ROUTE_PREFIX}/register")
    def register(payload: dict = Body(...)) -> dict:
        return _api.register(payload)

    @router.post(f"{ROUTE_PREFIX}/probe")
    def probe(payload: dict = Body(...)) -> dict:
        return _api.probe(str(payload.get("kind") or ""),
                          str(payload.get("model_id") or ""))

    @router.post(f"{ROUTE_PREFIX}/select")
    def select(payload: dict = Body(...)) -> dict:
        return _api.select(str(payload.get("kind") or ""),
                           str(payload.get("model_id") or ""))

    return router
