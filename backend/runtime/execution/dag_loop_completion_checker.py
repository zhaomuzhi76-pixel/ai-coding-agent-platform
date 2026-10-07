from __future__ import annotations

from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)
from backend.runtime.execution.runtime_node_state import (
    RuntimeNodeState,
)

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


class DAGLoopCompletionChecker:
    """
    DAG completion semantic owner.

    Responsibility:
        - own DAG completion semantics
        - reject empty execution topology
        - reject graph/state topology mismatch
        - determine terminal completion
        - distinguish successful and failed completion

    Not Responsible:
        - execution
        - scheduling
        - iteration control
        - state mutation
        - persistence
    """

    VERSION = "3.0"

    def completed(
        self,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> bool:
        self._validate(
            graph,
            state,
        )

        graph_ids = graph.node_ids()
        state_ids = {
            runtime.node_id
            for runtime in state.all()
        }

        if not graph_ids:
            return False

        if graph_ids != state_ids:
            return False

        return all(
            runtime.finished
            for runtime in state.all()
        )

    def successful(
        self,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> bool:
        self._validate(
            graph,
            state,
        )

        if not self.completed(
            graph,
            state,
        ):
            return False

        return all(
            runtime.state is RuntimeNodeState.SUCCESS
            for runtime in state.all()
        )

    def failed(
        self,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> bool:
        self._validate(
            graph,
            state,
        )

        if not self.completed(
            graph,
            state,
        ):
            return False

        return any(
            runtime.state
            in {
                RuntimeNodeState.FAILED,
                RuntimeNodeState.CANCELLED,
            }
            for runtime in state.all()
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

    @staticmethod
    def _validate(
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
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


__all__ = [
    "DAGLoopCompletionChecker",
]
