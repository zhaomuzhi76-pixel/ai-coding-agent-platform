from __future__ import annotations

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.plugin.descriptor import (
    PluginDescriptor,
)


class PluginRegistry:
    """
    Core plugin descriptor registry.

    Owns:
        - plugin descriptor registration
        - descriptor lookup
        - plugin existence query

    Does not own:
        - plugin loading
        - plugin creation
        - execution
        - lifecycle management
    """

    VERSION = "1.0"

    def __init__(
        self,
    ) -> None:
        self._plugins: dict[
            str,
            PluginDescriptor,
        ] = {}

    def register(
        self,
        descriptor: PluginDescriptor,
    ) -> None:
        if not isinstance(
            descriptor,
            PluginDescriptor,
        ):
            raise TypeError(
                "plugin descriptor required"
            )

        if not descriptor.ready():
            raise ValueError(
                "plugin descriptor not ready"
            )

        name = descriptor.name

        if name in self._plugins:
            raise ValueError(
                f"plugin exists: {name}"
            )

        self._plugins[name] = descriptor

    def get(
        self,
        name: str,
    ) -> PluginDescriptor:
        return self._plugins[name]

    def exists(
        self,
        name: str,
    ) -> bool:
        return name in self._plugins

    def names(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            self._plugins.keys()
        )

    def ready(
        self,
    ) -> bool:
        return all(
            item.ready()
            for item in self._plugins.values()
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "plugins": tuple(
                self._plugins.keys()
            ),
            "count": len(
                self._plugins
            ),
            "ready": self.ready(),
        }


__all__ = [
    "PluginRegistry",
]
