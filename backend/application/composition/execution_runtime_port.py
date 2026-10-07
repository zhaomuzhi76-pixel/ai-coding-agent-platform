from __future__ import annotations

from typing import Protocol, runtime_checkable

@runtime_checkable
class ApplicationExecutionComponentProtocol(Protocol):
    """
    Application-owned contract for a constructed execution component.
    """

    def ready(
        self,
    ) -> bool:
        ...

__all__ = [

    "ApplicationExecutionComponentProtocol",
]
