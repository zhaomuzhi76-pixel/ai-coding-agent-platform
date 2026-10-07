from __future__ import annotations


from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)


from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)


from backend.core.context.kernel_context import (
    KernelContext,
)



class DAGExecutionGuard:
    """
    DAG execution boundary guard.


    Responsibility:
        - validate execution boundary


    Not Responsible:
        - iteration control
        - progress detection
        - scheduling
    """


    VERSION = "2.0"



    def validate(
        self,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        execution_input: RuntimeExecutionInput,
        context: KernelContext,
    ) -> None:


        if graph is None:
            raise ValueError(
                "graph required"
            )


        if state is None:
            raise ValueError(
                "state required"
            )


        if execution_input is None:
            raise ValueError(
                "execution input required"
            )


        if context is None:
            raise ValueError(
                "context required"
            )



    def check(
        self,
        state: RuntimeExecutionState,
    ) -> None:

        if state is None:
            raise ValueError(
                "state required"
            )



    def ready(
        self,
    ) -> bool:

        return True



__all__ = [
    "DAGExecutionGuard",
]
