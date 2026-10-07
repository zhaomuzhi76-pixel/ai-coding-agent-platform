from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import CoreValue


@runtime_checkable
class ContextRegistryItemProtocol(
    Protocol,
):
    """
    Context registry item capability.

    Responsibility:

        - expose context snapshot
    """

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "ContextRegistryItemProtocol",
]
