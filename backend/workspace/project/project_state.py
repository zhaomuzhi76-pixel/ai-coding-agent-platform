from __future__ import annotations

from enum import Enum


class ProjectState(str, Enum):
    """
    Logical programming-project lifecycle state.

    State ownership is local to ProjectModel.
    """

    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"

    def ready(self) -> bool:
        return self is ProjectState.ACTIVE


__all__ = [
    "ProjectState",
]
