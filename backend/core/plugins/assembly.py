from __future__ import annotations

from backend.core.plugins.discovery import (
    PluginDiscovery,
)

from backend.core.plugins.contributor_registry import (
    ContributorRegistry,
)

from backend.core.contracts.payload import (
    Payload,
)


class PluginAssembly:
    """
    Plugin assembly coordinator.

    Responsibility:
        - connect discovery and contributor registry

    Not Responsible:
        - plugin execution
        - plugin lifecycle
    """

    VERSION = "3.0"

    RESPONSIBILITY = (
        "plugin_assembly",
    )

    def __init__(
        self,
        discovery: PluginDiscovery,
        registry: ContributorRegistry,
    ) -> None:
        self.discovery = discovery
        self.registry = registry

    def assemble(
        self,
    ) -> None:
        for plugin in self.discovery.discover():
            self.registry.register(
                plugin
            )

    def dump(
        self,
    ) -> Payload:
        return {
            "name": "PluginAssembly",
            "version": self.VERSION,
            "count": self.registry.count(),
        }


__all__ = [
    "PluginAssembly",
]
