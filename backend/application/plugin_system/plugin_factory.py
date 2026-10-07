from __future__ import annotations

from typing import Callable

from backend.application.plugin_system.plugin_contract import (
    ApplicationPluginContract,
)


class ApplicationPluginFactory:
    """
    Plugin construction boundary.

    Owns:
        - plugin instance creation

    Does not own:
        - registration
        - execution
        - lifecycle
    """

    VERSION = "1.0"

    def create(
        self,
        builder: Callable[
            [],
            ApplicationPluginContract,
        ],
    ) -> ApplicationPluginContract:
        plugin = builder()

        if not isinstance(
            plugin,
            ApplicationPluginContract,
        ):
            raise TypeError(
                "plugin factory returned invalid plugin"
            )

        return plugin

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPluginFactory",
]
