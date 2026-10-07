from __future__ import annotations

from enum import Enum


class ProjectRuntimeState(str, Enum):
    """
    Project runtime lifecycle state.

    Owns:
        - runtime lifecycle state only

    Does not own:
        - project identity
        - workspace operations
        - filesystem
        - execution
        - persistence
    """

    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"

    def ready(self) -> bool:
        return self is ProjectRuntimeState.ACTIVE


__all__ = [
    "ProjectRuntimeState",
]
