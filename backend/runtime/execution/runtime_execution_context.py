from __future__ import annotations


from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)


from backend.runtime.execution.runtime_execution_state_factory import (
    RuntimeExecutionStateFactory,
)


from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)



class RuntimeExecutionContext:
    """
    Runtime execution context creator.


    Responsibility:
        - create execution state


    Not Responsible:
        - execution
        - scheduling
        - lifecycle mutation
    """


    VERSION = "1.0"


    def __init__(
        self,
        factory: RuntimeExecutionStateFactory,
    ) -> None:


        if factory is None:
            raise ValueError(
                "state factory required"
            )


        self.factory = factory



    def create_state(
        self,
        graph: RuntimeGraph,
    ) -> RuntimeExecutionState:

        return self.factory.create(
            graph
        )


    def ready(
        self,
    ) -> bool:

        return self.factory.ready()



__all__ = [
    "RuntimeExecutionContext",
]
