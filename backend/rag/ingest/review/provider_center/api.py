"""provider_center API —— kind 参数化的统一入口。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.provider_center.catalog import (
    ProviderCatalog,
    get_default_catalog,
)
from backend.rag.ingest.review.provider_center.probe import ProviderProbe
from backend.rag.ingest.review.provider_center.selector import ProviderSelector
from backend.rag.ingest.review.provider_center.spec import ProviderSpec
from backend.rag.ingest.review.provider_center.view import ProviderCenterView


class ProviderCenterApi:
    def __init__(self, catalog: ProviderCatalog | None = None,
                 probe: ProviderProbe | None = None) -> None:
        self._catalog = catalog or get_default_catalog()
        self._probe = probe or ProviderProbe()
        self._view = ProviderCenterView(self._catalog)
        self._selector = ProviderSelector(self._catalog)

    def cards(self, kind: str) -> dict[str, Any]:
        return self._view.build_cards(kind)

    def selectable(self, kind: str) -> dict[str, Any]:
        return self._view.build_selectable(kind)

    def yaml(self, kind: str) -> dict[str, str]:
        return {"yaml": self._view.build_yaml(kind)}

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        spec = ProviderSpec(
            kind=str(payload.get("kind") or ""),
            model_id=str(payload.get("model_id") or ""),
            display_name=str(payload.get("display_name") or ""),
            backend_kind=str(payload.get("backend_kind") or "openai_compatible"),
            endpoint=str(payload.get("endpoint") or ""),
            api_key_env=str(payload.get("api_key_env") or ""),
            model_path=str(payload.get("model_path") or ""),
            weight=float(payload.get("weight") or 1.0),
            description=str(payload.get("description") or ""),
            tags=tuple(payload.get("tags") or ()),
        )
        self._catalog.register(spec)
        return {"model_id": spec.model_id, "kind": spec.kind, "registered": True}

    def probe(self, kind: str, model_id: str) -> dict[str, Any]:
        rec = self._catalog.get(model_id)
        if rec is None or rec.spec.kind != kind:
            return {"model_id": model_id, "kind": kind, "outcome": "not_found"}
        self._catalog.mark_probing(model_id)
        outcome, msg, latency = self._probe.run(rec.spec)
        self._catalog.mark_result(model_id, outcome, msg, latency)
        return {"model_id": model_id, "kind": kind,
                "outcome": outcome.value, "message": msg,
                "latency_ms": latency}

    def select(self, kind: str, model_id: str) -> dict[str, Any]:
        ok = self._selector.select(kind, model_id)
        return {"model_id": model_id, "kind": kind, "selected": ok,
                "current": self._selector.current(kind)}

    def list_all(self, kind: str) -> dict[str, Any]:
        return {"kind": kind,
                "models": list(self._selector.list_all_with_status(kind))}
