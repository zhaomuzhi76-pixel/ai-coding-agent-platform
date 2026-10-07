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


class ApplicationCapabilityInstaller:
    """
    Capability installation boundary.

    Owns:
        - implementation creation
        - descriptor registration

    Does not own:
        - lifecycle
        - lookup
        - construction of registry
    """

    VERSION = "1.0"

    def __init__(
        self,
        registry: ApplicationCapabilityRegistry,
    ) -> None:
        if not registry.ready():
            raise RuntimeError(
                "capability registry unavailable"
            )

        self.registry = registry

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
            if isinstance(
                implementation,
                type,
            )
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

    def ready(
        self,
    ) -> bool:
        return self.registry.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityInstaller",
]
