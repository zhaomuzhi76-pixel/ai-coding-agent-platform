from __future__ import annotations

from typing import Any

from backend.application.plugin_system.plugin_context import (
    ApplicationPluginContext,
)
from backend.application.plugin_system.plugin_contract import (
    ApplicationPluginContract,
)


class ApplicationPluginExecutor:
    """
    Plugin execution boundary.

    Owns:
        - invoke plugin execution

    Does not own:
        - plugin discovery
        - plugin creation
        - lifecycle management
    """

    VERSION = "1.0"

    def execute(
        self,
        *,
        plugin: ApplicationPluginContract,
        context: ApplicationPluginContext,
        payload: dict[str, Any],
    ) -> Any:
        if not context.ready():
            raise RuntimeError(
                "plugin context unavailable"
            )

        if not plugin.ready():
            raise RuntimeError(
                "plugin unavailable"
            )

        return plugin.execute(
            context=context,
            payload=payload,
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPluginExecutor",
]
