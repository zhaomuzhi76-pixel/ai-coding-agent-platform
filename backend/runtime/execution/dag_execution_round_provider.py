from __future__ import annotations

from backend.runtime.execution.dag_execution_round import (
    DAGExecutionRound,
)
from backend.runtime.execution.runtime_state_updater import (
    RuntimeStateUpdater,
)
from backend.runtime.execution.scheduler_dispatcher import (
    SchedulerDispatcher,
)


class DAGExecutionRoundProvider:
    """
    DAG execution round composition boundary.

    Responsibility:
        - consume an assembled scheduler dispatcher
        - consume the shared runtime state updater
        - assemble DAGExecutionRound

    Not Responsible:
        - scheduler provider construction
        - executor resolution
        - node event producer construction
        - runtime state construction
    """

    VERSION = "6.0"

    def __init__(
        self,
        *,
        dispatcher: SchedulerDispatcher,
    ) -> None:
        if dispatcher is None:
            raise ValueError(
                "scheduler dispatcher required"
            )

        if not isinstance(
            dispatcher,
            SchedulerDispatcher,
        ):
            raise TypeError(
                "dispatcher must SchedulerDispatcher"
            )
        self.dispatcher = dispatcher
    def create(
        self,
    ) -> DAGExecutionRound:
        return DAGExecutionRound(
            dispatcher=self.dispatcher,
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.dispatcher.ready()        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "dispatcher": (
                type(self.dispatcher).__name__
            ),            "ready": self.ready(),
        }


__all__ = [
    "DAGExecutionRoundProvider",
]
