from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationPluginDescriptor:
    """
    Immutable plugin identity.

    Owns:
        - plugin metadata

    Does not own:
        - runtime instance
        - lifecycle
    """

    name: str
    version: str
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()

    def key(self) -> str:
        return f"{self.name}:{self.version}"


__all__ = [
    "ApplicationPluginDescriptor",
]
