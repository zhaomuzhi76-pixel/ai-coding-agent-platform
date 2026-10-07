from __future__ import annotations

from backend.application.capability.contracts import (
    ApplicationCapabilityProtocol,
)
from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)
from backend.application.capability.index import (
    ApplicationCapabilityIndex,
)


class ApplicationCapabilityRegistry:
    """
    Capability registration boundary.

    Owns:
        - capability instance registration
        - capability removal
        - capability storage

    Does not own:
        - lifecycle
        - construction
        - lookup rules
    """

    VERSION = "3.1"

    def __init__(self) -> None:
        self._items: dict[
            str,
            ApplicationCapabilityProtocol,
        ] = {}
        self.index = ApplicationCapabilityIndex()

    def register(
        self,
        descriptor: ApplicationCapabilityDescriptor,
        capability: ApplicationCapabilityProtocol,
    ) -> None:
        if not isinstance(
            capability,
            ApplicationCapabilityProtocol,
        ):
            raise TypeError(
                "invalid capability"
            )

        if capability.name != descriptor.name:
            raise ValueError(
                "capability name mismatch"
            )

        if capability.version != descriptor.version:
            raise ValueError(
                "capability version mismatch"
            )

        key = descriptor.key()

        if key in self._items:
            raise ValueError(
                f"capability exists: {key}"
            )

        self._items[key] = capability
        self.index.add(descriptor)

    def unregister(
        self,
        key: str,
    ) -> None:
        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                "capability key required"
            )

        self._items.pop(key, None)
        self.index.remove(key)

    def resolve(
        self,
        name: str,
        version: str | None = None,
        category: str = "application",
    ) -> ApplicationCapabilityProtocol:
        key = self.index.resolve(
            name,
            version,
            category,
        )
        return self._items[key]

    def exists(
        self,
        name: str,
        version: str | None = None,
        category: str = "application",
    ) -> bool:
        try:
            self.index.resolve(
                name,
                version,
                category,
            )
            return True
        except LookupError:
            return False

    def keys(
        self,
    ) -> tuple[str, ...]:
        return self.index.keys()

    def names(
        self,
    ) -> tuple[str, ...]:
        return self.index.names()

    def ready(
        self,
    ) -> bool:
        return all(
            item.ready()
            for item in self._items.values()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "capabilities": self.keys(),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityRegistry",
]
