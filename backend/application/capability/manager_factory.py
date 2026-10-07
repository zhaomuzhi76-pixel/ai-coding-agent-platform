from __future__ import annotations

from backend.application.capability.controller import (
    ApplicationCapabilityController,
)
from backend.application.capability.installer import (
    ApplicationCapabilityInstaller,
)
from backend.application.capability.lifecycle_factory import (
    ApplicationCapabilityLifecycleFactory,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.capability.provider import (
    ApplicationCapabilityProvider,
)
from backend.application.capability.provider_factory import (
    ApplicationCapabilityProviderFactory,
)
from backend.application.capability.registry import (
    ApplicationCapabilityRegistry,
)
from backend.application.capability.resolver import (
    ApplicationCapabilityResolver,
)


class ApplicationCapabilityManagerFactory:
    """
    Capability manager assembly boundary.

    Owns:
        - provider assembly
        - resolver assembly
        - controller assembly
        - manager assembly

    Does not own:
        - registry construction
        - capability construction
        - lifecycle implementation
    """

    VERSION = "3.0"

    def create(
        self,
        *,
        registry: ApplicationCapabilityRegistry | None = None,
        provider: ApplicationCapabilityProvider | None = None,
    ) -> ApplicationCapabilityManager:

        active_provider = (
            provider
            if provider is not None
            else ApplicationCapabilityProviderFactory()
            .create(
                registry=registry,
            )
        )

        active_registry = active_provider.registry

        resolver = ApplicationCapabilityResolver(
            registry=active_registry,
        )

        installer = ApplicationCapabilityInstaller(
            registry=active_registry,
        )

        lifecycle = (
            ApplicationCapabilityLifecycleFactory()
            .create()
        )

        controller = ApplicationCapabilityController(
            lifecycle=lifecycle,
            resolver=resolver,
        )

        manager = ApplicationCapabilityManager(
            provider=active_provider,
            installer=installer,
            controller=controller,
        )

        if not manager.ready():
            raise RuntimeError(
                "application capability manager unavailable"
            )

        return manager

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityManagerFactory",
]
