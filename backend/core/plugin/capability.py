from __future__ import annotations

from typing import Final

from backend.core.contracts.value import CoreValue


class PluginCapability:
    """
    Core plugin capability descriptor.

    Owns:
        - capability identity
        - capability metadata

    Does not own:
        - execution
        - loading
        - registration
        - permission
    """

    VERSION: Final = "1.0"

    def __init__(
        self,
        name: str,
        description: str = "",
    ) -> None:
        if not isinstance(name, str):
            raise TypeError(
                "capability name must str"
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "capability name required"
            )

        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def ready(self) -> bool:
        return bool(self._name)

    def dump(self) -> dict[str, CoreValue]:
        return {
            "name": self._name,
            "description": self._description,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "PluginCapability",
]
