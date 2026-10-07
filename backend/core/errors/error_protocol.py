from __future__ import annotations

from backend.core.contracts.value import CoreValue

from typing import Mapping, Protocol, runtime_checkable

from backend.core.errors.error_code import (
    CoreErrorCode,
)


@runtime_checkable
class CoreErrorProtocol(Protocol):
    """
    Canonical framework error contract.

    Ownership:
        - define normalized error semantics

    Not Responsible:
        - transport delivery
        - exception construction
        - execution policy
    """

    code: CoreErrorCode
    message: str
    metadata: Mapping[str, CoreValue]

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, CoreValue]:
        ...


__all__ = [
    "CoreErrorProtocol",
]
