from __future__ import annotations

from backend.runtime.plugin.plugin_lifecycle import (
    RuntimePluginLifecycle,
    RuntimePluginLifecycleState,
)


class RuntimePluginLoadTransaction:
    """
    Plugin load transaction coordinator.

    Responsibility:
        - coordinate lifecycle hooks
        - commit lifecycle state only after hook success
        - rollback partially loaded plugins

    Not Responsible:
        - discovery
        - dependency resolution
        - capability implementation
        - plugin registry ownership
    """

    VERSION = "2.0"

    def __init__(
        self,
        lifecycle: RuntimePluginLifecycle,
    ) -> None:
        if lifecycle is None:
            raise ValueError(
                "lifecycle required"
            )

        self.lifecycle = lifecycle

    def load(
        self,
        *,
        plugin_name: str,
        plugin: object,
    ) -> object:
        if not plugin_name:
            raise ValueError(
                "plugin name required"
            )

        if plugin is None:
            raise ValueError(
                "plugin required"
            )

        self.lifecycle.register(plugin_name)

        try:
            self._invoke(
                plugin,
                "install",
            )
            self.lifecycle.install(plugin_name)

            self._invoke(
                plugin,
                "enable",
            )
            self.lifecycle.enable(plugin_name)

            return plugin
        except Exception:
            self.rollback(
                plugin_name=plugin_name,
                plugin=plugin,
            )
            raise

    def rollback(
        self,
        *,
        plugin_name: str,
        plugin: object,
    ) -> None:
        if not self.lifecycle.registered(
            plugin_name
        ):
            return

        state = self.lifecycle.get_state(
            plugin_name
        )

        try:
            if state is RuntimePluginLifecycleState.ENABLED:
                self._invoke(
                    plugin,
                    "disable",
                )
                self.lifecycle.disable(plugin_name)
                state = RuntimePluginLifecycleState.DISABLED

            if state in (
                RuntimePluginLifecycleState.CREATED,
                RuntimePluginLifecycleState.INSTALLED,
                RuntimePluginLifecycleState.DISABLED,
            ):
                self._invoke(
                    plugin,
                    "unload",
                )
                self.lifecycle.unload(plugin_name)
        except Exception:
            return

    def ready(self) -> bool:
        return self.lifecycle.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _invoke(
        plugin: object,
        method_name: str,
    ) -> None:
        method = getattr(
            plugin,
            method_name,
            None,
        )

        if method is None:
            return

        if not callable(method):
            raise TypeError(
                "plugin hook not callable: "
                f"{method_name}"
            )

        method()


__all__ = [
    "RuntimePluginLoadTransaction",
]
