"""provider_center 选择器 —— 按 kind 过滤可选模型。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.provider_center.catalog import ProviderCatalog
from backend.rag.ingest.review.provider_center.spec import (
    KIND_EMBEDDING,
    KIND_LLM,
    KIND_RERANKER,
    ProviderSpec,
)


class ProviderSelector:
    def __init__(self, catalog: ProviderCatalog) -> None:
        self._catalog = catalog

    def list_passing(self, kind: str) -> tuple[ProviderSpec, ...]:
        return tuple(r.spec for r in self._catalog.selectable(kind))

    def list_all_with_status(self, kind: str) -> tuple[dict[str, Any], ...]:
        out = []
        for rec in self._catalog.by_kind(kind):
            out.append({
                "spec": rec.spec.to_dict(),
                "status": rec.status.value,
                "selectable": rec.status.selectable,
                "last_outcome": rec.last_outcome.value if rec.last_outcome else None,
                "last_message": rec.last_message,
                "last_probe_at": rec.last_probe_at,
                "last_latency_ms": rec.last_latency_ms,
            })
        return tuple(out)

    def current(self, kind: str) -> str:
        sel = self._catalog.get_selected(kind)
        if sel:
            return sel
        passing = self.list_passing(kind)
        return passing[0].model_id if passing else ""

    def select(self, kind: str, model_id: str) -> bool:
        return self._catalog.set_selected(kind, model_id)


__all__ = [
    "ProviderSelector", "KIND_LLM", "KIND_EMBEDDING", "KIND_RERANKER",
]
