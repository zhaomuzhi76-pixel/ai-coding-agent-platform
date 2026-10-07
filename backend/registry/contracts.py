from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RegistryEntryProtocol(Protocol):
    name: str
    version: str

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class RegistryTargetProtocol(Protocol):
    def register(self, item: Any) -> None:
        ...

    def resolve(self, name: str) -> Any:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "RegistryEntryProtocol",
    "RegistryTargetProtocol",
]
