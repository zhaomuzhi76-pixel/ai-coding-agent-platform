from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.capability.contracts import (
    ApplicationCapabilityProtocol,
)
from backend.core.planning.contracts import (
    PlanningRequest,
    PlanningResult,
)


@runtime_checkable
class PlanningApplicationCapabilityProtocol(
    ApplicationCapabilityProtocol,
    Protocol,
):
    """
    Application-visible planning capability contract.

    Responsibility:
        - expose canonical planning operation
        - preserve application capability lifecycle

    Not Responsible:
        - planner implementation
        - runtime graph construction
        - DAG scheduling
        - persistence
        - transport serialization
        - execution lifecycle
    """

    async def plan(
        self,
        request: PlanningRequest,
    ) -> PlanningResult:
        ...


__all__ = [
    "PlanningApplicationCapabilityProtocol",
]
