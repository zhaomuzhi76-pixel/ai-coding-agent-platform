from __future__ import annotations

from typing import Any

from backend.providers.capability.contracts import (
    ProviderCapabilityProtocol,
)
from backend.providers.capability.descriptor import (
    ProviderCapabilityDescriptor,
)
from backend.providers.capability.registry import (
    ProviderCapabilityRegistry,
)


class BoundProviderCapability(
    ProviderCapabilityProtocol,
):
    """
    Bind one provider method to the capability contract.

    The bound method result is preserved:
    coroutine -> caller may await
    async iterator -> caller may iterate asynchronously
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        provider: str,
        capability: ProviderCapabilityDescriptor,
        target: Any,
    ) -> None:
        if not provider:
            raise ValueError(
                "provider name required"
            )
        if capability is None:
            raise ValueError(
                "capability descriptor required"
            )
        if target is None:
            raise ValueError(
                "provider capability target required"
            )
        if not callable(target):
            raise TypeError(
                "provider capability target must callable"
            )

        self.provider = provider
        self.descriptor = capability
        self.name = capability.name
        self.version = capability.version
        self._target = target

    def execute(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        return self._target(
            *args,
            **kwargs,
        )

    def ready(self) -> bool:
        return bool(
            self.provider
            and self._target
            and self.descriptor.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "provider": self.provider,
            "descriptor": self.descriptor.dump(),
            "ready": self.ready(),
        }


class ProviderCapabilityBridge:
    """
    Expose existing provider methods as independent
    capabilities.
    """

    VERSION = "1.0"

    DEFAULT_METHODS = (
        "chat",
        "stream_chat",
        "embedding",
    )

    def __init__(
        self,
        registry: ProviderCapabilityRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "provider capability registry required"
            )
        self.registry = registry

    def bind(
        self,
        provider_name: str,
        provider: Any,
        capabilities: tuple[str, ...] | None = None,
    ) -> tuple[BoundProviderCapability, ...]:
        if provider is None:
            raise ValueError(
                "provider required"
            )

        names = (
            capabilities
            or self.DEFAULT_METHODS
        )
        bound: list[
            BoundProviderCapability
        ] = []

        for name in names:
            target = getattr(
                provider,
                name,
                None,
            )

            if target is None:
                continue

            descriptor = (
                ProviderCapabilityDescriptor(
                    provider=provider_name,
                    name=name,
                    version=getattr(
                        provider,
                        "VERSION",
                        "1.0",
                    ),
                    method=name,
                )
            )

            capability = BoundProviderCapability(
                provider=provider_name,
                capability=descriptor,
                target=target,
            )

            self.registry.register(
                capability
            )
            bound.append(capability)

        return tuple(bound)

    def ready(self) -> bool:
        return self.registry.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "registry": self.registry.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "BoundProviderCapability",
    "ProviderCapabilityBridge",
]
