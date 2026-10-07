from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import CoreValue


@runtime_checkable
class ContextStateProtocol(
    Protocol,
):
    """
    Kernel context lifecycle state capability.

    Responsibility:

        - expose current state readiness
        - expose immutable state snapshot

    Not Responsible:

        - lifecycle transition
        - lifecycle management
        - persistence
        - scheduling
    """

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "ContextStateProtocol",
]
