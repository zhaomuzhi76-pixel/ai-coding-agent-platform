from __future__ import annotations

from backend.runtime.execution.runtime_node_state import (
    RuntimeNodeState,
)


class RuntimeStateTransition:
    """
    Runtime node lifecycle transition guard.

    Responsibility:
        - define valid runtime node transitions
        - allow idempotent terminal commits
        - reject illegal lifecycle jumps

    Not Responsible:
        - execution
        - scheduling
        - persistence
        - retry
    """

    VERSION = "3.0"

    _TRANSITIONS = {
        RuntimeNodeState.CREATED: {
            RuntimeNodeState.READY,
            RuntimeNodeState.CANCELLED,
        },
        RuntimeNodeState.READY: {
            RuntimeNodeState.RUNNING,
            RuntimeNodeState.CANCELLED,
        },
        RuntimeNodeState.RUNNING: {
            RuntimeNodeState.SUCCESS,
            RuntimeNodeState.FAILED,
            RuntimeNodeState.CANCELLED,
        },
        RuntimeNodeState.FAILED: {
            RuntimeNodeState.RUNNING,
            RuntimeNodeState.CANCELLED,
            RuntimeNodeState.FAILED,
        },
        RuntimeNodeState.SUCCESS: {
            RuntimeNodeState.SUCCESS,
        },
        RuntimeNodeState.CANCELLED: {
            RuntimeNodeState.CANCELLED,
        },
    }

    def can_transition(
        self,
        current: RuntimeNodeState,
        target: RuntimeNodeState,
    ) -> bool:
        if not isinstance(
            current,
            RuntimeNodeState,
        ):
            return False

        if not isinstance(
            target,
            RuntimeNodeState,
        ):
            return False

        return target in self._TRANSITIONS.get(
            current,
            set(),
        )

    def validate(
        self,
        current: RuntimeNodeState,
        target: RuntimeNodeState,
    ) -> None:
        if not isinstance(
            current,
            RuntimeNodeState,
        ):
            raise TypeError(
                "current must RuntimeNodeState"
            )

        if not isinstance(
            target,
            RuntimeNodeState,
        ):
            raise TypeError(
                "target must RuntimeNodeState"
            )

        if not self.can_transition(
            current,
            target,
        ):
            raise RuntimeError(
                "invalid runtime state transition: "
                f"{current.value} -> {target.value}"
            )

    def ready(
        self,
    ) -> bool:
        return bool(
            self._TRANSITIONS
        )


__all__ = [
    "RuntimeStateTransition",
]
