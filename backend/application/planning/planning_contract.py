from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import CoreValue
from backend.core.planning import (
    PlanningRequest,
    PlanningResult,
)


@runtime_checkable
class ApplicationPlanningProtocol(Protocol):
    """
    Application owned planning boundary.

    Application depends on this contract only.

    Concrete planners are hidden behind Core planning protocol.
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
    "ApplicationPlanningProtocol",
]
