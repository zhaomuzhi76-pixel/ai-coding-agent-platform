from __future__ import annotations

from typing import Any


class ProviderAssemblyContext:
    """
    Shared provider assembly state.

    Components are populated by dedicated assembly stages.
    """

    VERSION = "1.1"

    def __init__(
        self,
        *,
        provider_registry: Any,
        provider_bridge: Any,
        capability_registry: Any,
        capability_bridge: Any,
        capability_resolver: Any,
    ) -> None:
        dependencies = {
            "provider_registry": provider_registry,
            "provider_bridge": provider_bridge,
            "capability_registry": capability_registry,
            "capability_bridge": capability_bridge,
            "capability_resolver": capability_resolver,
        }

        for name, value in dependencies.items():
            if value is None:
                raise ValueError(
                    f"{name} required"
                )

        self.provider_registry = provider_registry
        self.provider_bridge = provider_bridge
        self.capability_registry = capability_registry
        self.capability_bridge = capability_bridge
        self.capability_resolver = capability_resolver

        self.selector = None
        self.execution = None
        self.runtime = None

    def ready(self) -> bool:
        required = (
            self.provider_registry,
            self.provider_bridge,
            self.capability_registry,
            self.capability_bridge,
            self.capability_resolver,
            self.selector,
            self.execution,
            self.runtime,
        )

        if not all(
            item is not None
            for item in required
        ):
            return False

        return all(
            item.ready()
            for item in required
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProviderAssemblyContext",
]
