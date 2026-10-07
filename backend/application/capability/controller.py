from __future__ import annotations

from typing import Any

from backend.application.capability.lifecycle import (
    ApplicationCapabilityLifecycle,
    ApplicationCapabilityState,
)
from backend.application.capability.state_guard import (
    ApplicationCapabilityStateGuard,
)


class ApplicationCapabilityController:
    """
    Capability lifecycle controller.

    Owns:
        - lifecycle transitions

    Does not own:
        - registry
        - installation
        - construction
    """

    VERSION = "1.2"

    def __init__(
        self,
        lifecycle: ApplicationCapabilityLifecycle,
        resolver: Any,
    ) -> None:
        if not lifecycle.ready():
            raise RuntimeError(
                "capability lifecycle unavailable"
            )

        self.lifecycle = lifecycle
        self.resolver = resolver

    def enable(
        self,
        name: str,
        context: Any = None,
    ) -> None:
        key = self.resolver.key(name)
        capability = self.resolver.resolve(name)
        state = self.lifecycle.state(key)

        ApplicationCapabilityStateGuard.require_not_unloaded(
            state,
            name,
        )

        if state is ApplicationCapabilityState.ENABLED:
            return

        initialize = getattr(
            capability,
            "initialize",
            None,
        )

        if initialize:
            initialize(context)

        if not capability.ready():
            raise RuntimeError(
                f"capability unavailable: {name}"
            )

        if state in (
            ApplicationCapabilityState.INSTALLED,
            ApplicationCapabilityState.DISABLED,
        ):
            self.lifecycle.enable(key)

    def disable(
        self,
        name: str,
    ) -> None:
        key = self.resolver.key(name)
        capability = self.resolver.resolve(name)
        state = self.lifecycle.state(key)

        if state is ApplicationCapabilityState.DISABLED:
            return

        ApplicationCapabilityStateGuard.require_enabled(
            state,
        )

        shutdown = getattr(
            capability,
            "shutdown",
            None,
        )

        if shutdown:
            shutdown()

        self.lifecycle.disable(key)

    def unload(
        self,
        name: str,
    ) -> None:
        key = self.resolver.key(name)
        state = self.lifecycle.state(key)

        if state is ApplicationCapabilityState.ENABLED:
            self.disable(name)

        self.lifecycle.unload(key)

    def ready(
        self,
    ) -> bool:
        return self.lifecycle.ready()


__all__ = [
    "ApplicationCapabilityController",
]
