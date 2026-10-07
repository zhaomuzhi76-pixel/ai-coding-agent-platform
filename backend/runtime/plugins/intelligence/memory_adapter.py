from __future__ import annotations

from backend.core.intelligence.memory_contract import (
    EngineeringMemoryRecordContract,
    EngineeringMemoryServiceContract,
)
from backend.runtime.plugins.intelligence.memory_service import (
    RuntimeEngineeringMemoryService,
)


class IntelligenceMemoryAdapter:
    VERSION = "2.0"

    def __init__(
        self,
        service: EngineeringMemoryServiceContract | None = None,
    ) -> None:
        self.service = (
            service
            if service is not None
            else RuntimeEngineeringMemoryService()
        )

        if not isinstance(
            self.service,
            EngineeringMemoryServiceContract,
        ):
            raise TypeError(
                "memory service contract required"
            )

    def remember(
        self,
        record: EngineeringMemoryRecordContract,
    ) -> None:
        if not isinstance(
            record,
            EngineeringMemoryRecordContract,
        ):
            raise TypeError(
                "memory record contract required"
            )

        self.service.remember(record)

    def history(
        self,
    ) -> tuple[EngineeringMemoryRecordContract, ...]:
        return self.service.history()

    def ready(self) -> bool:
        return self.service.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "service": self.service.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "IntelligenceMemoryAdapter",
]
