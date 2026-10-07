from __future__ import annotations

from backend.agent.capability.capability_registry import (
    CapabilityRegistry,
)


class CapabilityComposition:
    """
    Canonical capability composition facade.

    Responsibility:
        - own the capability registry boundary
        - expose composition readiness
        - expose diagnostics

    Does not own:
        - capability implementation
        - capability execution
        - runtime lifecycle
    """

    VERSION = "2.0"

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
    ) -> None:
        self.registry = (
            registry
            if registry is not None
            else CapabilityRegistry()
        )

    def ready(self) -> bool:
        return self.registry.ready()

    def names(self) -> tuple[str, ...]:
        return self.registry.names()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registry": self.registry.dump(),
        }


__all__ = [
    "CapabilityComposition",
]
