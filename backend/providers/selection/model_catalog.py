"""选择目录：把原始注册记录规范化为 ModelDescriptor，供前端下拉与门控使用。
职责：只构建与筛选描述符，不持有全局状态、不做回退、不做路由。"""
from __future__ import annotations
from typing import Any, Iterable, Mapping
from backend.providers.selection.contracts import ModelDescriptor, ModelKind, Modality

def _mods(raw: Iterable[str]) -> frozenset[Modality]:
    return frozenset(Modality(m) for m in raw)

def build_descriptor(raw: Mapping[str, Any]) -> ModelDescriptor:
    return ModelDescriptor(
        id=raw["id"], provider=raw["provider"],
        kind=ModelKind(raw["kind"]),
        input_modalities=_mods(raw.get("input_modalities", ["text"])),
        output_modalities=_mods(raw.get("output_modalities", ["text"])),
        display=raw.get("display", ""), meta=raw.get("meta", {}),
    )

class ModelCatalog:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], ModelDescriptor] = {}
    def register(self, raw: Mapping[str, Any]) -> ModelDescriptor:
        d = build_descriptor(raw); self._items[(d.id, d.provider)] = d; return d
    def register_many(self, raws: Iterable[Mapping[str, Any]]) -> None:
        for r in raws: self.register(r)
    def list_by_kind(self, kind: ModelKind) -> list[ModelDescriptor]:
        return [d for d in self._items.values() if d.kind == kind]
    def get(self, model_id: str, provider: str) -> ModelDescriptor | None:
        return self._items.get((model_id, provider))
    def all(self) -> list[ModelDescriptor]:
        return list(self._items.values())
