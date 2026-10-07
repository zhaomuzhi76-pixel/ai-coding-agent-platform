"""索引命名空间解析：EmbeddingDescriptor → IndexNamespace，带缓存。"""
from __future__ import annotations
from backend.providers.selection.contracts import EmbeddingDescriptor
from backend.rag.selection.contracts import IndexNamespace

class NamespaceResolver:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, int], IndexNamespace] = {}
    def resolve(self, descriptor: EmbeddingDescriptor) -> IndexNamespace:
        key = (descriptor.id, descriptor.dim)
        ns = self._cache.get(key)
        if ns is None:
            ns = IndexNamespace.from_descriptor(descriptor)
            self._cache[key] = ns
        return ns
