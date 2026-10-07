from __future__ import annotations

from backend.runtime.plugins.intelligence.memory_adapter import (
    IntelligenceMemoryAdapter,
)


class IntelligenceMemoryCapabilityProvider:
    """
    Runtime memory capability provider.

    Responsibility:
        - create memory capability instance

    Not Responsible:
        - memory implementation
        - persistence
        - retrieval
    """

    VERSION = "1.0"

    def __init__(
        self,
    ) -> None:
        self.adapter = (
            IntelligenceMemoryAdapter()
        )

    def create(
        self,
    ) -> IntelligenceMemoryAdapter:
        return self.adapter

    def ready(
        self,
    ) -> bool:
        return self.adapter.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "adapter": self.adapter.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "IntelligenceMemoryCapabilityProvider",
]
