from __future__ import annotations

from enum import Enum
from typing import Final

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.execution.execution_status_contract import (
    ExecutionStatusSnapshot,
)


VERSION: Final = "2.0"


class ExecutionStatus(
    str,
    Enum,
):
    """
    Execution runtime status definition.

    Responsibility:

        - define execution status values
        - provide status serialization

    Not Responsible:

        - lifecycle transition
        - scheduling
        - workflow orchestration
        - execution control
        - runtime state storage
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    def snapshot(
        self,
    ) -> ExecutionStatusSnapshot:

        return {
            "value": self.value,
        }

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": "ExecutionStatus",
            "version": VERSION,
            "status": self.value,
        }


__all__ = [
    "ExecutionStatus",
]
