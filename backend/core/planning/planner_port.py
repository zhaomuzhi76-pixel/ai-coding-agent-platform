from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import CoreValue
from backend.core.planning.contracts import PlanningRequest, PlanningResult


@runtime_checkable
class PlannerPortProtocol(Protocol):
    """
    Core owned planner boundary.

    Application depends only on this contract.

    Implementations may live in Agent/runtime layers.
    """

    async def plan(
        self,
        request: PlanningRequest,
    ) -> PlanningResult:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "PlannerPortProtocol",
]
