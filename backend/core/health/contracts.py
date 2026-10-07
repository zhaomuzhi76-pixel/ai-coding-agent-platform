from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)


@runtime_checkable
class HealthComponentProtocol(Protocol):
    """
    Component health snapshot capability.
    """

    def health(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "HealthComponentProtocol",
]
