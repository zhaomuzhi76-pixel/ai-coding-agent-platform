from __future__ import annotations

from typing import TypedDict

from backend.core.contracts.value import (
    CoreValue,
)


class ExecutionVariableSnapshot(
    TypedDict,
):
    """
    Execution variable snapshot contract.

    Responsibility:

        - define execution variable snapshot structure
    """

    id: str
    name: str
    value: CoreValue
    created_at: str


__all__ = [
    "ExecutionVariableSnapshot",
]
