"""L3 配置中心视图构建 —— catalog → 卡片 / 下拉 / YAML。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.foundation.reranker_center_contract import (
    RerankerCardEntry,
    RerankerModelEntry,
    color_of,
    label_of,
)
from backend.rag.ingest.review.storage.reranker_catalog import (
    ModelRecord,
    RerankerCatalog,
)


class RerankerCenterView:
    """把 RerankerCatalog 转换成配置中心可渲染的卡片/下拉/YAML。"""

    def __init__(self, catalog: RerankerCatalog) -> None:
        self._catalog = catalog

    def build_cards(self) -> dict[str, Any]:
        selected = self._catalog.get_selected()
        cards = [self._card(rec, selected)
                 for rec in self._catalog.all_records()]
        passing = sum(1 for c in cards if c["selectable"])
        return {
            "count": len(cards),
            "passing": passing,
            "selected": selected,
            "cards": cards,
        }

    def build_selectable(self) -> dict[str, Any]:
        """前端下拉列表数据源 —— 只含 passing。"""
        selected = self._catalog.get_selected()
        options = []
        for rec in self._catalog.selectable_records():
            options.append({
                "value": rec.spec.model_id,
                "label": rec.spec.display_name,
                "selected": rec.spec.model_id == selected,
            })
        if not selected and options:
            selected = options[0]["value"]
        return {"current": selected, "options": options}

    def build_yaml(self) -> str:
        try:
            import yaml  # type: ignore
        except Exception:
            return self._fallback_yaml()
        return yaml.safe_dump(self._yaml_dict(),
                              allow_unicode=True, sort_keys=False)

    def _card(self, rec: ModelRecord, selected: str) -> dict[str, Any]:
        spec = rec.spec
        entry = RerankerModelEntry(
            model_id=spec.model_id,
            display_name=spec.display_name,
            backend_kind=spec.backend_kind,
            endpoint=spec.endpoint,
            description=spec.description,
            weight=spec.weight,
            tags=tuple(spec.tags),
        )
        card = RerankerCardEntry(
            entry=entry,
            status=rec.status.value,
            selectable=rec.status.selectable,
            selected=(spec.model_id == selected),
            status_label=label_of(rec.status.value),
            status_color=color_of(rec.status.value),
            last_probe_at=rec.last_probe_at,
            last_outcome=rec.last_outcome.value if rec.last_outcome else "",
            last_message=rec.last_message,
            last_latency_ms=rec.last_latency_ms,
        )
        return card.to_dict()

    def _yaml_dict(self) -> dict[str, Any]:
        models = []
        for rec in self._catalog.all_records():
            spec = rec.spec
            models.append({
                "model_id": spec.model_id,
                "display_name": spec.display_name,
                "backend_kind": spec.backend_kind,
                "endpoint": spec.endpoint,
                "model_path": spec.model_path,
                "weight": spec.weight,
                "status": rec.status.value,
                "selectable": rec.status.selectable,
                "last_probe_at": rec.last_probe_at,
                "last_outcome": rec.last_outcome.value
                if rec.last_outcome else "",
            })
        return {"reranker": {
            "selected": self._catalog.get_selected(),
            "models": models,
        }}

    def _fallback_yaml(self) -> str:
        lines = ["reranker:"]
        lines.append(f"  selected: {self._catalog.get_selected() or ''}")
        lines.append("  models:")
        for rec in self._catalog.all_records():
            lines.append(f"    - model_id: {rec.spec.model_id}")
            lines.append(f"      display_name: {rec.spec.display_name}")
            lines.append(f"      status: {rec.status.value}")
            lines.append(
                f"      selectable: {str(rec.status.selectable).lower()}"
            )
        return "\n".join(lines) + "\n"
