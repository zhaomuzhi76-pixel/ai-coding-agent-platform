from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.health.status import HealthStatus


@runtime_checkable
class HealthCheckProtocol(Protocol):
    """
    Atomic health-check contract.
    """

    def check(self) -> HealthStatus:
        ...


__all__ = [
    "HealthCheckProtocol",
]
