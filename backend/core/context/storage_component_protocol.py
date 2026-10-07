from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import CoreValue


@runtime_checkable
class StorageComponentProtocol(
    Protocol,
):
    """
    Minimal storage component capability.

    Responsibility:

        - readiness
        - clear
        - snapshot
    """

    def ready(
        self,
    ) -> bool:
        ...

    def clear(
        self,
    ) -> None:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "StorageComponentProtocol",
]
