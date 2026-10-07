from __future__ import annotations

from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)

from backend.runtime.execution.runtime_node_state import (
    is_executable,
)


class DAGDeadlockDetector:
    """
    DAG execution deadlock detector.

    Responsibility:
        - detect execution stall
        - detect unfinished topology without executable nodes
        - protect DAG loop from infinite waiting

    Not Responsible:
        - execution
        - scheduling
        - state mutation
        - retry policy
        - persistence
    """

    VERSION = "1.0"

    def detect(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> bool:
        self._validate(
            graph,
            state,
        )

        if not graph.node_ids():
            return False

        if all(
            runtime.finished
            for runtime in state.all()
        ):
            return False

        for node in graph.all_nodes():
            runtime = state.get(
                node.node_id
            )

            if is_executable(
                runtime.state
            ):
                return False

        return True

    def validate(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> None:
        if self.detect(
            graph=graph,
            state=state,
        ):
            raise RuntimeError(
                "DAG execution deadlock detected"
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
    "DAGDeadlockDetector",
]
