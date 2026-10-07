from __future__ import annotations

from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)


class ApplicationCapabilityIndex:
    """
    Capability lookup index.

    Owns:
        - descriptor indexing
        - name/version/category lookup

    Does not own:
        - capability instance lifecycle
        - capability construction
        - capability registration policy
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._descriptors: dict[
            str,
            ApplicationCapabilityDescriptor,
        ] = {}

    def add(
        self,
        descriptor: ApplicationCapabilityDescriptor,
    ) -> None:
        key = descriptor.key()

        if key in self._descriptors:
            raise ValueError(
                f"capability descriptor exists: {key}"
            )

        self._descriptors[key] = descriptor

    def remove(
        self,
        key: str,
    ) -> None:
        self._descriptors.pop(
            key,
            None,
        )

    def resolve(
        self,
        name: str,
        version: str | None = None,
        category: str = "application",
    ) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "capability name required"
            )

        name = name.strip()

        if version:
            key = (
                f"{category}.{name}:"
                f"{version}"
            )

            if key not in self._descriptors:
                raise LookupError(
                    f"capability not found: {key}"
                )

            return key

        if name in self._descriptors:
            return name

        matches = [
            key
            for key, descriptor in self._descriptors.items()
            if (
                descriptor.name == name
                and descriptor.category == category
            )
        ]

        if not matches:
            raise LookupError(
                f"capability not found: {category}.{name}"
            )

        if len(matches) > 1:
            raise LookupError(
                f"version required: {category}.{name}"
            )

        return matches[0]

    def keys(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            self._descriptors
        )

    def names(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            descriptor.name
            for descriptor in self._descriptors.values()
        )

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
            "size": len(self._descriptors),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityIndex",
]
