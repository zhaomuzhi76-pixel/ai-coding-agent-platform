from __future__ import annotations

from backend.application.capability.provider import (
    ApplicationCapabilityProvider,
)
from backend.application.capability.registry import (
    ApplicationCapabilityRegistry,
)
from backend.application.capability.registry_factory import (
    ApplicationCapabilityRegistryFactory,
)


class ApplicationCapabilityProviderFactory:
    """
    Sole construction owner for ApplicationCapabilityProvider.

    Owns only:
        - registry resolution
        - provider construction
        - construction-time readiness validation
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        registry: ApplicationCapabilityRegistry | None = None,
    ) -> ApplicationCapabilityProvider:
        if not self.ready():
            raise RuntimeError(
                "application capability provider factory unavailable"
            )

        active_registry = (
            registry
            if registry is not None
            else ApplicationCapabilityRegistryFactory().create()
        )

        if not isinstance(
            active_registry,
            ApplicationCapabilityRegistry,
        ):
            raise TypeError(
                "registry must be ApplicationCapabilityRegistry"
            )

        provider = ApplicationCapabilityProvider(
            registry=active_registry,
        )

        if not provider.ready():
            raise RuntimeError(
                "application capability provider unavailable"
            )

        return provider

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityProviderFactory",
]
