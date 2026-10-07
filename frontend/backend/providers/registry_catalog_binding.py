"""把 catalog 的 ModelDescriptor 注册进 provider 注册表。
   不修改 backend/providers/registry.py。"""
from __future__ import annotations

from typing import Protocol

from .config.catalog import list_models


class RegistryPort(Protocol):
    def register_model(self, model_id: str, *, provider: str,
                       context_window: int, display_name: str) -> None: ...


class CatalogRegistryBinding:
    """幂等绑定器：多次 bind 不会重复注册。"""

    def __init__(self, registry: RegistryPort) -> None:
        self._registry = registry
        self._bound: set[str] = set()

    def bind(self) -> int:
        n = 0
        for m in list_models():
            if m.id in self._bound:
                continue
            self._registry.register_model(
                m.id, provider=m.provider,
                context_window=m.context_window,
                display_name=m.display_name,
            )
            self._bound.add(m.id)
            n += 1
        return n


def bind_catalog_to_registry(registry: RegistryPort) -> int:
    return CatalogRegistryBinding(registry).bind()
