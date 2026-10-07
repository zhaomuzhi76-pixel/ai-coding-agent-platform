from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.application.planning.composition import (
    PlanningApplicationComposition,
)
from backend.application.planning.composition_contract import (
    PlanningApplicationCompositionProtocol,
)


class PlanningApplicationCompositionFactory:
    """
    Sole construction owner for
    PlanningApplicationComposition.
    """

    VERSION = "1.0"

    def create(
        self,
    ) -> PlanningApplicationCompositionProtocol:
        composition = PlanningApplicationComposition()

        if not composition.ready():
            raise RuntimeError(
                "planning application composition unavailable"
            )

        return composition

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "PlanningApplicationCompositionFactory",
]
