"""选择回退解析。职责：把会话绑定中"未选"的字段回退到 catalog 默认。
不校验合法性（L2 selection_binder 做），不存储（L1 SessionBindingStore 做）。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from backend.providers.selection.contracts import ModelKind, SelectionBinding
from backend.providers.selection.model_catalog import ModelCatalog

@dataclass(frozen=True)
class ResolvedDefaults:
    llm_id: Optional[str]
    image_gen_id: Optional[str]
    notes: tuple[str, ...]

def _first_llm_id(catalog: ModelCatalog) -> Optional[str]:
    for d in catalog.list_by_kind(ModelKind.LLM):
        return d.id
    return None

def _first_image_gen_id(catalog: ModelCatalog) -> Optional[str]:
    for d in catalog.list_by_kind(ModelKind.IMAGE_GEN):
        return d.id
    return None

def resolve_defaults(binding: SelectionBinding, catalog: ModelCatalog) -> ResolvedDefaults:
    notes = []
    llm_id = binding.llm_id
    if llm_id is None:
        llm_id = _first_llm_id(catalog)
        if llm_id is not None:
            notes.append(f"llm 回退到 {llm_id}")
    image_gen_id = binding.image_gen_id
    if image_gen_id is None:
        image_gen_id = _first_image_gen_id(catalog)
        if image_gen_id is not None:
            notes.append(f"image_gen 回退到 {image_gen_id}")
    return ResolvedDefaults(llm_id=llm_id, image_gen_id=image_gen_id, notes=tuple(notes))

def apply_defaults(binding: SelectionBinding, catalog: ModelCatalog) -> SelectionBinding:
    d = resolve_defaults(binding, catalog)
    out = binding
    if out.llm_id is None and d.llm_id is not None:
        out = out.with_llm(d.llm_id)
    if out.image_gen_id is None and d.image_gen_id is not None:
        out = out.with_image_gen(d.image_gen_id)
    return out
