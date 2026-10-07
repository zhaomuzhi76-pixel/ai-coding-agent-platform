from __future__ import annotations

from typing import Any

from backend.application.capability.planning_contract import (
    PlanningApplicationCapabilityProtocol,
)
from backend.application.planning.service import (
    PlanningApplicationService,
)
from backend.core.planning.contracts import (
    PlanningRequest,
    PlanningResult,
)


class ApplicationPlanningCapabilityAdapter(
    PlanningApplicationCapabilityProtocol,
):
    """
    Application planning capability adapter.

    Owns:
        - capability identity
        - lifecycle state
        - application planning delegation

    Does not own:
        - planner implementation
        - runtime planning
        - execution lifecycle
        - persistence
        - transport
    """

    VERSION = "1.0"
    NAME = "planning"

    def __init__(
        self,
        service: PlanningApplicationService,
    ) -> None:
        if not isinstance(
            service,
            PlanningApplicationService,
        ):
            raise TypeError(
                "service must PlanningApplicationService"
            )

        self.service = service
        self.initialized = False
        self.shutdown_count = 0
        self.plan_count = 0

    @property
    def name(
        self,
    ) -> str:
        return self.NAME

    @property
    def version(
        self,
    ) -> str:
        return self.VERSION

    def capabilities(
        self,
    ) -> tuple[str, ...]:
        return (
            "planning.plan",
        )

    async def plan(
        self,
        request: PlanningRequest,
    ) -> PlanningResult:
        if not self.initialized:
            raise RuntimeError(
                "planning capability not enabled"
            )

        result = await self.service.plan(
            request
        )

        if not isinstance(
            result,
            PlanningResult,
        ):
            raise TypeError(
                "planning service must return PlanningResult"
            )

        self.plan_count += 1

        return result

    def initialize(
        self,
        context: Any = None,
    ) -> None:
        if not self.service.ready():
            raise RuntimeError(
                "planning service not ready"
            )

        self.initialized = True

    def shutdown(
        self,
    ) -> None:
        self.initialized = False
        self.shutdown_count += 1

    def ready(
        self,
    ) -> bool:
        return self.service.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities(),
            "initialized": self.initialized,
            "shutdown_count": self.shutdown_count,
            "plan_count": self.plan_count,
            "service": type(
                self.service
            ).__name__,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPlanningCapabilityAdapter",
]
