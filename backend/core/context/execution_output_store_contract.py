from __future__ import annotations

from typing import TypedDict

from backend.core.context.execution_output_contract import (
    ExecutionOutputSnapshot,
)


class ExecutionOutputStoreSnapshot(
    TypedDict,
):
    """
    Execution output store snapshot contract.
    """

    name: str
    version: str
    responsibility: tuple[str, ...]
    ready: bool
    count: int
    outputs: dict[
        str,
        ExecutionOutputSnapshot,
    ]


__all__ = [
    "ExecutionOutputStoreSnapshot",
]
