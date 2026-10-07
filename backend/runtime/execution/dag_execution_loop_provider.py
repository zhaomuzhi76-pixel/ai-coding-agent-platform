from __future__ import annotations

from backend.runtime.execution.dag_execution_cycle import (
    DAGExecutionCycle,
)
from backend.runtime.execution.dag_execution_cycle_provider import (
    DAGExecutionCycleProvider,
)
from backend.runtime.execution.dag_execution_guard import (
    DAGExecutionGuard,
)
from backend.runtime.execution.dag_execution_loop import (
    DAGExecutionLoop,
)
from backend.runtime.execution.dag_iteration_policy import (
    DAGIterationPolicy,
)
from backend.runtime.execution.dag_loop_completion_checker import (
    DAGLoopCompletionChecker,
)
from backend.runtime.execution.dag_loop_iteration_controller import (
    DAGLoopIterationController,
)
from backend.runtime.execution.runtime_execution_cycle_adapter import (
    RuntimeExecutionCycleAdapter,
)


class DAGExecutionLoopProvider:
    """
    DAG execution loop composition boundary.

    Responsibility:
        - consume assembled cycle provider
        - assemble DAG lifecycle loop

    Not Responsible:
        - scheduler construction
        - executor resolution
        - state construction
        - node event producer construction
    """

    VERSION = "5.0"

    def __init__(
        self,
        *,
        cycle_provider: DAGExecutionCycleProvider,
    ) -> None:
        if cycle_provider is None:
            raise ValueError(
                "DAG execution cycle provider required"
            )

        if not isinstance(
            cycle_provider,
            DAGExecutionCycleProvider,
        ):
            raise TypeError(
                "cycle provider must DAGExecutionCycleProvider"
            )

        self.cycle_provider = cycle_provider

    def create_cycle(
        self,
    ) -> DAGExecutionCycle:
        return self.cycle_provider.create()

    def create(
        self,
    ) -> DAGExecutionLoop:
        cycle = self.create_cycle()

        return DAGExecutionLoop(
            runner=RuntimeExecutionCycleAdapter(
                cycle
            ),
            guard=DAGExecutionGuard(),
            completion_checker=DAGLoopCompletionChecker(),
            iteration_controller=DAGLoopIterationController(
                policy=DAGIterationPolicy()
            ),
        )

    def ready(
        self,
    ) -> bool:
        return self.cycle_provider.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "cycle_provider": (
                self.cycle_provider.dump()
            ),
            "ready": self.ready(),
        }


__all__ = [
    "DAGExecutionLoopProvider",
]
