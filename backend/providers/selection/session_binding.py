"""会话级选择绑定存储。只存/取/更新，不做回退策略（回退在 application 层）。"""
from __future__ import annotations
from typing import Optional
from backend.providers.selection.contracts import SelectionBinding

class SessionBindingStore:
    def __init__(self) -> None:
        self._b: dict[str, SelectionBinding] = {}
    def get(self, session_id: str) -> SelectionBinding:
        return self._b.get(session_id, SelectionBinding())
    def set(self, session_id: str, binding: SelectionBinding) -> None:
        self._b[session_id] = binding
    def update_llm(self, session_id: str, llm_id: str) -> SelectionBinding:
        b = self.get(session_id).with_llm(llm_id); self.set(session_id, b); return b
    def update_image_gen(self, session_id: str, image_gen_id: Optional[str]) -> SelectionBinding:
        b = self.get(session_id).with_image_gen(image_gen_id); self.set(session_id, b); return b
    def update_embedding(self, session_id: str, embedding_id: str) -> SelectionBinding:
        b = self.get(session_id).with_embedding(embedding_id); self.set(session_id, b); return b
    def update_rerank(self, session_id: str, rerank_id: str) -> SelectionBinding:
        b = self.get(session_id).with_rerank(rerank_id); self.set(session_id, b); return b
    def drop(self, session_id: str) -> None:
        self._b.pop(session_id, None)
