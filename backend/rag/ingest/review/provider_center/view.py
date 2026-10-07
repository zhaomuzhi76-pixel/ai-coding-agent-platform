"""provider_center 视图 —— 卡片/下拉/YAML 三合一（按 kind）。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.foundation.reranker_center_contract import (
    color_of,
    label_of,
)
from backend.rag.ingest.review.provider_center.catalog import (
    ProviderCatalog,
    ProviderRecord,
)


class ProviderCenterView:
    def __init__(self, catalog: ProviderCatalog) -> None:
        self._catalog = catalog

    def build_cards(self, kind: str) -> dict[str, Any]:
        selected = self._catalog.get_selected(kind)
        cards = [self._card(rec, selected)
                 for rec in self._catalog.by_kind(kind)]
        return {
            "kind": kind,
            "count": len(cards),
            "passing": sum(1 for c in cards if c["selectable"]),
            "selected": selected,
            "cards": cards,
        }

    def build_selectable(self, kind: str) -> dict[str, Any]:
        selected = self._catalog.get_selected(kind)
        options = [{
            "value": rec.spec.model_id,
            "label": rec.spec.display_name,
            "selected": rec.spec.model_id == selected,
        } for rec in self._catalog.selectable(kind)]
        if not selected and options:
            selected = options[0]["value"]
        return {"kind": kind, "current": selected, "options": options}

    def build_yaml(self, kind: str) -> str:
        try:
            import yaml  # type: ignore
            return yaml.safe_dump(self._yaml_dict(kind),
                                  allow_unicode=True, sort_keys=False)
        except Exception:
            return self._fallback_yaml(kind)

    def _card(self, rec: ProviderRecord, selected: str) -> dict[str, Any]:
        spec = rec.spec
        return {
            **spec.to_dict(),
            "status": rec.status.value,
            "status_label": label_of(rec.status.value),
            "status_color": color_of(rec.status.value),
            "selectable": rec.status.selectable,
            "selected": spec.model_id == selected,
            "last_probe_at": rec.last_probe_at,
            "last_outcome": rec.last_outcome.value if rec.last_outcome else "",
            "last_message": rec.last_message,
            "last_latency_ms": rec.last_latency_ms,
        }

    def _yaml_dict(self, kind: str) -> dict[str, Any]:
        models = []
        for rec in self._catalog.by_kind(kind):
            s = rec.spec
            models.append({
                "model_id": s.model_id, "display_name": s.display_name,
                "backend_kind": s.backend_kind, "endpoint": s.endpoint,
                "api_key_env": s.api_key_env, "weight": s.weight,
                "status": rec.status.value,
                "selectable": rec.status.selectable,
            })
        return {kind: {
            "selected": self._catalog.get_selected(kind),
            "models": models,
        }}

    def _fallback_yaml(self, kind: str) -> str:
        lines = [f"{kind}:"]
        lines.append(f"  selected: {self._catalog.get_selected(kind) or ''}")
        lines.append("  models:")
        for rec in self._catalog.by_kind(kind):
            lines.append(f"    - model_id: {rec.spec.model_id}")
            lines.append(f"      status: {rec.status.value}")
        return "\n".join(lines) + "\n"
