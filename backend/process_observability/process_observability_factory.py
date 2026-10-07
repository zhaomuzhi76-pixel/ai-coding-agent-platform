from __future__ import annotations

from backend.process_control import (
    ProcessControlFactory,
)
from backend.process_observability.process_observability import (
    ProcessObservability,
)
from backend.process_observability.process_observability_support import (
    ProcessObservabilitySupport,
)


class ProcessObservabilityFactory:
    """
    Sole construction owner for process observability.
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        control=None,
        support: ProcessObservabilitySupport | None = None,
    ) -> ProcessObservability:
        active_control = control

        if active_control is None:
            active_control = (
                ProcessControlFactory()
                .create()
            )

        observability = ProcessObservability(
            control=active_control,
            support=support,
        )

        if not observability.ready():
            raise RuntimeError(
                "process observability unavailable"
            )

        return observability

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessObservabilityFactory",
]
