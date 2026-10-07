from __future__ import annotations

from backend.application.modules.infrastructure_composition import (
    ApplicationInfrastructureComposition,
)


class ApplicationInfrastructureCompositionFactory:
    """
    Infrastructure composition factory.

    Owns:
        - composition construction
        - validation

    Does not own:
        - runtime lifecycle
        - runtime implementation
    """

    VERSION = "1.0"

    def create(
        self,
        runtime_construction,
    ) -> ApplicationInfrastructureComposition:

        composition = (
            ApplicationInfrastructureComposition(
                runtime_construction
            )
        )

        if not composition.ready():
            raise RuntimeError(
                "infrastructure composition unavailable"
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
    "ApplicationInfrastructureCompositionFactory",
]
