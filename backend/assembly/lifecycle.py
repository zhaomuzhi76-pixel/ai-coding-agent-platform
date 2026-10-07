from __future__ import annotations

from enum import Enum


class AssemblyLifecycleState(Enum):
    CREATED = "created"
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"


class AssemblyLifecycle:
    """
    System assembly lifecycle boundary.
    """

    VERSION = "1.0"

    TRANSITIONS = {
        AssemblyLifecycleState.CREATED: (
            AssemblyLifecycleState.STARTED,
            AssemblyLifecycleState.FAILED,
        ),
        AssemblyLifecycleState.STARTED: (
            AssemblyLifecycleState.STOPPED,
            AssemblyLifecycleState.FAILED,
        ),
        AssemblyLifecycleState.STOPPED: (
            AssemblyLifecycleState.STARTED,
        ),
        AssemblyLifecycleState.FAILED: (
            AssemblyLifecycleState.STARTED,
        ),
    }

    def __init__(self) -> None:
        self._state = AssemblyLifecycleState.CREATED

    @property
    def state(self) -> AssemblyLifecycleState:
        return self._state

    def transition(
        self,
        target: AssemblyLifecycleState,
    ) -> None:
        if target not in self.TRANSITIONS[self._state]:
            raise RuntimeError(
                f"invalid assembly transition: "
                f"{self._state.value}->{target.value}"
            )
        self._state = target

    def start(self) -> None:
        self.transition(
            AssemblyLifecycleState.STARTED
        )

    def stop(self) -> None:
        self.transition(
            AssemblyLifecycleState.STOPPED
        )

    def fail(self) -> None:
        self.transition(
            AssemblyLifecycleState.FAILED
        )

    def ready(self) -> bool:
        return self._state is not AssemblyLifecycleState.FAILED

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "state": self._state.value,
            "ready": self.ready(),
        }


__all__ = [
    "AssemblyLifecycle",
    "AssemblyLifecycleState",
]
