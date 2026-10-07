from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.plugins.contract import (
    PluginContributor,
)


class ContributorRegistry:
    """
    Generic plugin registration boundary.

    Responsibility:
        - register contributors
        - expose contributors

    Not Responsible:
        - discovery
        - loading
        - execution
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "plugin_contributor_registration",
    )

    def __init__(
        self,
    ) -> None:
        self._plugins: dict[
            str,
            PluginContributor,
        ] = {}

    def register(
        self,
        plugin: PluginContributor,
    ) -> None:
        self._validate(plugin)

        if plugin.name in self._plugins:
            raise ValueError(
                f"plugin already registered: {plugin.name}"
            )

        self._plugins[plugin.name] = plugin

    def get(
        self,
        name: str,
    ) -> PluginContributor | None:
        return self._plugins.get(name)

    def list_plugins(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            self._plugins.keys()
        )

    def count(
        self,
    ) -> int:
        return len(self._plugins)

    def ready(
        self,
    ) -> bool:
        return all(
            bool(plugin.name)
            for plugin in self._plugins.values()
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": "ContributorRegistry",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "count": self.count(),
            "plugins": self.list_plugins(),
        }

    @staticmethod
    def _validate(
        plugin: PluginContributor,
    ) -> None:
        if plugin is None:
            raise ValueError(
                "plugin contributor required"
            )

        if not isinstance(
            plugin.name,
            str,
        ) or not plugin.name.strip():
            raise TypeError(
                "plugin contributor name required"
            )

        if not callable(
            plugin.contribute,
        ):
            raise TypeError(
                "plugin contributor must implement contribute()"
            )


__all__ = [
    "ContributorRegistry",
]
