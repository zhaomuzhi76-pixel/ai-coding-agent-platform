from __future__ import annotations

from backend.application.plugin_system.plugin_contract import (
    ApplicationPluginContract,
)
from backend.application.plugin_system.plugin_descriptor import (
    ApplicationPluginDescriptor,
)
from backend.application.plugin_system.plugin_registry import (
    ApplicationPluginRegistry,
)


class ApplicationPluginLoader:
    """
    Plugin loading boundary.

    Owns:
        - resolve plugin from registry

    Does not own:
        - plugin creation
        - lifecycle
        - execution
    """

    VERSION = "1.0"

    def __init__(
        self,
        registry: ApplicationPluginRegistry,
    ) -> None:
        self.registry = registry

    def load(
        self,
        descriptor: ApplicationPluginDescriptor,
    ) -> ApplicationPluginContract:
        plugin = self.registry.resolve(
            descriptor.key()
        )

        if not isinstance(
            plugin,
            ApplicationPluginContract,
        ):
            raise TypeError(
                "invalid plugin contract"
            )

        return plugin

    def ready(self) -> bool:
        return self.registry.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPluginLoader",
]
