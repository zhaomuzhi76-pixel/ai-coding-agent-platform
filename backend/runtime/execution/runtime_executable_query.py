from __future__ import annotations

from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)

from backend.core.execution import (
    ExecutionNodeProtocol,
)

from backend.runtime.execution.runtime_node_state import (
    RuntimeNodeState,
    is_executable,
)


class RuntimeExecutableQuery:
    """
    Query executable runtime nodes.

    Responsibility:
        - resolve executable nodes
        - enforce successful dependency requirement

    Not Responsible:
        - execution
        - scheduling
        - state mutation
        - retry policy
    """

    VERSION = "2.0"

    def find(
        self,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> list[ExecutionNodeProtocol]:

        successful = {
            runtime.node_id
            for runtime in state.all()
            if runtime.state
            is RuntimeNodeState.SUCCESS
        }

        result: list[ExecutionNodeProtocol] = []

        for node in graph.all_nodes():

            runtime = state.get(
                node.node_id
            )

            if not is_executable(
                runtime.state
            ):
                continue

            if all(
                dep in successful
                for dep in node.depends_on
            ):
                result.append(
                    node
                )

        return result


__all__ = [
    "RuntimeExecutableQuery",
]
