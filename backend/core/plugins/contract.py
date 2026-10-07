from __future__ import annotations

from typing import Protocol

from backend.core.plugins.plugin_target import (
    PluginTargetProtocol,
)


class PluginContributor(Protocol):
    """
    Generic plugin contribution contract.

    Responsibility:
        - expose stable plugin identity
        - contribute functionality to target boundary

    Not Responsible:
        - discovery
        - loading
        - execution
        - lifecycle
    """

    name: str

    def contribute(
        self,
        target: PluginTargetProtocol,
    ) -> None:
        ...


__all__ = [
    "PluginContributor",
]
