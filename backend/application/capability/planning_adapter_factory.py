from __future__ import annotations

from backend.application.capability.planning_adapter import (
    ApplicationPlanningCapabilityAdapter,
)
from backend.application.planning.service import (
    PlanningApplicationService,
)


class ApplicationPlanningCapabilityAdapterFactory:
    """
    Sole construction owner for planning capability adapter.
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        service: PlanningApplicationService,
    ) -> ApplicationPlanningCapabilityAdapter:

        if not self.ready():
            raise RuntimeError(
                "planning adapter factory unavailable"
            )

        if not isinstance(
            service,
            PlanningApplicationService,
        ):
            raise TypeError(
                "service must PlanningApplicationService"
            )

        adapter = (
            ApplicationPlanningCapabilityAdapter(
                service
            )
        )

        self._validate(
            adapter
        )

        return adapter

    @staticmethod
    def _validate(
        adapter: ApplicationPlanningCapabilityAdapter,
    ) -> None:
        for name in (
            "plan",
            "initialize",
            "shutdown",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(adapter, name, None)
            ):
                raise TypeError(
                    "invalid planning adapter"
                )

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
    "ApplicationPlanningCapabilityAdapterFactory",
]
