from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)


@runtime_checkable
class PlanningStepProtocol(
    Protocol,
):
    """
    Core-owned planning step capability.

    Runtime execution translates this structural contract
    into RuntimeExecutionStep.
    """

    node_id: str
    executor_type: str
    description: str
    depends_on: list[str]
    parameters: dict[str, CoreValue]
    metadata: dict[str, CoreValue]


__all__ = [
    "PlanningStepProtocol",
]
