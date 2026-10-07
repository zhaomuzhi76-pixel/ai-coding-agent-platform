from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.plugins.plugin_component import (
    PluginComponentProtocol,
)


class PluginDiscovery:
    """
    Plugin discovery boundary.

    Responsibility:
        - collect plugin components

    Not Responsible:
        - plugin execution
        - registration
        - business logic
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "plugin_discovery",
    )

    def __init__(
        self,
    ) -> None:
        self._components: list[
            PluginComponentProtocol
        ] = []

    def add(
        self,
        component: PluginComponentProtocol,
    ) -> None:
        self._validate(component)
        self._components.append(component)

    def discover(
        self,
    ) -> tuple[
        PluginComponentProtocol,
        ...,
    ]:
        return tuple(
            self._components
        )

    def count(
        self,
    ) -> int:
        return len(self._components)

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": "PluginDiscovery",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "count": self.count(),
        }

    @staticmethod
    def _validate(
        component: PluginComponentProtocol,
    ) -> None:
        if component is None:
            raise ValueError(
                "plugin component required"
            )

        if not isinstance(
            component.name,
            str,
        ):
            raise TypeError(
                "plugin component name required"
            )


__all__ = [
    "PluginDiscovery",
]
