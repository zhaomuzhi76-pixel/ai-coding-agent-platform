from __future__ import annotations

from enum import StrEnum


class ApplicationCapabilityState(StrEnum):
    CREATED = "created"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"


class ApplicationCapabilityLifecycle:
    """
    Application capability lifecycle state machine.
    """

    VERSION = "2.1"

    TRANSITIONS = {
        ApplicationCapabilityState.CREATED: (
            ApplicationCapabilityState.INSTALLED,
        ),
        ApplicationCapabilityState.INSTALLED: (
            ApplicationCapabilityState.ENABLED,
        ),
        ApplicationCapabilityState.ENABLED: (
            ApplicationCapabilityState.DISABLED,
        ),
        ApplicationCapabilityState.DISABLED: (
            ApplicationCapabilityState.ENABLED,
            ApplicationCapabilityState.UNLOADED,
        ),
        ApplicationCapabilityState.UNLOADED: (),
    }

    def __init__(self) -> None:
        self._states: dict[
            str,
            ApplicationCapabilityState,
        ] = {}

    def register(
        self,
        name: str,
    ) -> None:
        if not name:
            raise ValueError(
                "capability name required"
            )

        if name in self._states:
            raise ValueError(
                "capability already registered"
            )

        self._states[name] = (
            ApplicationCapabilityState.CREATED
        )

    def unregister(
        self,
        name: str,
    ) -> None:
        state = self.state(name)

        if state is not ApplicationCapabilityState.CREATED:
            raise RuntimeError(
                "only created capability can be unregistered"
            )

        del self._states[name]

    def registered(
        self,
        name: str,
    ) -> bool:
        return name in self._states

    def transition(
        self,
        name: str,
        target: ApplicationCapabilityState,
    ) -> None:
        current = self.state(name)

        if target not in self.TRANSITIONS[current]:
            raise RuntimeError(
                "invalid capability transition: "
                f"{current.value}->{target.value}"
            )

        self._states[name] = target

    def install(
        self,
        name: str,
    ) -> None:
        self.transition(
            name,
            ApplicationCapabilityState.INSTALLED,
        )

    def enable(
        self,
        name: str,
    ) -> None:
        self.transition(
            name,
            ApplicationCapabilityState.ENABLED,
        )

    def disable(
        self,
        name: str,
    ) -> None:
        self.transition(
            name,
            ApplicationCapabilityState.DISABLED,
        )

    def unload(
        self,
        name: str,
    ) -> None:
        self.transition(
            name,
            ApplicationCapabilityState.UNLOADED,
        )

    def state(
        self,
        name: str,
    ) -> ApplicationCapabilityState:
        try:
            return self._states[name]
        except KeyError as error:
            raise KeyError(
                f"capability not registered: {name}"
            ) from error

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "states": {
                name: state.value
                for name, state in self._states.items()
            },
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityLifecycle",
    "ApplicationCapabilityState",
]
