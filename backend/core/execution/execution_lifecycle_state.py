from __future__ import annotations

from dataclasses import dataclass, field

from backend.core.contracts.value import CoreValue

from backend.core.execution.execution_status import (
    ExecutionStatus,
)
from backend.core.contracts.timestamp import now_timestamp


@dataclass(slots=True)
class ExecutionLifecycleState:
    """
    Core-owned request-scoped execution lifecycle state.

    Owns:
        - execution identity
        - status storage
        - execution step
        - execution error
        - lifecycle timestamps

    Does not own:
        - transition rules
        - transition control
        - scheduling
        - execution
        - persistence
    """

    VERSION = "1.0"
    RESPONSIBILITY = ("execution_lifecycle_state",)

    task_id: str = ""

    _status: ExecutionStatus = field(
        default=ExecutionStatus.PENDING,
        init=False,
        repr=False,
    )

    step: int = 0
    error: str | None = None
    created_at: str = field(default_factory=now_timestamp)
    updated_at: str = field(default_factory=now_timestamp)

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str):
            raise TypeError("task_id must be str")

        if not isinstance(self.step, int):
            raise TypeError("step must be int")

        if self.step < 0:
            raise ValueError(
                "step cannot be negative"
            )

        if self.error is not None and not isinstance(
            self.error,
            str,
        ):
            raise TypeError(
                "error must be str or None"
            )

    @property
    def status(self) -> ExecutionStatus:
        return self._status

    def ready(self) -> bool:
        return bool(
            self.task_id.strip()
            and self.created_at
            and self.updated_at
            and isinstance(
                self._status,
                ExecutionStatus,
            )
            and self.step >= 0
        )

    def _set_status(
        self,
        status: ExecutionStatus,
    ) -> None:
        if not isinstance(
            status,
            ExecutionStatus,
        ):
            raise TypeError(
                "status must be ExecutionStatus"
            )

        self._status = status
        self.updated_at = now_timestamp()

    def update_step(
        self,
        step: int,
    ) -> None:
        if not isinstance(step, int):
            raise TypeError(
                "step must be int"
            )

        if step < 0:
            raise ValueError(
                "step cannot be negative"
            )

        self.step = step
        self.updated_at = now_timestamp()

    def set_error(
        self,
        error: str | None,
    ) -> None:
        if error is not None and not isinstance(
            error,
            str,
        ):
            raise TypeError(
                "error must be str or None"
            )

        self.error = error
        self.updated_at = now_timestamp()

    def snapshot(self) -> dict[str, CoreValue]:
        return {
            "task_id": self.task_id,
            "status": self._status.value,
            "step": self.step,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def dump(self) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "state": self.snapshot(),
        }


__all__ = [
    "ExecutionLifecycleState",
]
