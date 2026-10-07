from __future__ import annotations

from typing import Any

from backend.utils.time import now_iso

class RepairHistory:
    """
    Repair attempt history owner.

    Owns only attempt records and history queries.
    """

    VERSION = "4.0"
    RESPONSIBILITY = (
        "industrial_repair_attempt_history",
    )

    def __init__(self) -> None:
        self.records: list[
            dict[str, Any]
        ] = []

    def append(
        self,
        *,
        attempt: int,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        if attempt <= 0:
            raise ValueError(
                "attempt must be positive"
            )

        if not isinstance(result, dict):
            raise TypeError(
                "repair result must dict"
            )

        entry = {
            "attempt": attempt,
            "success": bool(
                result.get("success", False)
            ),
            "result": result,
            "created_at": now_iso(),
        }

        self.records.append(entry)
        return dict(entry)

    def list(
        self,
    ) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in self.records
        ]

    def clear(self) -> None:
        self.records.clear()

    def count(self) -> int:
        return len(self.records)

    def success_count(self) -> int:
        return sum(
            bool(
                item.get(
                    "success",
                    False,
                )
            )
            for item in self.records
        )

    def failure_count(self) -> int:
        return (
            self.count()
            - self.success_count()
        )

    def latest(
        self,
    ) -> dict[str, Any] | None:
        if not self.records:
            return None
        return dict(self.records[-1])

    def ready(self) -> bool:
        return isinstance(
            self.records,
            list,
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "count": self.count(),
            "success": self.success_count(),
            "failure": self.failure_count(),
            "records": self.list(),
        }

__all__ = [
    "RepairHistory",
]
