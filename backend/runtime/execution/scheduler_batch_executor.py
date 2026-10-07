from __future__ import annotations

from backend.core.context.kernel_context import KernelContext
from backend.runtime.execution.node_batch_processor import (
    NodeBatchProcessor,
)
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.core.execution import ExecutionNodeProtocol
from backend.runtime.execution.scheduler_result_collector import (
    SchedulerResultCollector,
)


class SchedulerBatchExecutor:
    """
    Runtime scheduler batch executor.

    Responsibility:
        - execute already-selected runtime nodes
        - collect normalized execution results

    Not Responsible:
        - graph traversal
        - node selection
        - scheduling policy
        - node failure classification
        - state mutation
        - persistence
    """

    VERSION = "3.0"

    def __init__(
        self,
        *,
        processor: NodeBatchProcessor,
        collector: SchedulerResultCollector,
    ) -> None:
        if processor is None:
            raise ValueError(
                "node batch processor required"
            )

        if collector is None:
            raise ValueError(
                "scheduler result collector required"
            )

        self.processor = processor
        self.collector = collector

    async def process(
        self,
        nodes: list[ExecutionNodeProtocol],
        context: KernelContext,
    ) -> list[NodeExecutionResult]:
        if context is None:
            raise ValueError(
                "context required"
            )

        if not isinstance(nodes, list):
            raise TypeError(
                "nodes must list"
            )

        if not nodes:
            return []

        results = await self.processor.process(
            nodes,
            context,
        )

        return self.collector.collect(
            results
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.processor.ready()
            and self.collector.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SchedulerBatchExecutor",
]
