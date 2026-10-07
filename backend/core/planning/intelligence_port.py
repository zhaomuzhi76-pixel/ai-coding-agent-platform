from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PlannerIntelligenceProtocol(Protocol):
    """
    Core-owned planner project-intelligence port.
    """

    def project_intelligence(
        self,
    ) -> dict[str, object]:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "PlannerIntelligenceProtocol",
]
