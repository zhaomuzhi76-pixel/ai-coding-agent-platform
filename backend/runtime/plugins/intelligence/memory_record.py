from __future__ import annotations

from dataclasses import dataclass

from backend.core.intelligence.memory_contract import (
    EngineeringMemoryRecordContract,
)


@dataclass(frozen=True)
class RuntimeEngineeringMemoryRecord(
    EngineeringMemoryRecordContract,
):
    change: str
    result: str
    lesson: str

    def ready(self) -> bool:
        return bool(
            self.change.strip()
            and self.result.strip()
        )

    def dump(self) -> dict[str, object]:
        return {
            "change": self.change,
            "result": self.result,
            "lesson": self.lesson,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeEngineeringMemoryRecord",
]
