from __future__ import annotations

from enum import StrEnum
from typing import Any

from backend.persistence.plugins.persistence_plugin_context import (
    PersistencePluginContext,
)
from backend.persistence.plugins.persistence_plugin_contract import (
    PersistencePluginContract,
)


class PersistencePluginState(StrEnum):
    CREATED = "created"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    STOPPED = "stopped"


class PersistencePluginRuntime:
    """
    Persistence-local plugin lifecycle and execution coordinator.

    Owns only plugin lifecycle state and execution admission.
    """

    VERSION = "1.0"

    def __init__(
        self,
        plugin: PersistencePluginContract,
        context: PersistencePluginContext,
    ) -> None:
        if not isinstance(
            plugin,
            PersistencePluginContract,
        ):
            raise TypeError(
                "persistence plugin contract required"
            )
        if not context.ready():
            raise RuntimeError(
                "persistence plugin context unavailable"
            )
        self.plugin = plugin
        self.context = context
        self._state = PersistencePluginState.CREATED

    def initialize(self) -> None:
        if self._state is not PersistencePluginState.CREATED:
            raise RuntimeError(
                "persistence plugin initialize boundary invalid"
            )
        self.plugin.initialize()
        self._state = PersistencePluginState.INITIALIZED

    def activate(self) -> None:
        if self._state is not PersistencePluginState.INITIALIZED:
            raise RuntimeError(
                "persistence plugin must initialize first"
            )
        try:
            self.plugin.activate()
        except Exception:
            self._state = PersistencePluginState.INITIALIZED
            raise
        self._state = PersistencePluginState.ACTIVE

    def stop(self) -> None:
        if self._state is PersistencePluginState.STOPPED:
            return
        self.plugin.stop()
        self._state = PersistencePluginState.STOPPED

    def execute(
        self,
        *,
        payload: dict[str, Any],
    ) -> Any:
        if not self.ready():
            raise RuntimeError(
                "persistence plugin runtime unavailable"
            )
        return self.plugin.execute(
            context=self.context,
            payload=payload,
        )

    def state(self) -> PersistencePluginState:
        return self._state

    def ready(self) -> bool:
        return (
            self._state is PersistencePluginState.ACTIVE
            and self.context.ready()
            and self.plugin.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "state": self._state.value,
            "ready": self.ready(),
            "plugin": self.plugin.name,
        }


__all__ = [
    "PersistencePluginRuntime",
    "PersistencePluginState",
]
