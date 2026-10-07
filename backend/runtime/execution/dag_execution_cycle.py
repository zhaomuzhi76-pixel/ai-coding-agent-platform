from __future__ import annotations

from backend.core.context.kernel_context import KernelContext

from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)

from backend.runtime.execution.dag_cycle_progress_tracker import (
    DAGCycleProgressTracker,
)

from backend.runtime.execution.dag_cycle_stream_emitter import (
    DAGCycleStreamEmitter,
)

from backend.runtime.execution.dag_execution_round import (
    DAGExecutionRound,
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


class DAGExecutionCycle:
    """
    Execute one DAG cycle.

    Responsibility:
        - coordinate one execution round
        - enforce cycle progress observation
        - coordinate stream emission

    Not Responsible:
        - completion semantics
        - scheduling
        - state mutation policy
        - persistence
    """

    VERSION = "5.0"

    def __init__(
        self,
        *,
        round_executor: DAGExecutionRound,
        progress_tracker: DAGCycleProgressTracker,
        stream_emitter: DAGCycleStreamEmitter,
    ) -> None:
        if round_executor is None:
            raise ValueError(
                "round executor required"
            )

        if progress_tracker is None:
            raise ValueError(
                "progress tracker required"
            )

        if stream_emitter is None:
            raise ValueError(
                "stream emitter required"
            )

        self.round_executor = round_executor
        self.progress_tracker = progress_tracker
        self.stream_emitter = stream_emitter

    async def execute(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        execution_input: RuntimeExecutionInput,
        context: KernelContext,
        stream_callback=None,
    ) -> list[NodeExecutionResult]:
        if execution_input is None:
            raise ValueError(
                "execution input required"
            )

        before = self.progress_tracker.before(
            state
        )

        outputs = await self.round_executor.execute(
            graph=graph,
            state=state,
            execution_input=execution_input,
            context=context,
        )

        after = self.progress_tracker.after(
            state
        )

        self.progress_tracker.check(
            before,
            after,
        )

        await self.stream_emitter.emit(
            stream_callback,
            outputs,
        )

        return outputs

    def ready(
        self,
    ) -> bool:
        return all(
            (
                self.round_executor.ready(),
                self.progress_tracker.ready(),
                self.stream_emitter.ready(),
            )
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
    "DAGExecutionCycle",
]
