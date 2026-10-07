"""向量模型目录。"""
from __future__ import annotations
from backend.providers.selection.contracts import EmbeddingDescriptor

class EmbeddingCatalog:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], EmbeddingDescriptor] = {}
    def register(self, embedding_id: str, provider: str, dim: int,
                 display: str = "", max_input_tokens: int = 8192) -> EmbeddingDescriptor:
        d = EmbeddingDescriptor(id=embedding_id, provider=provider, dim=dim,
                                display=display, max_input_tokens=max_input_tokens)
        self._items[(embedding_id, provider)] = d; return d
    def get(self, embedding_id: str, provider: str) -> EmbeddingDescriptor | None:
        return self._items.get((embedding_id, provider))
    def all(self) -> list[EmbeddingDescriptor]:
        return list(self._items.values())
