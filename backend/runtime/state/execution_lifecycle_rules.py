from __future__ import annotations

from backend.core.execution.execution_status import (
    ExecutionStatus,
)


class ExecutionLifecycleRules:
    """
    Execution lifecycle transition rules.

    Responsibility:
        - define allowed execution states
        - define state transition rules
        - validate transition permission

    Not Responsible:
        - state mutation
        - execution runtime data
        - event dispatch
        - persistence
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "execution_lifecycle_rules",
    )

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

    @classmethod
    def can_transition(
        cls,
        current: ExecutionStatus,
        target: ExecutionStatus,
    ) -> bool:

        return target in cls.TRANSITIONS.get(
            current,
            frozenset(),
        )

    @classmethod
    def validate_state(
        cls,
        state: ExecutionStatus,
    ) -> None:

        if state not in cls.TRANSITIONS:
            raise ValueError(
                f"unknown execution state: {state}"
            )

    @classmethod
    def ready(
        cls,
    ) -> bool:

        return bool(
            cls.TRANSITIONS
        )

    @classmethod
    def dump(
        cls,
    ) -> dict[str, object]:

        return {
            "name": "ExecutionLifecycleRules",
            "version": cls.VERSION,
            "responsibility": cls.RESPONSIBILITY,
            "ready": cls.ready(),
            "states": [
                state.value
                for state in cls.TRANSITIONS
            ],
        }


__all__ = [
    "ExecutionLifecycleRules",
]
