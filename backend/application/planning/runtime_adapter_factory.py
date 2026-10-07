from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.application.planning.runtime_adapter import (
    PlanningRuntimeAdapter,
)
from backend.application.planning.runtime_adapter_contract import (
    PlanningRuntimeAdapterProtocol,
)


class PlanningRuntimeAdapterFactory:
    """
    Sole construction owner for PlanningRuntimeAdapter.

    Responsibility:
        - construct PlanningRuntimeAdapter
        - validate its public contract
        - expose factory lifecycle metadata
    """

    VERSION = "1.0"

    def create(self) -> PlanningRuntimeAdapterProtocol:
        adapter = PlanningRuntimeAdapter()
        self._validate(adapter)
        return adapter

    @staticmethod
    def _validate(
        adapter: PlanningRuntimeAdapter,
    ) -> None:
        for name in (
            "adapt",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(adapter, name, None)
            ):
                raise TypeError(
                    "planning runtime adapter must expose "
                    f"{name}()"
                )

        if not adapter.ready():
            raise RuntimeError(
                "planning runtime adapter not ready"
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
    "PlanningRuntimeAdapterFactory",
]
