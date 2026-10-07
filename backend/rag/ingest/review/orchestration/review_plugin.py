"""L4 审核门插件 —— 挂载到 runtime.plugins，不改现有文件。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.api.review_router_factory import build_review_api
from backend.rag.ingest.review.orchestration.review_plugin_capability import (
    PLUGIN_DESCRIPTOR,
)


class RagReviewPlugin:
    """L23 审核门插件：暴露草稿审核 / 可视化召回 / 审批路由。"""

    descriptor = PLUGIN_DESCRIPTOR

    def __init__(self) -> None:
        self._api: Any | None = None

    @property
    def name(self) -> str:
        return PLUGIN_DESCRIPTOR["name"]

    def capabilities(self) -> tuple[str, ...]:
        return tuple(PLUGIN_DESCRIPTOR["capabilities"])

    def build_api(self, writer: Any | None = None,
                  bm25: Any | None = None,
                  reranker: Any | None = None) -> Any:
        if self._api is None:
            self._api = build_review_api(writer, bm25, reranker)
        return self._api

    def on_load(self, context: dict | None = None) -> None:
        return None

    def on_unload(self) -> None:
        self._api = None


def build_plugin() -> RagReviewPlugin:
    return RagReviewPlugin()
