from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.planning import (
    PlannerPortProtocol,
)
from backend.core.planning.contracts import (
    PlanningCapabilityProtocol,
)


@runtime_checkable
class PlanningApplicationCompositionProtocol(
    Protocol,
):
    """
    Application-owned planning composition contract.

    Planner is injected through the Core-owned port.
    Runtime implementation is intentionally invisible here.
    """

    def create(
        self,
        *,
        planner: PlannerPortProtocol,
    ) -> PlanningCapabilityProtocol:
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
    "PlanningApplicationCompositionProtocol",
]
