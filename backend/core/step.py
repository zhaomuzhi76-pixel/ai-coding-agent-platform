from __future__ import annotations

from typing import TypedDict

from backend.core.contracts.value import (
    CoreValue,
)


class Step(
    TypedDict,
):
    """
    Legacy step compatibility contract.

    Responsibility:

        - preserve old import compatibility
        - provide typed execution step shape

    New runtime execution must use:
        backend.core.execution.RuntimeExecutionStep
    """

    id: str
    tool: str
    input: dict[str, CoreValue]
    output: CoreValue
    status: str


__all__ = [
    "Step",
]
