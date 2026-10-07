from __future__ import annotations

from backend.application.capability.lifecycle import (
    ApplicationCapabilityLifecycle,
)


class ApplicationCapabilityLifecycleFactory:
    """
    Sole construction owner for ApplicationCapabilityLifecycle.

    Owns only:
        - lifecycle construction
        - construction-time readiness validation
    """

    VERSION = "1.0"

    def create(self) -> ApplicationCapabilityLifecycle:
        if not self.ready():
            raise RuntimeError(
                "application capability lifecycle factory unavailable"
            )

        lifecycle = ApplicationCapabilityLifecycle()

        if not lifecycle.ready():
            raise RuntimeError(
                "application capability lifecycle unavailable"
            )

        return lifecycle

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityLifecycleFactory",
]
