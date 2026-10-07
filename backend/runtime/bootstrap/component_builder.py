from __future__ import annotations

from backend.runtime.bootstrap.runtime_component_provider_contract import (
    RuntimeComponentProviderProtocol,
)


class RuntimeComponentBuilder:
    """
    Capability-based runtime component builder.

    Responsibility:
        - resolve capability provider
        - create runtime component
    """

    VERSION = "10.0"

    RESPONSIBILITY = (
        "runtime_component_resolution_boundary",
    )

    def __init__(
        self,
        *,
        capability_registry,
    ) -> None:
        if capability_registry is None:
            raise ValueError(
                "capability registry required"
            )

        self.capability_registry = capability_registry

    def create(
        self,
        capability: str,
    ) -> object:
        if not capability:
            raise ValueError("capability required")

        provider = self.capability_registry.resolve(
            capability
        )

        if not isinstance(
            provider,
            RuntimeComponentProviderProtocol,
        ):
            raise TypeError(
                "component provider must implement "
                "RuntimeComponentProviderProtocol"
            )

        return provider.create()

    def has(
        self,
        capability: str,
    ) -> bool:
        if not capability:
            return False

        return self.capability_registry.exists(
            capability
        )

    def ready(
        self,
    ) -> bool:
        return self.capability_registry.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeComponentBuilder",
]
