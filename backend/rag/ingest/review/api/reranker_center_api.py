"""L4 配置中心 HTTP 路由 —— /api/config/reranker 命名空间。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.api.reranker_router import RerankerApi
from backend.rag.ingest.review.review.reranker_center_view import (
    RerankerCenterView,
)
from backend.rag.ingest.review.storage.reranker_catalog import (
    get_default_catalog,
)

ROUTE_PREFIX = "/api/config/reranker"

ROUTES: tuple[tuple[str, str, str], ...] = (
    ("GET",  f"{ROUTE_PREFIX}/cards",      "配置中心卡片视图"),
    ("GET",  f"{ROUTE_PREFIX}/selectable", "前端下拉（只含通过项）"),
    ("GET",  f"{ROUTE_PREFIX}/yaml",       "查看 YAML"),
    ("POST", f"{ROUTE_PREFIX}/probe",      "链路测试"),
    ("POST", f"{ROUTE_PREFIX}/select",     "选择排序模型"),
    ("POST", f"{ROUTE_PREFIX}/register",   "注册新模型"),
)


def _build_default_api() -> RerankerApi:
    """构造带内置 probe 的 RerankerApi —— api 层可向下 import review 层。"""
    from backend.rag.ingest.review.review.reranker_adapter import build_reranker
    from backend.rag.ingest.review.review.reranker_probe import RerankerProbe

    catalog = get_default_catalog()
    probe = RerankerProbe(lambda _spec: build_reranker())
    return RerankerApi(catalog, probe)


def build_router(api: RerankerApi | None = None,
                 view: RerankerCenterView | None = None) -> Any:
    """返回 FastAPI APIRouter；未安装 FastAPI 时返回 None。"""
    try:
        from fastapi import APIRouter, Body  # type: ignore
    except Exception:
        return None
    _api = api if api is not None else _build_default_api()
    _view = view if view is not None else RerankerCenterView(_api._catalog)
    router = APIRouter()

    @router.get(f"{ROUTE_PREFIX}/cards")
    def cards() -> dict:
        return _view.build_cards()

    @router.get(f"{ROUTE_PREFIX}/selectable")
    def selectable() -> dict:
        return _view.build_selectable()

    @router.get(f"{ROUTE_PREFIX}/yaml")
    def yaml_text() -> dict:
        return {"yaml": _view.build_yaml()}

    @router.post(f"{ROUTE_PREFIX}/probe")
    def probe(payload: dict = Body(...)) -> dict:
        return _api.probe(str(payload.get("model_id") or ""))

    @router.post(f"{ROUTE_PREFIX}/select")
    def select(payload: dict = Body(...)) -> dict:
        return _api.select(str(payload.get("model_id") or ""))

    @router.post(f"{ROUTE_PREFIX}/register")
    def register(payload: dict = Body(...)) -> dict:
        from backend.rag.ingest.review.foundation.reranker_model_spec import (
            RerankerModelSpec,
        )
        return _api.register(RerankerModelSpec(
            model_id=str(payload.get("model_id") or ""),
            display_name=str(payload.get("display_name") or ""),
            backend_kind=str(payload.get("backend_kind") or "openai_compatible"),
            endpoint=str(payload.get("endpoint") or ""),
            model_path=str(payload.get("model_path") or ""),
            weight=float(payload.get("weight") or 1.0),
            description=str(payload.get("description") or ""),
            tags=tuple(payload.get("tags") or ()),
        ))

    return router
