from __future__ import annotations


from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)


from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


from backend.runtime.execution.runtime_node_runtime import (
    RuntimeNodeRuntime,
)



class RuntimeExecutionStateFactory:
    """
    Runtime execution state factory.

    Responsibility:
        - create runtime execution state
        - initialize runtime node runtime objects

    Not Responsible:
        - graph construction
        - execution
        - scheduling
        - lifecycle transition policy
        - persistence
    """


    VERSION = "2.0"


    RESPONSIBILITY = (
        "runtime_execution_state_creation",
    )


    def create(
        self,
        graph: RuntimeGraph,
    ) -> RuntimeExecutionState:

        self._validate_graph(
            graph
        )


        state = RuntimeExecutionState()


        for node in graph.all_nodes():

            state.register(
                RuntimeNodeRuntime(
                    node_id=node.node_id,
                )
            )


        return state



    def create_empty(
        self,
    ) -> RuntimeExecutionState:

        return RuntimeExecutionState()



    def ready(
        self,
    ) -> bool:

        return True



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": (
                "RuntimeExecutionStateFactory"
            ),
            "version": self.VERSION,
            "responsibility": (
                self.RESPONSIBILITY
            ),
            "ready": self.ready(),
        }



    def _validate_graph(
        self,
        graph: RuntimeGraph,
    ) -> None:

        if not isinstance(
            graph,
            RuntimeGraph,
        ):
            raise TypeError(
                "graph must RuntimeGraph"
            )



__all__ = [
    "RuntimeExecutionStateFactory",
]
