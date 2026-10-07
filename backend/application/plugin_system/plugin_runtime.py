from __future__ import annotations

from backend.application.plugin_system.plugin_context import (
    ApplicationPluginContext,
)
from backend.application.plugin_system.plugin_contract import (
    ApplicationPluginContract,
)
from backend.application.plugin_system.plugin_lifecycle import (
    ApplicationPluginLifecycle,
    ApplicationPluginState,
)


class ApplicationPluginRuntime:
    """
    Plugin runtime coordinator.

    Owns:
        - plugin lifecycle coordination

    Does not own:
        - plugin discovery
        - plugin creation
        - business execution
    """

    VERSION = "1.1"

    def __init__(
        self,
        plugin: ApplicationPluginContract,
        context: ApplicationPluginContext,
    ) -> None:
        if not isinstance(plugin, ApplicationPluginContract):
            raise TypeError(
                "plugin must implement ApplicationPluginContract"
            )
        if not isinstance(context, ApplicationPluginContext):
            raise TypeError(
                "plugin context required"
            )

        self.plugin = plugin
        self.context = context
        self.lifecycle = ApplicationPluginLifecycle()

    def initialize(self) -> None:
        self.plugin.initialize()
        self.lifecycle.initialize()

    def activate(self) -> None:
        self.lifecycle.require(
            ApplicationPluginState.INITIALIZED
        )

        try:
            self.plugin.activate()
        except Exception:
            self.lifecycle.fail()
            self.lifecycle.rollback(
                ApplicationPluginState.INITIALIZED
            )
            raise

        self.lifecycle.activate()

    def stop(self) -> None:
        self.plugin.stop()
        self.lifecycle.stop()

    def execute(
        self,
        *,
        payload: dict[str, object],
    ) -> object:
        if not self.ready():
            raise RuntimeError(
                "plugin runtime unavailable"
            )

        return self.plugin.execute(
            context=self.context,
            payload=payload,
        )

    def ready(self) -> bool:
        return (
            self.context.ready()
            and self.plugin.ready()
            and self.lifecycle.state()
            is ApplicationPluginState.ACTIVE
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "state": self.lifecycle.state().value,
            "plugin": self.plugin.name,
        }


__all__ = [
    "ApplicationPluginRuntime",
]
