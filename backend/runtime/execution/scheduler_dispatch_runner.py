from __future__ import annotations

from backend.core.context.kernel_context import KernelContext

from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)

from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)

from backend.runtime.execution.scheduler_round_executor import (
    SchedulerRoundExecutor,
)


class SchedulerDispatchRunner:
    """
    Scheduler round execution boundary.

    Responsibility:
        - invoke scheduler round executor

    Not Responsible:
        - completion
        - validation implementation
        - state mutation policy
        - node execution
    """

    VERSION = "2.0"

    def __init__(
        self,
        executor: SchedulerRoundExecutor,
    ) -> None:
        if executor is None:
            raise ValueError(
                "scheduler round executor required"
            )

        self.executor = executor

    async def run(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        context: KernelContext,
    ) -> list[NodeExecutionResult]:
        return await self.executor.execute(
            graph=graph,
            state=state,
            context=context,
        )

    def ready(
        self,
    ) -> bool:
        return self.executor.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SchedulerDispatchRunner",
]
