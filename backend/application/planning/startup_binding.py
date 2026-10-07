from __future__ import annotations

from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.capability.planning_adapter import (
    ApplicationPlanningCapabilityAdapter,
)
from backend.application.planning.planning_capability_binder import (
    PlanningCapabilityBinder,
)
from backend.application.planning.planning_startup_state import (
    PlanningStartupState,
)
from backend.application.planning.service import (
    PlanningApplicationService,
)


class PlanningStartupBinding:
    """
    Planning startup orchestration boundary.

    Owns:
        - startup binding flow
        - readiness projection
        - state ownership

    Does not own:
        - capability construction
        - lifecycle transition
        - planner implementation
    """

    VERSION = "6.0"
    CAPABILITY_KEY = "application.planning:1.0"

    def __init__(
        self,
    ) -> None:
        self.binder = PlanningCapabilityBinder()
        self.state = PlanningStartupState()

    def bind(
        self,
        *,
        planning_service: PlanningApplicationService,
        capability_manager: ApplicationCapabilityManager,
    ) -> ApplicationPlanningCapabilityAdapter:

        capability = self.binder.bind(
            service=planning_service,
            manager=capability_manager,
        )

        self.state.update(
            service=planning_service,
            manager=capability_manager,
            capability=capability,
        )

        if not self.ready():
            raise RuntimeError(
                "planning startup binding unavailable"
            )

        return capability

    def reset(
        self,
    ) -> None:
        self.state.reset()

    def ready(
        self,
    ) -> bool:
        return bool(
            self.binder.ready()
            and self.state.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "binder": self.binder.dump(),
            "state": self.state.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "PlanningStartupBinding",
]
