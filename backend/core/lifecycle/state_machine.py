from __future__ import annotations

from backend.core.lifecycle.state import (
    LifecycleState,
)


class LifecycleStateMachine:
    """
    Lifecycle transition authority.

    Owns:
        - lifecycle transition rules
        - transition validation

    Does not own:
        - component registry
        - history storage
        - component execution
    """

    VERSION = "1.0"

    TRANSITIONS = {
        LifecycleState.CREATED: frozenset(
            {
                LifecycleState.INITIALIZED,
            }
        ),
        LifecycleState.INITIALIZED: frozenset(
            {
                LifecycleState.RUNNING,
                LifecycleState.STOPPED,
                LifecycleState.DESTROYED,
            }
        ),
        LifecycleState.RUNNING: frozenset(
            {
                LifecycleState.STOPPED,
            }
        ),
        LifecycleState.STOPPED: frozenset(
            {
                LifecycleState.RUNNING,
                LifecycleState.DESTROYED,
            }
        ),
        LifecycleState.DESTROYED: frozenset(),
    }

    def can_transition(
        self,
        current: LifecycleState,
        target: LifecycleState,
    ) -> bool:
        return target in self.TRANSITIONS[current]

    def validate(
        self,
        current: LifecycleState,
        target: LifecycleState,
    ) -> None:
        if not self.can_transition(
            current,
            target,
        ):
            raise RuntimeError(
                f"invalid lifecycle transition: "
                f"{current.value}->{target.value}"
            )

    def ready(
        self,
    ) -> bool:
        return isinstance(
            self.TRANSITIONS,
            dict,
        )


__all__ = [
    "LifecycleStateMachine",
]
