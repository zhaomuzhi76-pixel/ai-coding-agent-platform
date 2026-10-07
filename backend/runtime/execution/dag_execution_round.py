from __future__ import annotations

from backend.core.context.kernel_context import (
    KernelContext,
)

from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)

from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)

from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)

from backend.runtime.execution.scheduler_dispatcher import (
    SchedulerDispatcher,
)


class DAGExecutionRound:
    """
    Execute one DAG execution round.

    Responsibility:
        - coordinate one scheduler dispatch cycle
        - return normalized node execution results

    Not Responsible:
        - node selection
        - lifecycle transition
        - state mutation
        - completion detection
        - persistence
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

        self.dispatcher = dispatcher


    async def execute(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        execution_input: RuntimeExecutionInput,
        context: KernelContext,
    ) -> list[NodeExecutionResult]:

        if graph is None:
            raise ValueError(
                "graph required"
            )

        if state is None:
            raise ValueError(
                "state required"
            )

        if execution_input is None:
            raise ValueError(
                "execution input required"
            )

        if context is None:
            raise ValueError(
                "context required"
            )

        return await self.dispatcher.dispatch(
            graph=graph,
            state=state,
            context=context,
        )


    def ready(
        self,
    ) -> bool:

        return self.dispatcher.ready()


    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "DAGExecutionRound",
]
