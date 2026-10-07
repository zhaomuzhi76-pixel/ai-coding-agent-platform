from __future__ import annotations

from backend.core.context.context_state_protocol import (
    ContextStateProtocol,
)

from backend.core.contracts.value import (
    CoreValue,
)


class ContextStateCarrier:
    """
    Context state observation carrier.

    Owns:
        - state reference
        - state observation

    Does not own:
        - state mutation
        - lifecycle
        - persistence
        - execution
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "context_state_observation",
    )

    def __init__(
        self,
        state: ContextStateProtocol,
    ) -> None:

        if not isinstance(
            state,
            ContextStateProtocol,
        ):
            raise TypeError(
                "invalid context state"
            )

        self._state = state


    def ready(
        self,
    ) -> bool:

        return self._state.ready()


    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "state": self._state.dump(),
        }


__all__ = [
    "ContextStateCarrier",
]
