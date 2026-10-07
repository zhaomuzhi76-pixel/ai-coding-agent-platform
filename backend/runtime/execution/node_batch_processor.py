from __future__ import annotations

import asyncio

from backend.core.context.kernel_context import KernelContext
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.runtime.execution.node_execution_runner import (
    NodeExecutionRunner,
)
from backend.core.execution import ExecutionNodeProtocol


class NodeBatchProcessor:
    """
    Runtime internal concurrent node processor.

    Responsibility:
        - execute a selected ExecutionNodeProtocol batch concurrently
        - enforce local concurrency limit

    Not Responsible:
        - node selection
        - scheduler policy
        - executor resolution
        - persistence
    """

    VERSION = "36.0"

    def __init__(
        self,
        runner: NodeExecutionRunner,
        max_concurrency: int = 4,
    ) -> None:
        if runner is None:
            raise ValueError(
                "node runner required"
            )

        if max_concurrency <= 0:
            raise ValueError(
                "max_concurrency must positive"
            )

        self.runner = runner
        self.max_concurrency = max_concurrency

    async def process(
        self,
        nodes: list[ExecutionNodeProtocol],
        context: KernelContext,
    ) -> list[NodeExecutionResult]:
        self._validate(
            nodes,
            context,
        )

        if not nodes:
            return []

        semaphore = asyncio.Semaphore(
            self.max_concurrency
        )

        async def execute(
            node: ExecutionNodeProtocol,
        ) -> NodeExecutionResult:
            async with semaphore:
                return await self.runner.run(
                    node,
                    context,
                )

        return list(
            await asyncio.gather(
                *(
                    execute(node)
                    for node in nodes
                )
            )
        )

    def ready(self) -> bool:
        return self.runner.ready()

    def _validate(
        self,
        nodes: list[ExecutionNodeProtocol],
        context: KernelContext,
    ) -> None:
        if not isinstance(nodes, list):
            raise TypeError(
                "nodes must list"
            )

        for node in nodes:
            if not isinstance(
                node,
                ExecutionNodeProtocol,
            ):
                raise TypeError(
                    "invalid runtime node"
                )

        if context is None:
            raise ValueError(
                "context required"
            )


__all__ = [
    "NodeBatchProcessor",
]
