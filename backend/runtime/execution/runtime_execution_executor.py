from __future__ import annotations

from collections.abc import Callable

from backend.core.context.kernel_context import (
    KernelContext,
)
from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)
from backend.runtime.execution.dag_execution_loop import (
    DAGExecutionLoop,
)
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.runtime.execution.runtime_execution_context import (
    RuntimeExecutionContext,
)
from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


class RuntimeExecutionExecutor:
    """
    Runtime execution implementation boundary.

    Responsibility:
        - implement the runtime execution protocol
        - create request-scoped runtime node state
        - delegate DAG execution
        - return node execution outputs

    Not Responsible:
        - canonical ExecutionResult creation
        - graph construction
        - scheduling
        - node execution
        - failure classification
        - result processing
    """

    VERSION = "9.0"

    RESPONSIBILITY = (
        "runtime_execution_engine",
    )

    def __init__(
        self,
        *,
        loop: DAGExecutionLoop,
        execution_context: RuntimeExecutionContext,
    ) -> None:
        if loop is None:
            raise ValueError(
                "execution loop required"
            )

        if execution_context is None:
            raise ValueError(
                "execution context required"
            )

        if not loop.ready():
            raise RuntimeError(
                "execution loop not ready"
            )

        if not execution_context.ready():
            raise RuntimeError(
                "execution context not ready"
            )

        self.loop = loop
        self.execution_context = execution_context

    async def execute(
        self,
        *,
        graph: RuntimeGraph,
        execution_input: RuntimeExecutionInput,
        context: KernelContext,
        stream_callback: Callable[..., object] | None = None,
    ) -> list[NodeExecutionResult]:
        if not isinstance(
            graph,
            RuntimeGraph,
        ):
            raise TypeError(
                "graph must RuntimeGraph"
            )

        if not isinstance(
            execution_input,
            RuntimeExecutionInput,
        ):
            raise TypeError(
                "execution_input must RuntimeExecutionInput"
            )

        if context is None:
            raise ValueError(
                "context required"
            )

        state = self.execution_context.create_state(
            graph,
        )

        if state is None or not state.ready():
            raise RuntimeError(
                "runtime execution state unavailable"
            )

        outputs = await self.loop.execute(
            graph=graph,
            state=state,
            execution_input=execution_input,
            context=context,
            stream_callback=stream_callback,
        )

        if not isinstance(
            outputs,
            list,
        ):
            raise TypeError(
                "runtime execution outputs must list"
            )

        return outputs

    def ready(
        self,
    ) -> bool:
        return (
            self.loop.ready()
            and self.execution_context.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "loop": type(
                self.loop
            ).__name__,
            "execution_context": type(
                self.execution_context
            ).__name__,
        }


__all__ = [
    "RuntimeExecutionExecutor",
]
