from __future__ import annotations

from backend.core.context.kernel_context import KernelContext

from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)

from backend.runtime.execution.dag_deadlock_detector import (
    DAGDeadlockDetector,
)

from backend.runtime.execution.dag_execution_guard import (
    DAGExecutionGuard,
)

from backend.runtime.execution.dag_loop_completion_checker import (
    DAGLoopCompletionChecker,
)

from backend.runtime.execution.dag_loop_iteration_controller import (
    DAGLoopIterationController,
)

from backend.runtime.execution.dag_round_result_validator import (
    DAGRoundResultValidator,
)

from backend.runtime.execution.execution_cycle_contract import (
    ExecutionCycleProtocol,
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


class DAGExecutionLoop:
    """
    DAG lifecycle loop coordinator.

    Responsibility:
        - control DAG lifecycle
        - invoke execution cycle
        - validate cycle output
        - detect deadlock
        - control iteration

    Not Responsible:
        - node execution
        - scheduling
        - failure classification
        - persistence
    """

    VERSION = "70.0"

    def __init__(
        self,
        *,
        runner: ExecutionCycleProtocol,
        guard: DAGExecutionGuard,
        completion_checker: DAGLoopCompletionChecker,
        iteration_controller: DAGLoopIterationController,
        deadlock_detector: DAGDeadlockDetector | None = None,
        result_validator: DAGRoundResultValidator | None = None,
    ) -> None:

        if runner is None:
            raise ValueError(
                "execution cycle required"
            )

        if guard is None:
            raise ValueError(
                "guard required"
            )

        if completion_checker is None:
            raise ValueError(
                "completion checker required"
            )

        if iteration_controller is None:
            raise ValueError(
                "iteration controller required"
            )

        self.runner = runner
        self.guard = guard
        self.completion_checker = completion_checker
        self.iteration_controller = iteration_controller

        self.deadlock_detector = (
            deadlock_detector
            if deadlock_detector is not None
            else DAGDeadlockDetector()
        )

        self.result_validator = (
            result_validator
            if result_validator is not None
            else DAGRoundResultValidator()
        )

        self.execution_count = 0

    async def execute(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        execution_input: RuntimeExecutionInput,
        context: KernelContext,
        stream_callback=None,
    ) -> list[NodeExecutionResult]:

        self.guard.validate(
            graph,
            state,
            execution_input,
            context,
        )

        outputs: list[NodeExecutionResult] = []

        while not self.completion_checker.completed(
            graph,
            state,
        ):

            self.iteration_controller.next()

            result = await self.runner.run(
                graph=graph,
                state=state,
                execution_input=execution_input,
                context=context,
                stream_callback=stream_callback,
            )

            result = self.result_validator.validate(
                result
            )

            outputs.extend(
                result
            )

            self.deadlock_detector.validate(
                graph=graph,
                state=state,
            )

            self.execution_count += 1

        return outputs

    def ready(
        self,
    ) -> bool:
        return all(
            (
                self.runner.ready(),
                self.guard.ready(),
                self.completion_checker.ready(),
                self.iteration_controller.ready(),
                self.deadlock_detector.ready(),
                self.result_validator.ready(),
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
        }


__all__ = [
    "DAGExecutionLoop",
]
