from __future__ import annotations

from backend.providers.capability.contracts import (
    ProviderCapabilityProtocol,
    ProviderCapabilityRegistryProtocol,
)
from backend.providers.capability.descriptor import (
    ProviderCapabilityDescriptor,
)


class ProviderCapabilityRegistry(
    ProviderCapabilityRegistryProtocol,
):
    """
    Provider capability registry.

    Owns capability bindings, not provider implementations.
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._items: dict[
            str,
            tuple[
                ProviderCapabilityDescriptor,
                ProviderCapabilityProtocol,
            ],
        ] = {}

    def register(
        self,
        capability: ProviderCapabilityProtocol,
    ) -> None:
        if capability is None:
            raise ValueError(
                "provider capability required"
            )

        key = self._key(
            capability.provider,
            capability.name,
        )

        if key in self._items:
            raise ValueError(
                f"provider capability exists: {key}"
            )

        descriptor = getattr(
            capability,
            "descriptor",
            None,
        )

        if descriptor is None:
            descriptor = ProviderCapabilityDescriptor(
                provider=capability.provider,
                name=capability.name,
                version=capability.version,
                method=capability.name,
            )

        self._items[key] = (
            descriptor,
            capability,
        )

    def resolve(
        self,
        provider: str,
        name: str,
    ) -> ProviderCapabilityProtocol:
        key = self._key(provider, name)

        try:
            return self._items[key][1]
        except KeyError as error:
            raise LookupError(
                f"provider capability not found: {key}"
            ) from error

    def descriptor(
        self,
        provider: str,
        name: str,
    ) -> ProviderCapabilityDescriptor:
        key = self._key(provider, name)

        try:
            return self._items[key][0]
        except KeyError as error:
            raise LookupError(
                f"provider capability not found: {key}"
            ) from error

    def exists(
        self,
        provider: str,
        name: str,
    ) -> bool:
        return self._key(
            provider,
            name,
        ) in self._items

    def names(
        self,
        provider: str | None = None,
    ) -> tuple[str, ...]:
        if provider is None:
            return tuple(
                self._items
            )

        prefix = f"{provider}."
        return tuple(
            key[len(prefix):]
            for key in self._items
            if key.startswith(prefix)
        )

    def ready(self) -> bool:
        return all(
            capability.ready()
            for _, capability
            in self._items.values()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "capabilities": tuple(
                self._items
            ),
            "ready": self.ready(),
        }

    @staticmethod
    def _key(
        provider: str,
        name: str,
    ) -> str:
        if not provider:
            raise ValueError(
                "provider name required"
            )
        if not name:
            raise ValueError(
                "capability name required"
            )
        return f"{provider}.{name}"


__all__ = [
    "ProviderCapabilityRegistry",
]
