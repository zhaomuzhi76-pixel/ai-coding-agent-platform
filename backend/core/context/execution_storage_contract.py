from __future__ import annotations

from typing import TypedDict

from backend.core.context.execution_output_contract import (
    ExecutionOutputSnapshot,
)
from backend.core.context.execution_variable_contract import (
    ExecutionVariableSnapshot,
)


class ExecutionContextStorageSnapshot(
    TypedDict,
):
    """Execution context storage snapshot contract."""

    name: str
    version: str
    responsibility: tuple[str, ...]
    ready: bool
    variable_store: dict[
        str,
        ExecutionVariableSnapshot,
    ]
    output_store: dict[
        str,
        ExecutionOutputSnapshot,
    ]


__all__ = [
    "ExecutionContextStorageSnapshot",
]
