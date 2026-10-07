"""会话选择解析。职责：读取绑定 + 校验 ID 在 catalog 中是否存在。
不做回退填充（回退在 L3 application.chatbot.selection_resolver）。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
from backend.providers.selection.contracts import SelectionBinding
from backend.providers.selection.session_binding import SessionBindingStore
from backend.providers.selection.model_catalog import ModelCatalog

@dataclass(frozen=True)
class BindingResolution:
    binding: SelectionBinding
    llm_valid: bool
    image_gen_valid: bool
    messages: Tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.llm_valid and self.image_gen_valid

def _llm_exists(catalog: ModelCatalog, llm_id: Optional[str]) -> bool:
    if llm_id is None:
        return True
    return any(d.id == llm_id for d in catalog.all())

def resolve_binding(store: SessionBindingStore, session_id: str,
                    catalog: ModelCatalog) -> BindingResolution:
    b = store.get(session_id)
    msgs = []
    llm_ok = _llm_exists(catalog, b.llm_id)
    if not llm_ok:
        msgs.append(f"llm_id={b.llm_id} 不在 catalog")
    ig_ok = _llm_exists(catalog, b.image_gen_id)
    if not ig_ok:
        msgs.append(f"image_gen_id={b.image_gen_id} 不在 catalog")
    return BindingResolution(binding=b, llm_valid=llm_ok, image_gen_valid=ig_ok,
                             messages=tuple(msgs))
