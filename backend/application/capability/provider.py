from __future__ import annotations

from typing import Any

from backend.application.capability.contracts import (
    ApplicationCapabilityProtocol,
)
from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)
from backend.application.capability.registry import (
    ApplicationCapabilityRegistry,
)


class ApplicationCapabilityProvider:
    """
    Capability resolution and installation provider.

    Owns:
        - capability lookup
        - capability creation delegation
        - capability installation delegation

    Does not own:
        - lifecycle
        - registry construction
    """

    VERSION = "4.0"

    name = "application_capability_provider"
    version = VERSION

    def __init__(
        self,
        registry: ApplicationCapabilityRegistry,
    ) -> None:
        if not isinstance(
            registry,
            ApplicationCapabilityRegistry,
        ):
            raise TypeError(
                "registry must be ApplicationCapabilityRegistry"
            )

        if not registry.ready():
            raise RuntimeError(
                "capability registry unavailable"
            )

        self.registry = registry

    def create(
        self,
        implementation: Any,
        context: Any = None,
    ) -> ApplicationCapabilityProtocol:
        if implementation is None:
            raise ValueError(
                "capability implementation required"
            )

        capability = (
            implementation(context)
            if isinstance(implementation, type)
            else implementation
        )

        if not isinstance(
            capability,
            ApplicationCapabilityProtocol,
        ):
            raise TypeError(
                "invalid capability implementation"
            )

        return capability

    def install(
        self,
        descriptor: ApplicationCapabilityDescriptor,
        implementation: Any,
        context: Any = None,
    ) -> ApplicationCapabilityProtocol:
        capability = self.create(
            implementation,
            context,
        )
        self.registry.register(
            descriptor,
            capability,
        )
        return capability

    def resolve(
        self,
        name: str,
    ) -> ApplicationCapabilityProtocol:
        return self.registry.resolve(name)

    def ready(self) -> bool:
        return self.registry.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "registry": self.registry.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityProvider",
]
