from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CapabilityContract(Protocol):
    """
    Stable capability contract.

    Responsibility:
        - identify one capability
        - expose readiness

    Does not own:
        - execution logic
        - runtime lifecycle
        - transport
        - persistence
    """

    def name(self) -> str:
        ...

    def ready(self) -> bool:
        ...


__all__ = [
    "CapabilityContract",
]
