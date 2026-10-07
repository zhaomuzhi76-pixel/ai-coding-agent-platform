from __future__ import annotations

from enum import Enum


class ApplicationPluginState(str, Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    FAILED = "failed"
    STOPPED = "stopped"


class ApplicationPluginLifecycle:
    VERSION = "1.1"

    def __init__(self) -> None:
        self._state = ApplicationPluginState.CREATED

    def initialize(self) -> None:
        if self._state is not ApplicationPluginState.CREATED:
            raise RuntimeError(
                "plugin must initialize from created state"
            )
        self._state = ApplicationPluginState.INITIALIZED

    def activate(self) -> None:
        self.require(
            ApplicationPluginState.INITIALIZED
        )
        self._state = ApplicationPluginState.ACTIVE

    def fail(self) -> None:
        self._state = ApplicationPluginState.FAILED

    def rollback(
        self,
        state: ApplicationPluginState,
    ) -> None:
        if self._state is not ApplicationPluginState.FAILED:
            raise RuntimeError(
                "plugin rollback requires failed state"
            )
        self._state = state

    def stop(self) -> None:
        self._state = ApplicationPluginState.STOPPED

    def require(
        self,
        state: ApplicationPluginState,
    ) -> None:
        if self._state is not state:
            raise RuntimeError(
                "invalid plugin lifecycle state: "
                f"expected={state.value} "
                f"actual={self._state.value}"
            )

    def state(self) -> ApplicationPluginState:
        return self._state


__all__ = [
    "ApplicationPluginLifecycle",
    "ApplicationPluginState",
]
