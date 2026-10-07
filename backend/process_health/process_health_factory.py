from __future__ import annotations

from backend.process_health.process_health import (
    ProcessHealth,
)
from backend.process_health.process_health_support import (
    ProcessHealthSupport,
)
from backend.process_observability import (
    ProcessObservabilityFactory,
)


class ProcessHealthFactory:
    """
    Construction boundary for process health.

    Owns only:
        - observability resolution
        - ProcessHealth construction
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        observability=None,
        support: ProcessHealthSupport | None = None,
    ) -> ProcessHealth:
        active_observability = (
            observability
            if observability is not None
            else ProcessObservabilityFactory().create()
        )

        health = ProcessHealth(
            observability=active_observability,
            support=support,
        )

        if not health.ready():
            raise RuntimeError(
                "process health unavailable"
            )

        return health

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessHealthFactory",
]
