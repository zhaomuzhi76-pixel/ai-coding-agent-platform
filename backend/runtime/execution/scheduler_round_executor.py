from __future__ import annotations

from backend.core.context.kernel_context import KernelContext

from backend.runtime.execution.empty_round_policy import (
    EmptyRoundPolicy,
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

from backend.runtime.execution.runtime_state_updater import (
    RuntimeStateUpdater,
)
from backend.runtime.execution.runtime_dependency_failure_propagator import (
    RuntimeDependencyFailurePropagator,
)

from backend.runtime.execution.scheduler_execution_contracts import (
    SchedulerBatchExecutorProtocol,
)

from backend.runtime.execution.scheduler_node_selector import (
    SchedulerNodeSelector,
)


class SchedulerRoundExecutor:
    """
    Execute one scheduler round.

    Responsibility:
        - resolve executable nodes
        - commit node lifecycle transitions
        - delegate selected nodes to batch executor

    Not Responsible:
        - executor resolution
        - node execution
        - persistence
    """

    VERSION = "13.0"

    RESPONSIBILITY = (
        "scheduler_round_execution",
        "runtime_lifecycle_commit",
    )

    def __init__(
        self,
        *,
        executor: SchedulerBatchExecutorProtocol,
        selector: SchedulerNodeSelector,
        state_updater: RuntimeStateUpdater,
        failure_propagator: RuntimeDependencyFailurePropagator,
        empty_round_policy: EmptyRoundPolicy | None = None,
    ) -> None:

        if executor is None:
            raise ValueError(
                "scheduler batch executor required"
            )

        if selector is None:
            raise ValueError(
                "scheduler node selector required"
            )

        if state_updater is None:
            raise ValueError(
                "runtime state updater required"
            )

        if failure_propagator is None:
            raise ValueError(
                "runtime dependency failure propagator required"
            )

        self.executor = executor
        self.selector = selector
        self.state_updater = state_updater
        self.failure_propagator = failure_propagator

        self.empty_round_policy = (
            empty_round_policy
            if empty_round_policy is not None
            else EmptyRoundPolicy()
        )

    async def execute(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        context: KernelContext,
    ) -> list[NodeExecutionResult]:

        nodes = self.selector.select(
            graph=graph,
            state=state,
        )

        self.empty_round_policy.validate(
            graph,
            nodes,
        )

        if not nodes:
            return []

        self.state_updater.start(
            state,
            [
                node.node_id
                for node in nodes
            ],
        )

        results = await self.executor.process(
            nodes,
            context,
        )

        self.state_updater.update(
            state,
            results,
        )

        self.failure_propagator.propagate(
            graph=graph,
            state=state,
        )

        return results

    def ready(
        self,
    ) -> bool:

        return all(
            (
                self.executor.ready(),
                self.selector.ready(),
                self.state_updater.ready(),
                self.failure_propagator.ready(),
                self.empty_round_policy.ready(),
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "failure_propagator": self.failure_propagator.dump(),
        }


__all__ = [
    "SchedulerRoundExecutor",
]
