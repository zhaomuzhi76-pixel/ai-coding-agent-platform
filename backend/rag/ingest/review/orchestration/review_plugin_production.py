"""L4 生产插件 —— 挂载生产装配，不改已封顶的 review_plugin.py。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.api.review_factory_production import (
    backends,
    build_production_api,
)
from backend.rag.ingest.review.orchestration.review_plugin_capability import (
    PLUGIN_DESCRIPTOR,
)


class RagReviewPluginProduction:
    """生产版插件：真实后端 + 优雅回落。"""

    descriptor = PLUGIN_DESCRIPTOR

    def __init__(self) -> None:
        self._api: Any | None = None

    @property
    def name(self) -> str:
        return PLUGIN_DESCRIPTOR["name"]

    def capabilities(self) -> tuple[str, ...]:
        return tuple(PLUGIN_DESCRIPTOR["capabilities"])

    def build_api(self) -> Any:
        if self._api is None:
            self._api = build_production_api()
        return self._api

    def backend_report(self) -> dict[str, str]:
        return backends()

    def on_load(self, context: dict | None = None) -> None:
        return None

    def on_unload(self) -> None:
        self._api = None


def build_plugin() -> RagReviewPluginProduction:
    return RagReviewPluginProduction()
