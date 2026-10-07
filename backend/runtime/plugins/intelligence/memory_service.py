from __future__ import annotations

from backend.core.intelligence.memory_contract import (
    EngineeringMemoryRecordContract,
    EngineeringMemoryServiceContract,
)
from backend.runtime.plugins.intelligence.memory_store import (
    RuntimeEngineeringMemoryStore,
)


class RuntimeEngineeringMemoryService(
    EngineeringMemoryServiceContract,
):
    VERSION = "1.0"

    def __init__(
        self,
        store: RuntimeEngineeringMemoryStore | None = None,
    ) -> None:
        self._store = (
            store
            or RuntimeEngineeringMemoryStore()
        )

    def remember(
        self,
        record: EngineeringMemoryRecordContract,
    ) -> None:
        if not record.ready():
            return

        self._store.save(record)

    def history(
        self,
    ) -> tuple[EngineeringMemoryRecordContract, ...]:
        return self._store.all()

    def ready(self) -> bool:
        return self._store.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "store": self._store.dump(),
        }


__all__ = [
    "RuntimeEngineeringMemoryService",
]
