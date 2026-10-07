from __future__ import annotations

from backend.runtime.plugin.capability import (
    RuntimeCapability,
)


class IntelligenceGovernanceCapability(
    RuntimeCapability,
):
    """
    Agent intelligence governance capability.

    Owns:
        - intelligence decision boundary
        - memory governance contract

    Does not own:
        - memory storage
        - session state
        - reflection engine
        - knowledge base
    """

    def __init__(
        self,
    ) -> None:
        super().__init__(
            category="intelligence",
            name="governance",
            version="1.0",
        )


__all__ = [
    "IntelligenceGovernanceCapability",
]
