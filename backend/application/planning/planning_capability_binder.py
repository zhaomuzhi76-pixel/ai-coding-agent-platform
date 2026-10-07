from __future__ import annotations

from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.capability.planning_adapter import (
    ApplicationPlanningCapabilityAdapter,
)
from backend.application.capability.planning_adapter_factory import (
    ApplicationPlanningCapabilityAdapterFactory,
)
from backend.application.capability.planning_composition import (
    ApplicationPlanningCapabilityComposition,
)
from backend.application.capability.planning_composition_factory import (
    ApplicationPlanningCapabilityCompositionFactory,
)
from backend.application.planning.service import (
    PlanningApplicationService,
)


class PlanningCapabilityBinder:
    """
    Planning capability installation boundary.

    Owns:
        - capability composition creation
        - adapter creation
        - capability installation

    Does not own:
        - planner construction
        - startup lifecycle
        - execution
    """

    VERSION = "1.0"

    def __init__(
        self,
    ) -> None:
        self.composition: (
            ApplicationPlanningCapabilityComposition
            | None
        ) = None

    def bind(
        self,
        *,
        service: PlanningApplicationService,
        manager: ApplicationCapabilityManager,
    ) -> ApplicationPlanningCapabilityAdapter:

        if not isinstance(
            service,
            PlanningApplicationService,
        ):
            raise TypeError(
                "service must PlanningApplicationService"
            )

        if not isinstance(
            manager,
            ApplicationCapabilityManager,
        ):
            raise TypeError(
                "manager must ApplicationCapabilityManager"
            )

        composition = (
            ApplicationPlanningCapabilityCompositionFactory()
            .create(
                manager=manager,
            )
        )

        adapter = (
            ApplicationPlanningCapabilityAdapterFactory()
            .create(
                service=service,
            )
        )

        composition.install(
            adapter,
        )

        composition.enable()

        if not adapter.ready():
            raise RuntimeError(
                "planning capability unavailable"
            )

        self.composition = composition

        return adapter

    def ready(
        self,
    ) -> bool:
        return (
            self.composition is not None
            and self.composition.ready()
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
    "PlanningCapabilityBinder",
]
