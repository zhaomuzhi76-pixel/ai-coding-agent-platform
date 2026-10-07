from __future__ import annotations

from backend.core.contracts.value import CoreValue
from backend.core.planning import (
    PlannerPortProtocol,
)
from backend.core.planning.contracts import (
    PlanningRequest,
    PlanningResult,
)


class PlanningApplicationService:
    """
    Application-owned task planning service.

    Responsibility:
        - consume the Core planner port
        - expose application planning operations
        - preserve the planning contract boundary

    Not Responsible:
        - planner implementation
        - runtime execution
        - persistence
        - transport
        - plugin lifecycle
    """

    VERSION = "2.0"

    def __init__(
        self,
        capability: PlannerPortProtocol,
    ) -> None:
        if capability is None:
            raise ValueError(
                "planner port required"
            )

        if not isinstance(
            capability,
            PlannerPortProtocol,
        ):
            raise TypeError(
                "planner must implement PlannerPortProtocol"
            )

        if not capability.ready():
            raise RuntimeError(
                "planner not ready"
            )

        self.capability = capability
        self.request_count = 0

    async def plan(
        self,
        request: PlanningRequest,
    ) -> PlanningResult:
        if not isinstance(
            request,
            PlanningRequest,
        ):
            raise TypeError(
                "request must PlanningRequest"
            )

        if not request.ready():
            raise ValueError(
                "planning request not ready"
            )

        result = await self.capability.plan(
            request
        )

        if not isinstance(
            result,
            PlanningResult,
        ):
            raise TypeError(
                "planner must return PlanningResult"
            )

        if not result.ready():
            raise RuntimeError(
                "planning result not ready"
            )

        self.request_count += 1
        return result

    def ready(
        self,
    ) -> bool:
        return self.capability.ready()

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "request_count": self.request_count,
            "planner": type(
                self.capability
            ).__name__,
        }


__all__ = [
    "PlanningApplicationService",
]
