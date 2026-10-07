from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)


@runtime_checkable
class CodeFindingProtocol(
    Protocol,
):
    """
    Core-owned code intelligence finding boundary.

    A finding is a domain object owned by the inspection
    implementation. Core only requires a serializable snapshot.
    """

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "CodeFindingProtocol",
]
