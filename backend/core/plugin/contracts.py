from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)


@runtime_checkable
class PluginProtocol(Protocol):
    """
    Core plugin contract.

    Owns:
        - plugin identity exposure
        - plugin descriptor exposure
        - readiness contract

    Does not own:
        - registration
        - loading
        - dependency injection
        - execution scheduling
    """

    @property
    def name(
        self,
    ) -> str:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "PluginProtocol",
]
