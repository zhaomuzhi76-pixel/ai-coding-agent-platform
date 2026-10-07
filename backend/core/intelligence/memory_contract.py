from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EngineeringMemoryRecordContract(Protocol):
    change: str
    result: str
    lesson: str

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


@runtime_checkable
class EngineeringMemoryServiceContract(Protocol):
    def remember(
        self,
        record: EngineeringMemoryRecordContract,
    ) -> None:
        ...

    def history(
        self,
    ) -> tuple[EngineeringMemoryRecordContract, ...]:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "EngineeringMemoryRecordContract",
    "EngineeringMemoryServiceContract",
]
