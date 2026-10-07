from __future__ import annotations

from typing import Any

from backend.providers.contracts import ProviderProtocol
from backend.providers.factory import ProviderFactory


class RuntimeProviderAdapter(ProviderProtocol):
    """Adapt concrete provider implementations to ProviderProtocol."""

    VERSION = "2.1"

    def __init__(
        self,
        *,
        name: str,
        provider_type: str,
        factory: ProviderFactory,
        category: str = "llm",
        config: dict[str, Any] | None = None,
    ) -> None:
        if not name:
            raise ValueError("provider name required")
        if not provider_type:
            raise ValueError("provider type required")
        if factory is None:
            raise ValueError("provider factory required")
        self.name = name
        self.version = self.VERSION
        self.category = category
        self.provider_type = provider_type
        self.factory = factory
        self.config = dict(config or {})
        self._instances: list[Any] = []

    def create(self, context: Any = None) -> Any:
        parameters = dict(self.config)
        if isinstance(context, dict):
            parameters.update(context)
        instance = self.factory.create(
            self.provider_type,
            **parameters,
        )
        self._instances.append(instance)
        return instance

    def ready(self) -> bool:
        return (
            self.factory.ready()
            and self.factory.exists(
                self.provider_type
            )
        )

    def shutdown(self) -> None:
        remaining = []
        for instance in self._instances:
            shutdown = getattr(
                instance,
                "shutdown",
                None,
            )
            if shutdown is None:
                continue
            try:
                shutdown()
            except Exception:
                remaining.append(instance)
        self._instances = remaining

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "provider_type": self.provider_type,
            "instances": len(self._instances),
            "ready": self.ready(),
        }


__all__ = ["RuntimeProviderAdapter"]
