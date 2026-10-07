from __future__ import annotations

from typing import Any

from backend.core.execution.execution_status import (
    ExecutionStatus,
)
from backend.runtime.state.execution_lifecycle_rules import (
    ExecutionLifecycleRules,
)
from backend.core.execution.execution_lifecycle_state import (
    ExecutionLifecycleState,
)


class ExecutionLifecycleMachine:
    """
    Execution lifecycle transition controller.

    Responsibility:
        - validate lifecycle transition
        - mutate injected lifecycle state
        - expose lifecycle observation

    State write boundary:
        - state owns its private status storage
        - machine is the only lifecycle transition controller

    Not Responsible:
        - execution state construction
        - execution
        - DAG node state
        - scheduling
        - persistence
        - event dispatch
    """

    VERSION = "10.0"

    RESPONSIBILITY = (
        "execution_lifecycle_transition_control",
    )

    def __init__(
        self,
        state: ExecutionLifecycleState,
    ) -> None:
        if not isinstance(
            state,
            ExecutionLifecycleState,
        ):
            raise TypeError(
                "state must be ExecutionLifecycleState"
            )

        self.state = state
        self.transition_count = 0
        self.last_transition: (
            tuple[str, str] | None
        ) = None

    def transition(
        self,
        target: ExecutionStatus,
    ) -> None:
        if not isinstance(
            target,
            ExecutionStatus,
        ):
            raise TypeError(
                "target must be ExecutionStatus"
            )

        current = self.current()

        if not ExecutionLifecycleRules.can_transition(
            current,
            target,
        ):
            raise RuntimeError(
                f"invalid transition "
                f"{current.value}->{target.value}"
            )

        self.state._set_status(
            target
        )

        self.transition_count += 1
        self.last_transition = (
            current.value,
            target.value,
        )

    def start(
        self,
    ) -> None:
        self.transition(
            ExecutionStatus.RUNNING
        )

    def success(
        self,
    ) -> None:
        self.transition(
            ExecutionStatus.COMPLETED
        )

    def fail(
        self,
        error: str | None = None,
    ) -> None:
        self.state.set_error(
            error
        )
        self.transition(
            ExecutionStatus.FAILED
        )

    def next_step(
        self,
    ) -> int:
        next_step = (
            self.state.step + 1
        )

        self.state.update_step(
            next_step
        )

        return next_step

    def current(
        self,
    ) -> ExecutionStatus:
        return self.state.status

    def ready(
        self,
    ) -> bool:
        return self.state.ready()

    def snapshot(
        self,
    ) -> dict[str, Any]:
        return {
            "state": self.current().value,
            "step": self.state.step,
            "transition_count": (
                self.transition_count
            ),
            "last_transition": (
                self.last_transition
            ),
        }

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": (
                self.RESPONSIBILITY
            ),
            "ready": self.ready(),
            "snapshot": self.snapshot(),
        }


__all__ = [
    "ExecutionLifecycleMachine",
]
