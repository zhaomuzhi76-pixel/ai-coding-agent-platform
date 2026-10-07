from __future__ import annotations

from enum import StrEnum


class NodeState(StrEnum):
    """
    Task graph node lifecycle state.

    Responsibility:

        - graph node lifecycle contract
        - task state representation

    Not Responsible:

        - planner state
        - executor scheduling
        - retry policy
        - persistence
    """

    CREATED = "created"

    READY = "ready"

    RUNNING = "running"

    SUCCESS = "success"

    FAILED = "failed"

    CANCELLED = "cancelled"


TERMINAL_STATES = frozenset(
    {
        NodeState.SUCCESS,
        NodeState.FAILED,
        NodeState.CANCELLED,
    }
)


EXECUTABLE_STATES = frozenset(
    {
        NodeState.CREATED,
        NodeState.READY,
    }
)


__all__ = [
    "NodeState",
    "TERMINAL_STATES",
    "EXECUTABLE_STATES",
]
