from __future__ import annotations

from typing import Dict

from backend.application.plugin_system.plugin_contract import (
    ApplicationPluginContract,
)
from backend.application.plugin_system.plugin_descriptor import (
    ApplicationPluginDescriptor,
)


class ApplicationPluginRegistry:
    """
    Plugin discovery and identity registry.

    Owns:
        - register plugin
        - remove plugin
        - resolve plugin

    Does not own:
        - lifecycle transition
        - execution
        - construction
    """

    def __init__(self) -> None:
        self._plugins: Dict[
            str,
            ApplicationPluginContract,
        ] = {}

        self._descriptors: Dict[
            str,
            ApplicationPluginDescriptor,
        ] = {}

    def register(
        self,
        *,
        descriptor: ApplicationPluginDescriptor,
        plugin: ApplicationPluginContract,
    ) -> None:
        key = descriptor.key()

        if key in self._plugins:
            raise RuntimeError(
                f"plugin already registered: {key}"
            )

        self._plugins[key] = plugin
        self._descriptors[key] = descriptor

    def unregister(
        self,
        key: str,
    ) -> None:
        self._plugins.pop(
            key,
            None,
        )

        self._descriptors.pop(
            key,
            None,
        )

    def resolve(
        self,
        key: str,
    ) -> ApplicationPluginContract:
        plugin = self._plugins.get(key)

        if plugin is None:
            raise RuntimeError(
                f"plugin unavailable: {key}"
            )

        return plugin

    def descriptor(
        self,
        key: str,
    ) -> ApplicationPluginDescriptor:
        descriptor = self._descriptors.get(key)

        if descriptor is None:
            raise RuntimeError(
                f"descriptor unavailable: {key}"
            )

        return descriptor

    def list(self) -> list[str]:
        return list(
            self._plugins.keys()
        )

    def ready(self) -> bool:
        return True


__all__ = [
    "ApplicationPluginRegistry",
]
