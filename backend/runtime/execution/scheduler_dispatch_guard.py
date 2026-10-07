from __future__ import annotations

from backend.core.context.kernel_context import (
    KernelContext,
)
from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)
from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


class SchedulerDispatchGuard:
    """
    Scheduler dispatch boundary guard.

    Responsibility:
        - validate scheduler dispatch input
        - enforce concrete runtime contracts

    Not Responsible:
        - node selection
        - execution
        - completion
        - state mutation
        - persistence
    """

    VERSION = "2.0"

    def validate(
        self,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        context: KernelContext,
    ) -> None:
        if not isinstance(
            graph,
            RuntimeGraph,
        ):
            raise TypeError(
                "graph must RuntimeGraph"
            )

        if not isinstance(
            state,
            RuntimeExecutionState,
        ):
            raise TypeError(
                "state must RuntimeExecutionState"
            )

        if not isinstance(
            context,
            KernelContext,
        ):
            raise TypeError(
                "context must KernelContext"
            )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SchedulerDispatchGuard",
]
