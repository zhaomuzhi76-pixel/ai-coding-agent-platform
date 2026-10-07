from __future__ import annotations

from backend.core.execution.execution_status import (
    ExecutionStatus,
)


class ExecutionStateMachine:
    """
    Execution status transition owner.

    Owns:
        - legal status transition rules

    Does not own:
        - state storage
        - execution data
        - scheduling
        - runtime execution
    """

    VERSION = "1.0"

    TRANSITIONS = {
        ExecutionStatus.PENDING: frozenset(
            {
                ExecutionStatus.RUNNING,
                ExecutionStatus.FAILED,
            }
        ),
        ExecutionStatus.RUNNING: frozenset(
            {
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
            }
        ),
        ExecutionStatus.COMPLETED: frozenset(),
        ExecutionStatus.FAILED: frozenset(),
    }

    def can_transition(
        self,
        current: ExecutionStatus,
        target: ExecutionStatus,
    ) -> bool:
        if not isinstance(
            current,
            ExecutionStatus,
        ):
            raise TypeError(
                "current status required"
            )

        if not isinstance(
            target,
            ExecutionStatus,
        ):
            raise TypeError(
                "target status required"
            )

        return target in self.TRANSITIONS[current]

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.TRANSITIONS,
                dict,
            )
            and all(
                isinstance(
                    item,
                    frozenset,
                )
                for item
                in self.TRANSITIONS.values()
            )
        )


__all__ = [
    "ExecutionStateMachine",
]
