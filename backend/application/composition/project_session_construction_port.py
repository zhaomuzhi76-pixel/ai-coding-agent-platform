from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ApplicationProjectSessionConstructionProtocol(
    Protocol,
):
    """
    Application-facing project/session construction port.

    Concrete construction belongs to assembly.
    """

    def create(
        self,
    ) -> dict[str, object]:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationProjectSessionConstructionProtocol",
]
