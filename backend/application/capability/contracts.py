from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ApplicationCapabilityProtocol(Protocol):
    name: str
    version: str

    def capabilities(self) -> tuple[str, ...]:
        ...

    def initialize(
        self,
        context: Any = None,
    ) -> None:
        ...

    def shutdown(self) -> None:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class ApplicationCapabilityProviderProtocol(Protocol):
    name: str
    version: str

    def create(
        self,
        implementation: Any,
        context: Any = None,
    ) -> ApplicationCapabilityProtocol:
        ...

    def install(
        self,
        descriptor: "ApplicationCapabilityDescriptor",
        implementation: Any,
        context: Any = None,
    ) -> ApplicationCapabilityProtocol:
        ...

    def resolve(
        self,
        name: str,
    ) -> ApplicationCapabilityProtocol:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationCapabilityProtocol",
    "ApplicationCapabilityProviderProtocol",
]
