from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.context.kernel_context import KernelContext
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.core.execution import ExecutionNodeProtocol


@runtime_checkable
class SchedulerBatchExecutorProtocol(
    Protocol,
):
    """
    Runtime scheduler batch execution contract.

    Responsibility:
        - execute already-selected runtime nodes
        - return normalized node execution results

    Not Responsible:
        - graph traversal
        - node selection
        - scheduling policy
        - state mutation
        - retry policy
        - persistence
    """

    async def process(
        self,
        nodes: list[ExecutionNodeProtocol],
        context: KernelContext,
    ) -> list[NodeExecutionResult]:
        ...

    def ready(self) -> bool:
        ...


__all__ = [
    "SchedulerBatchExecutorProtocol",
]
