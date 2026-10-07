from __future__ import annotations


from backend.runtime.execution.runtime_executable_query import (
    RuntimeExecutableQuery,
)


from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)


from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


from backend.core.execution import (
    ExecutionNodeProtocol,
)



class SchedulerNodeSelector:
    """
    Select nodes for scheduler round.


    Responsibility:
        - resolve executable nodes


    Not Responsible:
        - execution
        - state update
        - retry
    """


    VERSION = "1.0"



    def __init__(
        self,
        query: RuntimeExecutableQuery,
    ) -> None:

        if query is None:
            raise ValueError(
                "executable query required"
            )

        self.query = query



    def select(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
    ) -> list[ExecutionNodeProtocol]:

        return self.query.find(
            graph,
            state,
        )



    def ready(
        self,
    ) -> bool:

        return self.query is not None



__all__ = [
    "SchedulerNodeSelector",
]
