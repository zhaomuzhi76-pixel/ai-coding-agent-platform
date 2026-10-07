from __future__ import annotations

from typing import Final

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.plugin.capability import (
    PluginCapability,
)


class PluginDescriptor:
    """
    Immutable plugin metadata descriptor.

    Owns:
        - plugin identity metadata
        - capability declaration

    Does not own:
        - plugin loading
        - plugin lifecycle
        - plugin execution
        - plugin registration
    """

    VERSION: Final = "1.0"

    def __init__(
        self,
        *,
        name: str,
        version: str,
        category: str,
        capabilities: tuple[
            PluginCapability,
            ...,
        ] = (),
    ) -> None:
        if not isinstance(name, str):
            raise TypeError(
                "plugin name must str"
            )

        if not isinstance(version, str):
            raise TypeError(
                "plugin version must str"
            )

        if not isinstance(category, str):
            raise TypeError(
                "plugin category must str"
            )

        name = name.strip()
        version = version.strip()
        category = category.strip()

        if not name:
            raise ValueError(
                "plugin name required"
            )

        if not version:
            raise ValueError(
                "plugin version required"
            )

        if not category:
            raise ValueError(
                "plugin category required"
            )

        for item in capabilities:
            if not isinstance(
                item,
                PluginCapability,
            ):
                raise TypeError(
                    "invalid plugin capability"
                )

        self._name = name
        self._version = version
        self._category = category
        self._capabilities = tuple(
            capabilities
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def category(self) -> str:
        return self._category

    def capabilities(
        self,
    ) -> tuple[PluginCapability, ...]:
        return self._capabilities

    def ready(
        self,
    ) -> bool:
        return bool(
            self._name
            and self._version
            and self._category
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self._name,
            "version": self._version,
            "category": self._category,
            "capabilities": [
                item.dump()
                for item in self._capabilities
            ],
            "ready": self.ready(),
        }


__all__ = [
    "PluginDescriptor",
]
