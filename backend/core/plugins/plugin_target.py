from __future__ import annotations

from typing import Protocol

from backend.core.di.value_protocol import (
    DependencyValueProtocol,
)


class PluginTargetProtocol(Protocol):
    """
    Plugin contribution target contract.

    Responsibility:
        - define plugin attachment boundary

    Not Responsible:
        - plugin loading
        - plugin execution
        - business registration logic
    """

    def register(
        self,
        name: str,
        value: DependencyValueProtocol,
    ) -> None:
        ...


__all__ = [
    "PluginTargetProtocol",
]
