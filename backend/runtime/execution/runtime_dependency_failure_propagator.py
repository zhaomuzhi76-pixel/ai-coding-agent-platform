from __future__ import annotations

from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)
from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)
from backend.runtime.execution.runtime_node_state import (
    RuntimeNodeState,
)


class RuntimeDependencyFailurePropagator:
    """
    Propagate terminal failure through DAG dependencies.

    Responsibility:
        - cancel nodes blocked by failed/cancelled dependencies

    Not Responsible:
        - node execution
        - scheduling
        - retry
        - persistence
    """

    VERSION = "1.0"

    def propagate(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> int:
        self._validate(graph, state)

        cancelled = 0
        changed = True

        while changed:
            changed = False

            terminal_blockers = {
                runtime.node_id
                for runtime in state.all()
                if runtime.state
                in {
                    RuntimeNodeState.FAILED,
                    RuntimeNodeState.CANCELLED,
                }
            }

            for node in graph.all_nodes():
                runtime = state.get(node.node_id)

                if runtime.state not in {
                    RuntimeNodeState.CREATED,
                    RuntimeNodeState.READY,
                }:
                    continue

                if not any(
                    dependency in terminal_blockers
                    for dependency in node.depends_on
                ):
                    continue

                runtime.transition(
                    RuntimeNodeState.CANCELLED
                )
                cancelled += 1
                changed = True

        return cancelled

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate(
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> None:
        if not isinstance(graph, RuntimeGraph):
            raise TypeError("graph must RuntimeGraph")

        if not isinstance(
            state,
            RuntimeExecutionState,
        ):
            raise TypeError(
                "state must RuntimeExecutionState"
            )


__all__ = [
    "RuntimeDependencyFailurePropagator",
]
