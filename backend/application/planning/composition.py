from __future__ import annotations

from backend.application.planning.composition_contract import (
    PlanningApplicationCompositionProtocol,
)
from backend.application.planning.service import (
    PlanningApplicationService,
)
from backend.application.planning.service_factory import (
    PlanningApplicationServiceFactory,
)
from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.planning import (
    PlannerPortProtocol,
)


class PlanningApplicationComposition(
    PlanningApplicationCompositionProtocol,
):
    """
    Application planning composition boundary.

    Owns:
        - planner port validation
        - planning application service construction

    Does not own:
        - planner implementation
        - runtime capability registration
        - runtime lifecycle
        - execution
        - persistence
        - transport
    """

    VERSION = "5.0"

    def create(
        self,
        *,
        planner: PlannerPortProtocol,
    ) -> PlanningApplicationService:
        if not isinstance(
            planner,
            PlannerPortProtocol,
        ):
            raise TypeError(
                "planner must implement PlannerPortProtocol"
            )

        if not planner.ready():
            raise RuntimeError(
                "planner unavailable"
            )

        service = (
            PlanningApplicationServiceFactory().create(
                capability=planner,
            )
        )

        if not service.ready():
            raise RuntimeError(
                "planning application service unavailable"
            )

        return service

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "PlanningApplicationComposition",
]
