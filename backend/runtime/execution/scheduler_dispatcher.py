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

from backend.runtime.execution.scheduler_dispatch_guard import (
    SchedulerDispatchGuard,
)

from backend.runtime.execution.scheduler_dispatch_runner import (
    SchedulerDispatchRunner,
)


class SchedulerDispatcher:
    """
    Scheduler dispatch coordinator.

    Responsibility:
        - validate dispatch boundary
        - coordinate dispatch flow

    Not Responsible:
        - scheduler execution
        - node execution
        - completion
        - state mutation
        - persistence
    """

    VERSION = "6.0"

    def __init__(
        self,
        *,
        runner: SchedulerDispatchRunner,
        guard: SchedulerDispatchGuard,
    ) -> None:
        if runner is None:
            raise ValueError(
                "dispatch runner required"
            )

        if guard is None:
            raise ValueError(
                "dispatch guard required"
            )

        self.runner = runner
        self.guard = guard

    async def dispatch(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        context: KernelContext,
    ) -> list[NodeExecutionResult]:
        self.guard.validate(
            graph,
            state,
            context,
        )

        return await self.runner.run(
            graph=graph,
            state=state,
            context=context,
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.runner.ready()
            and self.guard.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SchedulerDispatcher",
]
