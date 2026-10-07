from __future__ import annotations

from backend.core.intelligence.memory_contract import (
    EngineeringMemoryRecordContract,
)


class RuntimeEngineeringMemoryStore:
    def __init__(self) -> None:
        self._records: list[
            EngineeringMemoryRecordContract
        ] = []

    def save(
        self,
        record: EngineeringMemoryRecordContract,
    ) -> None:
        if not record.ready():
            return

        self._records.append(record)

    def all(
        self,
    ) -> tuple[EngineeringMemoryRecordContract, ...]:
        return tuple(self._records)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "record_count": len(self._records),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeEngineeringMemoryStore",
]
