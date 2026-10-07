from __future__ import annotations

from typing import Any

from backend.providers.adapters.runtime_adapter import (
    RuntimeProviderAdapter,
)
from backend.providers.factory import ProviderFactory
from backend.providers.registry import ProviderRegistry


class RuntimeProviderBridge:
    """Bind concrete providers into the generic provider registry."""

    VERSION = "2.0"

    def __init__(
        self,
        registry: ProviderRegistry,
        factory: ProviderFactory,
    ) -> None:
        if registry is None:
            raise ValueError("provider registry required")
        if factory is None:
            raise ValueError("provider factory required")
        self.registry = registry
        self.factory = factory
        self._adapters: dict[
            str,
            RuntimeProviderAdapter,
        ] = {}

    def register(
        self,
        *,
        name: str,
        provider_type: str,
        category: str = "llm",
        config: dict[str, Any] | None = None,
    ) -> RuntimeProviderAdapter:
        adapter = RuntimeProviderAdapter(
            name=name,
            provider_type=provider_type,
            category=category,
            factory=self.factory,
            config=config,
        )
        self.registry.register(adapter)
        self._adapters[name] = adapter
        return adapter

    def resolve(
        self,
        name: str,
    ) -> RuntimeProviderAdapter:
        adapter = self._adapters.get(name)
        if adapter is None:
            raise LookupError(
                f"runtime provider adapter not found: {name}"
            )
        return adapter

    def names(self) -> tuple[str, ...]:
        return tuple(self._adapters)

    def ready(self) -> bool:
        return (
            self.factory.ready()
            and self.registry.ready()
            and all(
                adapter.ready()
                for adapter in self._adapters.values()
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "providers": self.names(),
            "registry": self.registry.dump(),
            "ready": self.ready(),
        }


__all__ = ["RuntimeProviderBridge"]
