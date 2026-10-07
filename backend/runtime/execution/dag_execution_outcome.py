from __future__ import annotations

from backend.runtime.execution.dag_loop_completion_checker import (
    DAGLoopCompletionChecker,
)

from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


class DAGExecutionOutcome:
    """
    DAG final execution outcome.

    Responsibility:
        - expose final execution semantic state

    Not Responsible:
        - execution
        - scheduling
        - state mutation
        - persistence
    """

    VERSION = "1.0"

    def __init__(
        self,
        checker: DAGLoopCompletionChecker | None = None,
    ) -> None:
        self.checker = (
            checker
            if checker is not None
            else DAGLoopCompletionChecker()
        )

    def success(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> bool:
        return self.checker.successful(
            graph,
            state,
        )

    def failed(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> bool:
        return self.checker.failed(
            graph,
            state,
        )

    def ready(
        self,
    ) -> bool:
        return self.checker.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "DAGExecutionOutcome",
]
