from __future__ import annotations

from backend.application.composition.capability import (
    ApplicationCapabilityComposition,
)


class ApplicationCapabilityCompositionFactory:
    """
    Sole construction owner for ApplicationCapabilityComposition.
    """

    VERSION = "1.0"

    def create(
        self,
    ) -> ApplicationCapabilityComposition:
        composition = ApplicationCapabilityComposition()

        if not composition.ready():
            raise RuntimeError(
                "application capability composition unavailable"
            )

        return composition

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityCompositionFactory",
]
