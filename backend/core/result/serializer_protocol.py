from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import CoreValue


@runtime_checkable
class ResultSerializerProtocol(Protocol):
    def to_dict(
        self,
        value: CoreValue,
    ) -> dict[str, CoreValue]:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "ResultSerializerProtocol",
]
