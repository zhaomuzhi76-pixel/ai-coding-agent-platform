from __future__ import annotations

from typing import TypedDict

from backend.core.step import (
    Step,
)


class Plan(
    TypedDict,
):
    """
    Legacy planning contract.

    Responsibility:

        - preserve old plan data shape

    Runtime execution must consume:
        backend.core.execution.RuntimeExecutionStep
    """

    steps: list[Step]


__all__ = [
    "Plan",
]
