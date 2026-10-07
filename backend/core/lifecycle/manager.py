from __future__ import annotations

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.lifecycle.event import (
    LifecycleEvent,
)

from backend.core.lifecycle.lifecycle_history import (
    LifecycleHistory,
)

from backend.core.lifecycle.state import (
    LifecycleState,
)

from backend.core.lifecycle.state_machine import (
    LifecycleStateMachine,
)


class LifecycleManager:
    """
    Canonical lifecycle coordinator.

    Owns:
        - component lifecycle state
        - transition coordination
        - lifecycle history binding

    Does not own:
        - component execution hooks
        - dependency creation
        - business logic
    """

    VERSION = "5.0"

    def __init__(
        self,
    ) -> None:
        self._states: dict[
            str,
            LifecycleState,
        ] = {}

        self._history = LifecycleHistory()

        self._machine = LifecycleStateMachine()

    def register(
        self,
        component_id: str,
    ) -> None:
        normalized_id = self._validate_id(
            component_id
        )

        if normalized_id in self._states:
            raise ValueError(
                f"component already registered: {normalized_id}"
            )

        self._states[
            normalized_id
        ] = LifecycleState.CREATED

        self._history.record(
            LifecycleState.CREATED.value
        )

    def initialize(
        self,
        component_id: str,
    ) -> LifecycleEvent:
        return self._transition(
            component_id,
            LifecycleState.INITIALIZED,
        )

    def start(
        self,
        component_id: str,
    ) -> LifecycleEvent:
        return self._transition(
            component_id,
            LifecycleState.RUNNING,
        )

    def stop(
        self,
        component_id: str,
    ) -> LifecycleEvent:
        return self._transition(
            component_id,
            LifecycleState.STOPPED,
        )

    def destroy(
        self,
        component_id: str,
    ) -> LifecycleEvent:
        return self._transition(
            component_id,
            LifecycleState.DESTROYED,
        )

    def state(
        self,
        component_id: str,
    ) -> LifecycleState:
        normalized_id = self._validate_id(
            component_id
        )

        if normalized_id not in self._states:
            raise KeyError(
                normalized_id
            )

        return self._states[
            normalized_id
        ]

    @property
    def history(
        self,
    ) -> LifecycleHistory:
        return self._history

    def ready(
        self,
    ) -> bool:
        return (
            self._machine.ready()
            and isinstance(
                self._history,
                LifecycleHistory,
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "states": {
                key: value.value
                for key, value
                in self._states.items()
            },
            "history": self._history.dump(),
            "ready": self.ready(),
        }

    def _transition(
        self,
        component_id: str,
        target: LifecycleState,
    ) -> LifecycleEvent:
        normalized_id = self._validate_id(
            component_id
        )

        current = self.state(
            normalized_id
        )

        self._machine.validate(
            current,
            target,
        )

        self._states[
            normalized_id
        ] = target

        self._history.record(
            target.value
        )

        return LifecycleEvent(
            component_id=normalized_id,
            component_name=normalized_id,
            state=target,
        )

    @staticmethod
    def _validate_id(
        component_id: str,
    ) -> str:
        if not isinstance(
            component_id,
            str,
        ):
            raise TypeError(
                "component id must str"
            )

        value = component_id.strip()

        if not value:
            raise ValueError(
                "component id required"
            )

        return value


__all__ = [
    "LifecycleManager",
]
