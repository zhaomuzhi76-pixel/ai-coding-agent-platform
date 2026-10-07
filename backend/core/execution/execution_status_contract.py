from __future__ import annotations

from typing import TypedDict


class ExecutionStatusSnapshot(
    TypedDict,
):
    """
    Execution status snapshot contract.

    Responsibility:

        - define serialized execution status value
    """

    value: str


__all__ = [
    "ExecutionStatusSnapshot",
]
