from __future__ import annotations

from backend.application.capability.registry import (
    ApplicationCapabilityRegistry,
)


class ApplicationCapabilityResolver:
    """
    Capability resolution boundary.

    Owns:
        - capability lookup delegation
        - capability key resolution

    Does not own:
        - registration
        - lifecycle
        - construction
        - registry ownership
    """

    VERSION = "2.0"

    def __init__(
        self,
        registry: ApplicationCapabilityRegistry,
    ) -> None:
        if not registry.ready():
            raise RuntimeError(
                "capability registry unavailable"
            )

        self.registry = registry

    def resolve(
        self,
        name: str,
        version: str | None = None,
        category: str = "application",
    ):
        return self.registry.resolve(
            name=name,
            version=version,
            category=category,
        )

    def key(
        self,
        name: str,
        version: str | None = None,
        category: str = "application",
    ) -> str:
        return self.registry.index.resolve(
            name=name,
            version=version,
            category=category,
        )

    def exists(
        self,
        name: str,
        version: str | None = None,
        category: str = "application",
    ) -> bool:
        return self.registry.exists(
            name=name,
            version=version,
            category=category,
        )

    def names(
        self,
    ) -> tuple[str, ...]:
        return self.registry.names()

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
            "registry": self.registry.dump(),
        }


__all__ = [
    "ApplicationCapabilityResolver",
]
