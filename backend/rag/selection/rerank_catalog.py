"""精排模型目录。"""
from __future__ import annotations
from backend.providers.selection.contracts import RerankDescriptor

class RerankCatalog:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], RerankDescriptor] = {}
    def register(self, rerank_id: str, provider: str, display: str = "") -> RerankDescriptor:
        d = RerankDescriptor(id=rerank_id, provider=provider, display=display)
        self._items[(rerank_id, provider)] = d; return d
    def get(self, rerank_id: str, provider: str) -> RerankDescriptor | None:
        return self._items.get((rerank_id, provider))
    def all(self) -> list[RerankDescriptor]:
        return list(self._items.values())
