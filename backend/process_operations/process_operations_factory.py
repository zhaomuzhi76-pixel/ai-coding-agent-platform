from __future__ import annotations

from backend.process_control import (
    ProcessControlFactory,
)
from backend.process_health import (
    ProcessHealthFactory,
)
from backend.process_observability import (
    ProcessObservabilityFactory,
)
from backend.process_operations.process_operations import (
    ProcessOperations,
)
from backend.process_operations.process_operations_support import (
    ProcessOperationsSupport,
)


class ProcessOperationsFactory:
    """
    Construction boundary for the process operations aggregate.

    Owns only:
        - lower-layer dependency resolution
        - ProcessOperations construction
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        control=None,
        observability=None,
        health=None,
        support: ProcessOperationsSupport | None = None,
    ) -> ProcessOperations:
        active_control = (
            control
            if control is not None
            else ProcessControlFactory().create()
        )

        active_observability = (
            observability
            if observability is not None
            else ProcessObservabilityFactory().create(
                control=active_control
            )
        )

        active_health = (
            health
            if health is not None
            else ProcessHealthFactory().create(
                observability=active_observability
            )
        )

        operations = ProcessOperations(
            control=active_control,
            observability=active_observability,
            health=active_health,
            support=support,
        )

        if not operations.ready():
            raise RuntimeError(
                "process operations unavailable"
            )

        return operations

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessOperationsFactory",
]
