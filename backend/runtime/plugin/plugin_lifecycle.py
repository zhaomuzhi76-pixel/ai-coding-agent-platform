from __future__ import annotations

from enum import Enum


class RuntimePluginLifecycleState(Enum):
    CREATED = "created"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"


class RuntimePluginLifecycle:
    """
    Runtime plugin lifecycle state machine.

    Responsibility:
        - own lifecycle states
        - validate lifecycle transitions
        - support transactional rollback

    Not Responsible:
        - plugin discovery
        - plugin loading
        - capability registration
        - plugin business logic
    """

    VERSION = "4.0"

    TRANSITIONS = {
        RuntimePluginLifecycleState.CREATED: (
            RuntimePluginLifecycleState.INSTALLED,
            RuntimePluginLifecycleState.UNLOADED,
        ),
        RuntimePluginLifecycleState.INSTALLED: (
            RuntimePluginLifecycleState.ENABLED,
            RuntimePluginLifecycleState.UNLOADED,
        ),
        RuntimePluginLifecycleState.ENABLED: (
            RuntimePluginLifecycleState.DISABLED,
        ),
        RuntimePluginLifecycleState.DISABLED: (
            RuntimePluginLifecycleState.ENABLED,
            RuntimePluginLifecycleState.UNLOADED,
        ),
        RuntimePluginLifecycleState.UNLOADED: (),
    }

    def __init__(self) -> None:
        self._states: dict[
            str,
            RuntimePluginLifecycleState,
        ] = {}

    def register(
        self,
        plugin_name: str,
    ) -> None:
        self._validate_name(plugin_name)

        if plugin_name in self._states:
            raise ValueError(
                "plugin already registered"
            )

        self._states[plugin_name] = (
            RuntimePluginLifecycleState.CREATED
        )

    def install(
        self,
        plugin_name: str,
    ) -> None:
        self.transition(
            plugin_name,
            RuntimePluginLifecycleState.INSTALLED,
        )

    def enable(
        self,
        plugin_name: str,
    ) -> None:
        self.transition(
            plugin_name,
            RuntimePluginLifecycleState.ENABLED,
        )

    def disable(
        self,
        plugin_name: str,
    ) -> None:
        self.transition(
            plugin_name,
            RuntimePluginLifecycleState.DISABLED,
        )

    def unload(
        self,
        plugin_name: str,
    ) -> None:
        self.transition(
            plugin_name,
            RuntimePluginLifecycleState.UNLOADED,
        )

    def transition(
        self,
        plugin_name: str,
        target: RuntimePluginLifecycleState,
    ) -> None:
        current = self.get_state(plugin_name)

        if target not in self.TRANSITIONS[current]:
            raise RuntimeError(
                "invalid transition "
                f"{current.value}->{target.value}"
            )

        self._states[plugin_name] = target

    def get_state(
        self,
        plugin_name: str,
    ) -> RuntimePluginLifecycleState:
        self._validate_name(plugin_name)

        try:
            return self._states[plugin_name]
        except KeyError as error:
            raise KeyError(
                "plugin not registered"
            ) from error

    def registered(
        self,
        plugin_name: str,
    ) -> bool:
        return plugin_name in self._states

    def ready(self) -> bool:
        return all(
            bool(name)
            for name in self._states
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "states": {
                name: state.value
                for name, state
                in self._states.items()
            },
            "ready": self.ready(),
        }

    @staticmethod
    def _validate_name(
        plugin_name: str,
    ) -> None:
        if not isinstance(plugin_name, str):
            raise TypeError(
                "plugin name must str"
            )

        if not plugin_name.strip():
            raise ValueError(
                "plugin name required"
            )


__all__ = [
    "RuntimePluginLifecycle",
    "RuntimePluginLifecycleState",
]
