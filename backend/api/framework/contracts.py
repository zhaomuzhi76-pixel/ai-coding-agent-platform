from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class APITransportProtocol(Protocol):
    name: str
    version: str

    async def handle(
        self,
        request: Any,
    ) -> Any:
        ...

    def initialize(self) -> None:
        ...

    def shutdown(self) -> None:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class APIRouteProtocol(Protocol):
    path: str
    method: str

    async def handle(
        self,
        request: Any,
    ) -> Any:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "APITransportProtocol",
    "APIRouteProtocol",
]
