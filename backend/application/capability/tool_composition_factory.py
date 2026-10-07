from __future__ import annotations

from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.capability.tool_composition import (
    ApplicationToolComposition,
)


class ApplicationToolCompositionFactory:
    """
    Factory for tool capability composition.

    Owns:
        - composition construction
        - construction validation

    Does not own:
        - tool implementation
        - execution lifecycle
        - runtime services
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        manager: ApplicationCapabilityManager,
    ) -> ApplicationToolComposition:
        if not isinstance(
            manager,
            ApplicationCapabilityManager,
        ):
            raise TypeError(
                "manager must be ApplicationCapabilityManager"
            )

        composition = ApplicationToolComposition(
            manager,
        )

        if not composition.ready():
            raise RuntimeError(
                "tool composition unavailable"
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
    "ApplicationToolCompositionFactory",
]
