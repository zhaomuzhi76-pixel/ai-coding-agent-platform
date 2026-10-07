from __future__ import annotations

from enum import StrEnum


class DependencyLifetime(StrEnum):
    """
    Dependency instance lifetime policy.

    Owns:
        - lifetime semantic identity

    Does not own:
        - registration
        - resolution
        - instance storage
    """

    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


__all__ = [
    "DependencyLifetime",
]
