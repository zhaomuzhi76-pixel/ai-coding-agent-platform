from __future__ import annotations

from backend.core.context.kernel_context import (
    KernelContext,
)

from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)

from backend.runtime.execution.dag_execution_cycle import (
    DAGExecutionCycle,
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


class RuntimeExecutionCycleAdapter:
    """
    Runtime execution cycle adapter.

    Responsibility:
        - adapt DAG cycle to execution-cycle contract

    Not Responsible:
        - loop lifecycle
        - completion
        - iteration policy
    """

    VERSION = "2.1"

    def __init__(
        self,
        cycle: DAGExecutionCycle,
    ) -> None:
        if cycle is None:
            raise ValueError(
                "cycle required"
            )

        self.cycle = cycle

    async def run(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        execution_input: RuntimeExecutionInput,
        context: KernelContext,
        stream_callback=None,
    ) -> list[NodeExecutionResult]:

        return await self.cycle.execute(
            graph=graph,
            state=state,
            execution_input=execution_input,
            context=context,
            stream_callback=stream_callback,
        )

    def ready(
        self,
    ) -> bool:
        return self.cycle.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeExecutionCycleAdapter",
]
