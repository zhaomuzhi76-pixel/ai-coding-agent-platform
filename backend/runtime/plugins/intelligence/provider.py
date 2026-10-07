from __future__ import annotations

from backend.runtime.plugins.intelligence.governance import (
    IntelligenceGovernanceService,
)


class IntelligenceGovernanceCapabilityProvider:
    """
    Runtime capability provider.
    """

    VERSION = "1.0"

    def __init__(
        self,
    ) -> None:
        self.service = (
            IntelligenceGovernanceService()
        )

    def create(
        self,
    ) -> IntelligenceGovernanceService:
        return self.service

    def ready(
        self,
    ) -> bool:
        return self.service.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "service": self.service.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "IntelligenceGovernanceCapabilityProvider",
]
