from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.application.planning.service import (
    PlanningApplicationService,
)
from backend.core.planning.contracts import (
    PlanningCapabilityProtocol,
)


class PlanningApplicationServiceFactory:
    VERSION = "1.0"

    def create(
        self,
        *,
        capability: PlanningCapabilityProtocol,
    ) -> PlanningApplicationService:
        if capability is None:
            raise ValueError("planning capability required")

        service = PlanningApplicationService(
            capability=capability,
        )

        self._validate(service)
        return service

    @staticmethod
    def _validate(
        service: PlanningApplicationService,
    ) -> None:
        for name in (
            "plan",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(service, name, None)
            ):
                raise TypeError(
                    "planning application service must expose "
                    f"{name}()"
                )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "PlanningApplicationServiceFactory",
]
