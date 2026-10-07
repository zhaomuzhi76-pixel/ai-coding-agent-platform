from __future__ import annotations

from backend.runtime.execution.dag_cycle_progress_tracker import (
    DAGCycleProgressTracker,
)
from backend.runtime.execution.dag_cycle_stream_emitter import (
    DAGCycleStreamEmitter,
)
from backend.runtime.execution.dag_execution_cycle import (
    DAGExecutionCycle,
)
from backend.runtime.execution.dag_execution_progress import (
    DAGExecutionProgress,
)
from backend.runtime.execution.dag_execution_round_provider import (
    DAGExecutionRoundProvider,
)
from backend.runtime.execution.dag_execution_stream import (
    DAGExecutionStream,
)


class DAGExecutionCycleProvider:
    """
    DAG execution cycle composition boundary.

    Responsibility:
        - consume assembled DAG round provider
        - assemble cycle observation components
        - assemble DAGExecutionCycle

    Not Responsible:
        - scheduler construction
        - executor resolution
        - runtime state construction
    """

    VERSION = "4.0"

    def __init__(
        self,
        *,
        round_provider: DAGExecutionRoundProvider,
    ) -> None:
        if round_provider is None:
            raise ValueError(
                "DAG execution round provider required"
            )

        if not isinstance(
            round_provider,
            DAGExecutionRoundProvider,
        ):
            raise TypeError(
                "round provider must DAGExecutionRoundProvider"
            )

        self.round_provider = round_provider

    def create(
        self,
    ) -> DAGExecutionCycle:
        return DAGExecutionCycle(
            round_executor=self.round_provider.create(),
            progress_tracker=DAGCycleProgressTracker(
                DAGExecutionProgress()
            ),
            stream_emitter=DAGCycleStreamEmitter(
                DAGExecutionStream()
            ),
        )

    def ready(
        self,
    ) -> bool:
        return self.round_provider.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "round_provider": (
                self.round_provider.dump()
            ),
            "ready": self.ready(),
        }


__all__ = [
    "DAGExecutionCycleProvider",
]
