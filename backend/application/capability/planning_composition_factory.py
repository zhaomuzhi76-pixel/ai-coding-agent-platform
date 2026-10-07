from __future__ import annotations

from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)

from backend.application.capability.planning_composition import (
    ApplicationPlanningCapabilityComposition,
)


class ApplicationPlanningCapabilityCompositionFactory:
    """
    Factory for planning capability composition.

    Owns:
        - composition construction
        - construction validation

    Does not own:
        - planner implementation
        - provider implementation
        - runtime lifecycle
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        manager: ApplicationCapabilityManager,
    ) -> ApplicationPlanningCapabilityComposition:

        if not isinstance(
            manager,
            ApplicationCapabilityManager,
        ):
            raise TypeError(
                "manager must be ApplicationCapabilityManager"
            )

        composition = ApplicationPlanningCapabilityComposition(
            manager,
        )

        if not composition.ready():
            raise RuntimeError(
                "planning capability composition unavailable"
            )

        return composition

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPlanningCapabilityCompositionFactory",
]
