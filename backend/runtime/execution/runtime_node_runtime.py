from __future__ import annotations

from dataclasses import dataclass, field

from backend.runtime.execution.runtime_node_state import (
    RuntimeNodeState,
    is_finished,
)
from backend.runtime.execution.runtime_state_transition import (
    RuntimeStateTransition,
)


@dataclass
class RuntimeNodeRuntime:
    """
    Runtime state holder for one execution node.

    Responsibility:
        - own one runtime node state
        - enforce state transitions
        - expose readiness and terminal-state observation

    Not Responsible:
        - execution
        - scheduling
        - graph construction
        - persistence
    """

    VERSION = "4.0"

    node_id: str
    _state: RuntimeNodeState = field(
        default=RuntimeNodeState.CREATED,
        repr=False,
    )

    def __post_init__(
        self,
    ) -> None:
        if not isinstance(
            self.node_id,
            str,
        ) or not self.node_id.strip():
            raise ValueError(
                "node_id required"
            )

        if not isinstance(
            self._state,
            RuntimeNodeState,
        ):
            raise TypeError(
                "state must RuntimeNodeState"
            )

        self.node_id = self.node_id.strip()

        self._transition_guard = (
            RuntimeStateTransition()
        )

    @property
    def state(
        self,
    ) -> RuntimeNodeState:
        return self._state

    def transition(
        self,
        target: RuntimeNodeState,
    ) -> None:
        if not isinstance(
            target,
            RuntimeNodeState,
        ):
            raise TypeError(
                "target must RuntimeNodeState"
            )

        current = self._state

        self._transition_guard.validate(
            current,
            target,
        )

        self._set_state(
            target
        )

    def _set_state(
        self,
        target: RuntimeNodeState,
    ) -> None:
        if not isinstance(
            target,
            RuntimeNodeState,
        ):
            raise TypeError(
                "target must RuntimeNodeState"
            )

        self._state = target

    def ready(
        self,
    ) -> bool:
        return bool(
            self.node_id
            and isinstance(
                self._state,
                RuntimeNodeState,
            )
        )

    @property
    def finished(
        self,
    ) -> bool:
        return is_finished(
            self._state
        )

    @property
    def failed(
        self,
    ) -> bool:
        return (
            self._state
            == RuntimeNodeState.FAILED
        )

    def snapshot(
        self,
    ) -> tuple[str, str]:
        return (
            self.node_id,
            self._state.value,
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": "RuntimeNodeRuntime",
            "version": self.VERSION,
            "ready": self.ready(),
            "node_id": self.node_id,
            "state": self._state.value,
            "finished": self.finished,
            "failed": self.failed,
        }


__all__ = [
    "RuntimeNodeRuntime",
]
