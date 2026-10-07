"""L3 排序模型选择器 —— 前端下拉列表的唯一数据源。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.foundation.reranker_model_spec import (
    RerankerModelSpec,
)
from backend.rag.ingest.review.storage.reranker_catalog import RerankerCatalog


class RerankerSelector:
    """只暴露链路测试通过（passing）的模型。"""

    def __init__(self, catalog: RerankerCatalog) -> None:
        self._catalog = catalog

    def list_passing(self) -> tuple[RerankerModelSpec, ...]:
        return self._catalog.selectable_specs()

    def list_all_with_status(self) -> tuple[dict[str, Any], ...]:
        out = []
        for rec in self._catalog.all_records():
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

    def current(self) -> str:
        selected = self._catalog.get_selected()
        if selected:
            return selected
        passing = self.list_passing()
        return passing[0].model_id if passing else ""

    def select(self, model_id: str) -> bool:
        return self._catalog.set_selected(model_id)
