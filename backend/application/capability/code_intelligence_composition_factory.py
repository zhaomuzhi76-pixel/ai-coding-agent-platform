from __future__ import annotations

from backend.application.capability.code_intelligence_composition import (
    ApplicationCodeIntelligenceComposition,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)


class ApplicationCodeIntelligenceCompositionFactory:
    """
    Factory for code intelligence composition.

    Owns:
        - composition construction
        - construction validation

    Does not own:
        - code intelligence implementation
        - repository access
        - runtime execution
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        manager: ApplicationCapabilityManager,
    ) -> ApplicationCodeIntelligenceComposition:
        if not isinstance(
            manager,
            ApplicationCapabilityManager,
        ):
            raise TypeError(
                "manager must be ApplicationCapabilityManager"
            )

        composition = ApplicationCodeIntelligenceComposition(
            manager,
        )

        if not composition.ready():
            raise RuntimeError(
                "code intelligence composition unavailable"
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
    "ApplicationCodeIntelligenceCompositionFactory",
]
