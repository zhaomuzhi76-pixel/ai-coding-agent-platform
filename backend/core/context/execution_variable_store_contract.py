from __future__ import annotations

from typing import TypedDict

from backend.core.context.execution_variable_contract import (
    ExecutionVariableSnapshot,
)


class ExecutionVariableStoreSnapshot(
    TypedDict,
):
    """
    Execution variable store snapshot contract.
    """

    name: str
    version: str
    responsibility: tuple[str, ...]
    ready: bool
    count: int
    variables: dict[
        str,
        ExecutionVariableSnapshot,
    ]


__all__ = [
    "ExecutionVariableStoreSnapshot",
]
