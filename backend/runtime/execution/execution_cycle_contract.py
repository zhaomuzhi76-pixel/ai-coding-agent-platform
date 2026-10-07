from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.context.kernel_context import (
    KernelContext,
)

from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)

from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)

from backend.runtime.execution.runtime_execution_state import (
    RuntimeExecutionState,
)

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


@runtime_checkable
class ExecutionCycleProtocol(
    Protocol,
):
    """
    Runtime execution cycle contract.

    Responsibility:
        - execute one runtime cycle

    Not Responsible:
        - lifecycle control
        - completion decision
        - persistence
    """

    async def run(
        self,
        *,
        graph: RuntimeGraph,
        state: RuntimeExecutionState,
        execution_input: RuntimeExecutionInput,
        context: KernelContext,
        stream_callback=None,
    ) -> list[NodeExecutionResult]:
        ...

    def ready(
        self,
    ) -> bool:
        ...


__all__ = [
    "ExecutionCycleProtocol",
]
