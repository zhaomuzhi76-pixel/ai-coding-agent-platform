from __future__ import annotations

from backend.application.composition.runtime import (
    ApplicationRuntimeComposition,
)
from backend.application.composition.runtime_construction_port import (
    ApplicationRuntimeConstructionProtocol,
)


class ApplicationRuntimeCompositionFactory:
    """
    Sole construction owner for ApplicationRuntimeComposition.
    """

    VERSION = "3.0"

    def create(
        self,
        *,
        construction: ApplicationRuntimeConstructionProtocol,
    ) -> ApplicationRuntimeComposition:
        if not isinstance(
            construction,
            ApplicationRuntimeConstructionProtocol,
        ):
            raise TypeError(
                "construction must implement "
                "ApplicationRuntimeConstructionProtocol"
            )

        if not construction.ready():
            raise RuntimeError(
                "runtime construction unavailable"
            )

        composition = ApplicationRuntimeComposition(
            construction=construction,
        )

        if not composition.ready():
            raise RuntimeError(
                "application runtime composition unavailable"
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
    "ApplicationRuntimeCompositionFactory",
]
