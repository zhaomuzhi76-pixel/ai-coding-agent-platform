from __future__ import annotations

from typing import Protocol


class PluginComponentProtocol(Protocol):
    """
    Discovered plugin component contract.

    Responsibility:
        - provide plugin component boundary

    Not Responsible:
        - loading
        - execution
        - lifecycle
    """

    name: str


__all__ = [
    "PluginComponentProtocol",
]
