from __future__ import annotations

from typing import Any

from backend.providers.adapters.runtime_adapter import (
    RuntimeProviderAdapter,
)
from backend.providers.adapters.runtime_bridge import (
    RuntimeProviderBridge,
)
from backend.providers.factory import (
    ProviderFactory,
)
from backend.providers.registry import (
    ProviderRegistry,
)


class ProviderAssembly:
    """
    Assemble provider definitions and instances.

    Responsibility:
        - register provider classes
        - create provider adapters
        - create concrete provider instances

    Not Responsible:
        - capability binding
        - provider runtime execution
        - application composition
    """

    VERSION = "3.0"

    def __init__(
        self,
        registry: ProviderRegistry,
        factory: ProviderFactory | None = None,
    ) -> None:
        if registry is None:
            raise ValueError(
                "provider registry required"
            )

        self.registry = registry
        self.factory = factory or ProviderFactory()
        self.bridge = RuntimeProviderBridge(
            registry=registry,
            factory=self.factory,
        )

    def build(
        self,
        provider_types: dict[str, dict[str, Any]],
    ) -> tuple[
        tuple[RuntimeProviderAdapter, ...],
        tuple[Any, ...],
    ]:
        if not provider_types:
            raise ValueError(
                "provider types required"
            )

        for provider_type, config in provider_types.items():
            provider_class = config.get(
                "provider_class"
            )

            if provider_class is None:
                raise ValueError(
                    f"provider class required: "
                    f"{provider_type}"
                )

            self.factory.register(
                provider_type,
                provider_class,
            )

        adapters: list[
            RuntimeProviderAdapter
        ] = []
        providers: list[Any] = []

        for provider_type, config in provider_types.items():
            name = config.get(
                "name",
                provider_type,
            )

            adapter = self.bridge.register(
                name=name,
                provider_type=provider_type,
                category=config.get(
                    "category",
                    "llm",
                ),
                config=config.get(
                    "config",
                    {},
                ),
            )

            providers.append(
                adapter.create()
            )
            adapters.append(adapter)

        return (
            tuple(adapters),
            tuple(providers),
        )

    def ready(self) -> bool:
        return (
            self.factory.ready()
            and self.registry.ready()
            and self.bridge.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "providers": tuple(
                self.registry.names()
            ),
        }


__all__ = [
    "ProviderAssembly",
]
