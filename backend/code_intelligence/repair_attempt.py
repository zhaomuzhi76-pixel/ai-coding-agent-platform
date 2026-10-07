from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class RepairAttemptContext:
    """
    Immutable-style context describing one repair attempt.

    Owns attempt metadata and derived execution context only.
    """

    attempt: int
    task: str
    files: list[str]
    base_context: dict[str, Any] = field(
        default_factory=dict
    )

    def build(self) -> dict[str, Any]:
        context = dict(self.base_context)
        context["repair_attempt"] = self.attempt
        context["repair_task"] = self.task
        context["repair_files"] = list(self.files)
        return context

    def ready(self) -> bool:
        return (
            self.attempt > 0
            and bool(self.task)
            and bool(self.files)
        )

    def dump(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "task": self.task,
            "files": list(self.files),
            "context": dict(self.base_context),
            "ready": self.ready(),
        }

__all__ = [
    "RepairAttemptContext",
]
