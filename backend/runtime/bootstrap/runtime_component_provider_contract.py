from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RuntimeComponentProviderProtocol(Protocol):
    """Capability provider contract for runtime component creation."""

    def create(self) -> object:
        ...


__all__ = [
    "RuntimeComponentProviderProtocol",
]
