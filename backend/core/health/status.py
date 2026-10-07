from __future__ import annotations

from enum import StrEnum


class HealthStatus(StrEnum):
    """
    Canonical health state.

    Owns:
        - health status vocabulary

    Does not own:
        - health checking
        - report generation
        - monitoring lifecycle
    """

    UNKNOWN = "unknown"
    READY = "ready"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


__all__ = [
    "HealthStatus",
]
