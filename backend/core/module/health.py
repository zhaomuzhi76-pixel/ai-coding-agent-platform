from __future__ import annotations

from typing import Final

from backend.core.contracts.value import CoreValue


class BaseHealth:
    """
    Canonical health capability.

    Owns:
        - health information generation

    Does not own:
        - readiness contract
        - lifecycle state
        - component snapshot
        - health scheduling
    """

    VERSION: Final = "7.0"

    RESPONSIBILITY: Final = (
        "health_capability",
    )

    def health(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "status": "READY",
        }


__all__ = [
    "BaseHealth",
]
