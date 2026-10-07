from __future__ import annotations

from typing import Any

from backend.application.capability.controller import (
    ApplicationCapabilityController,
)
from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)
from backend.application.capability.installer import (
    ApplicationCapabilityInstaller,
)
from backend.application.capability.lifecycle import (
    ApplicationCapabilityState,
)
from backend.application.capability.provider import (
    ApplicationCapabilityProvider,
)


class ApplicationCapabilityManager:
    """
    Capability orchestration boundary.

    Owns:
        - capability coordination
        - install delegation
        - resolve delegation

    Does not own:
        - registry
        - lifecycle transitions
        - capability construction
    """

    VERSION = "3.2"

    def __init__(
        self,
        *,
        provider: ApplicationCapabilityProvider,
        installer: ApplicationCapabilityInstaller,
        controller: ApplicationCapabilityController,
    ) -> None:
        self.provider = provider
        self.installer = installer
        self.controller = controller

        if not self.ready():
            raise RuntimeError(
                "capability manager unavailable"
            )

    def install(
        self,
        descriptor: ApplicationCapabilityDescriptor,
        implementation: Any,
        context: Any = None,
    ) -> Any:
        if not isinstance(
            descriptor,
            ApplicationCapabilityDescriptor,
        ):
            raise TypeError(
                "capability descriptor required"
            )

        key = descriptor.key()

        if self.controller.lifecycle.registered(key):
            raise ValueError(
                f"capability lifecycle already registered: {key}"
            )

        if key in self.installer.registry.keys():
            raise ValueError(
                f"capability already installed: {key}"
            )

        capability = self.installer.install(
            descriptor,
            implementation,
            context,
        )

        try:
            self.controller.lifecycle.register(key)
            self.controller.lifecycle.install(key)
        except Exception:
            self.installer.registry.unregister(key)

            if self.controller.lifecycle.registered(key):
                self.controller.lifecycle.unregister(key)

            raise

        return capability

    def enable(
        self,
        name: str,
        context: Any = None,
    ) -> None:
        self.controller.enable(
            name,
            context,
        )

    def disable(
        self,
        name: str,
    ) -> None:
        self.controller.disable(
            name,
        )

    def unload(
        self,
        name: str,
    ) -> None:
        self.controller.unload(
            name,
        )

    def resolve(
        self,
        name: str,
    ) -> Any:
        return self.provider.resolve(
            name,
        )

    def state(
        self,
        name: str,
    ) -> ApplicationCapabilityState:
        return self.controller.lifecycle.state(
            self.controller.resolver.key(name)
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.provider.ready()
            and self.installer.ready()
            and self.controller.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityManager",
]
