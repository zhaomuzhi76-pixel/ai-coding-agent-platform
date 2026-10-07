"""L4 配置中心 Reranker 插件 —— 命名空间隔离。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.api.reranker_center_api import (
    ROUTE_PREFIX,
    ROUTES,
    build_router,
)
from backend.rag.ingest.review.review.reranker_center_view import (
    RerankerCenterView,
)
from backend.rag.ingest.review.storage.reranker_catalog import (
    get_default_catalog,
)


class RerankerCenterPlugin:
    descriptor = {
        "name": "reranker_center",
        "version": "1.0.0",
        "description": "配置中心 Reranker 卡片 + 链路测试门 + 前端下拉",
        "prefix": ROUTE_PREFIX,
        "routes": ROUTES,
    }

    @property
    def name(self) -> str:
        return self.descriptor["name"]

    def routes(self) -> tuple[tuple[str, str, str], ...]:
        return tuple(self.descriptor["routes"])

    def build_router(self) -> Any:
        return build_router()

    def build_view(self) -> RerankerCenterView:
        return RerankerCenterView(get_default_catalog())

    def on_load(self, context: dict | None = None) -> None:
        return None

    def on_unload(self) -> None:
        return None


def build_plugin() -> RerankerCenterPlugin:
    return RerankerCenterPlugin()
