from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.application.planning.execution_preparer import (
    PlanningExecutionPreparer,
)
from backend.application.planning.execution_preparer_contract import (
    PlanningExecutionPreparerProtocol,
)
from backend.application.planning.runtime_adapter_factory import (
    PlanningRuntimeAdapterFactory,
)
from backend.application.planning.service import (
    PlanningApplicationService,
)


class PlanningExecutionPreparerFactory:
    """
    Sole construction owner for PlanningExecutionPreparer.
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        planning_service: PlanningApplicationService,
        adapter_factory: PlanningRuntimeAdapterFactory | None = None,
    ) -> PlanningExecutionPreparerProtocol:
        if planning_service is None:
            raise ValueError(
                "planning service required"
            )

        factory = (
            adapter_factory
            if adapter_factory is not None
            else PlanningRuntimeAdapterFactory()
        )

        if not factory.ready():
            raise RuntimeError(
                "planning runtime adapter factory unavailable"
            )

        adapter = factory.create()

        preparer = PlanningExecutionPreparer(
            planning_service=planning_service,
            adapter=adapter,
        )

        self._validate(preparer)
        return preparer

    @staticmethod
    def _validate(
        preparer: PlanningExecutionPreparerProtocol,
    ) -> None:
        for name in (
            "prepare",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(preparer, name, None)
            ):
                raise TypeError(
                    "planning execution preparer must expose "
                    f"{name}()"
                )

        if not preparer.ready():
            raise RuntimeError(
                "planning execution preparer not ready"
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
    "PlanningExecutionPreparerFactory",
]
