from __future__ import annotations

from enum import StrEnum


class RuntimeNodeState(StrEnum):
    """
    Runtime node lifecycle state value.

    Responsibility:
        - define runtime node state values

    Not Responsible:
        - state transition
        - scheduling
        - execution
        - graph construction
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
        RuntimeNodeState.SUCCESS,
        RuntimeNodeState.FAILED,
        RuntimeNodeState.CANCELLED,
    }
)


EXECUTABLE_STATES = frozenset(
    {
        RuntimeNodeState.CREATED,
        RuntimeNodeState.READY,
    }
)


def is_finished(
    state: RuntimeNodeState,
) -> bool:
    return state in TERMINAL_STATES


def is_executable(
    state: RuntimeNodeState,
) -> bool:
    return state in EXECUTABLE_STATES


__all__ = [
    "RuntimeNodeState",
    "TERMINAL_STATES",
    "EXECUTABLE_STATES",
    "is_finished",
    "is_executable",
]
