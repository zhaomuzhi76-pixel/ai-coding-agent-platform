from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LifecycleComponentProtocol(Protocol):
    """
    Canonical component lifecycle capability.
    """

    def initialize(self) -> None:
        ...

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def destroy(self) -> None:
        ...


__all__ = [
    "LifecycleComponentProtocol",
]
