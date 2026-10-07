from __future__ import annotations

from backend.application.capability.registry import (
    ApplicationCapabilityRegistry,
)


class ApplicationCapabilityRegistryFactory:
    """
    Sole construction owner for ApplicationCapabilityRegistry.

    Owns only:
        - registry construction
        - construction-time readiness validation
    """

    VERSION = "1.0"

    def create(self) -> ApplicationCapabilityRegistry:
        if not self.ready():
            raise RuntimeError(
                "application capability registry factory unavailable"
            )

        registry = ApplicationCapabilityRegistry()

        if not registry.ready():
            raise RuntimeError(
                "application capability registry unavailable"
            )

        return registry

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityRegistryFactory",
]
