from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import CoreValue


@runtime_checkable
class ExecutionContextStorageProtocol(
    Protocol,
):
    """
    Runtime execution storage capability contract.

    Responsibility:

        - expose storage readiness
        - clear mutable storage
        - expose storage snapshot

    Not Responsible:

        - storage creation
        - variable management
        - output management
        - persistence
        - lifecycle
        - scheduling
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
    "ExecutionContextStorageProtocol",
]
