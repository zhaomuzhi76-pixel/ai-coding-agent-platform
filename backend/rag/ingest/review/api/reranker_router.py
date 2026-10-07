"""L4 排序模型 API —— 前端下拉/测试/选择的唯一入口。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.foundation.reranker_model_spec import (
    RerankerModelSpec,
)
from backend.rag.ingest.review.review.reranker_probe import RerankerProbe
from backend.rag.ingest.review.review.reranker_selector import RerankerSelector
from backend.rag.ingest.review.storage.reranker_catalog import (
    RerankerCatalog,
    get_default_catalog,
)


class RerankerApi:
    def __init__(self, catalog: RerankerCatalog | None = None,
                 probe: RerankerProbe | None = None) -> None:
        self._catalog = catalog or get_default_catalog()
        self._probe = probe
        self._selector = RerankerSelector(self._catalog)

    def list_available(self) -> dict[str, Any]:
        return {
            "current": self._selector.current(),
            "selectable": [s.to_dict() for s in self._selector.list_passing()],
        }

    def list_all(self) -> dict[str, Any]:
        return {"models": list(self._selector.list_all_with_status())}

    def register(self, spec: RerankerModelSpec) -> dict[str, Any]:
        self._catalog.register(spec)
        return {"model_id": spec.model_id, "registered": True}

    def probe(self, model_id: str) -> dict[str, Any]:
        if self._probe is None:
            return {"model_id": model_id, "outcome": "no_probe",
                    "message": "probe not configured"}
        rec = self._catalog.get(model_id)
        if rec is None:
            return {"model_id": model_id, "outcome": "not_found"}
        self._catalog.mark_probing(model_id)
        outcome, msg, latency = self._probe.run(rec.spec)
        self._catalog.mark_result(model_id, outcome, msg, latency)
        return {"model_id": model_id, "outcome": outcome.value,
                "message": msg, "latency_ms": latency}

    def select(self, model_id: str) -> dict[str, Any]:
        ok = self._selector.select(model_id)
        return {"model_id": model_id, "selected": ok,
                "current": self._selector.current()}
