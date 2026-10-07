from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ModuleProtocol(Protocol):
    """
    Canonical module identity contract.

    Owns:
        - module name

    Does not own:
        - component identity protocol
        - readiness protocol
        - dump protocol
        - lifecycle protocol
    """

    @property
    def name(self) -> str:
        ...


__all__ = [
    "ModuleProtocol",
]
