from __future__ import annotations

from enum import Enum


class LifecycleState(Enum):
    """
    Canonical framework component lifecycle state.
    """

    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    DESTROYED = "destroyed"

    def value_name(self) -> str:
        return self.value


__all__ = [
    "LifecycleState",
]
