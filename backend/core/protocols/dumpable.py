from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import CoreValue


@runtime_checkable
class DumpableProtocol(Protocol):
    """
    Base dump contract.

    Responsibility:
        - expose serializable component snapshot

    Not Responsible:
        - storage
        - persistence
        - transport
        - business data transformation
    """

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "DumpableProtocol",
]
