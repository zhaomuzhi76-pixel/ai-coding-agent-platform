from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ProviderCapabilityProtocol(Protocol):
    name: str
    version: str
    provider: str

    def execute(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class ProviderCapabilityRegistryProtocol(Protocol):
    def register(
        self,
        capability: ProviderCapabilityProtocol,
    ) -> None:
        ...

    def resolve(
        self,
        provider: str,
        name: str,
    ) -> ProviderCapabilityProtocol:
        ...

    def exists(
        self,
        provider: str,
        name: str,
    ) -> bool:
        ...

    def ready(self) -> bool:
        ...


__all__ = [
    "ProviderCapabilityProtocol",
    "ProviderCapabilityRegistryProtocol",
]
