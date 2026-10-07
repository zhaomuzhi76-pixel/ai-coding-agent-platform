from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ReadyProtocol(Protocol):
    """
    Base readiness contract.

    Responsibility:
        - provide component readiness state

    Not Responsible:
        - lifecycle management
        - initialization strategy
        - dependency resolution
    """

    def ready(self) -> bool:
        ...


__all__ = [
    "ReadyProtocol",
]
