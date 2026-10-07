from __future__ import annotations

from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.capability.planning_adapter import (
    ApplicationPlanningCapabilityAdapter,
)
from backend.application.planning.service import (
    PlanningApplicationService,
)


class PlanningStartupState:
    """
    Runtime state holder for planning startup binding.

    Owns:
        - bound planning service
        - capability manager
        - installed capability

    Does not own:
        - installation
        - lifecycle transition
        - planner construction
    """

    VERSION = "1.0"

    def __init__(
        self,
    ) -> None:
        self.service: (
            PlanningApplicationService | None
        ) = None

        self.manager: (
            ApplicationCapabilityManager | None
        ) = None

        self.capability: (
            ApplicationPlanningCapabilityAdapter | None
        ) = None

    def update(
        self,
        *,
        service: PlanningApplicationService,
        manager: ApplicationCapabilityManager,
        capability: ApplicationPlanningCapabilityAdapter,
    ) -> None:
        self.service = service
        self.manager = manager
        self.capability = capability

    def reset(
        self,
    ) -> None:
        self.service = None
        self.manager = None
        self.capability = None

    def ready(
        self,
    ) -> bool:
        return bool(
            self.service is not None
            and self.service.ready()
            and self.manager is not None
            and self.manager.ready()
            and self.capability is not None
            and self.capability.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "PlanningStartupState",
]
