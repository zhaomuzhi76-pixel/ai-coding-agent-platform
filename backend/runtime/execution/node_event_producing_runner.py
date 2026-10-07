from __future__ import annotations

from backend.core.context.kernel_context import KernelContext
from backend.runtime.contracts.node_events import (
    RuntimeNodeEventProducerProtocol,
)
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.runtime.execution.node_execution_runner import (
    NodeExecutionRunner,
)
from backend.core.execution import ExecutionNodeProtocol


class NodeEventProducingRunner:
    """
    Runtime execution event decorator.

    Responsibility:
        - emit node lifecycle events around one node execution

    Not Responsible:
        - node execution
        - scheduling
        - state mutation
    """

    VERSION = "1.0"

    def __init__(
        self,
        runner: NodeExecutionRunner,
        producer: RuntimeNodeEventProducerProtocol,
    ) -> None:
        if runner is None:
            raise ValueError(
                "node runner required"
            )

        if producer is None:
            raise ValueError(
                "node event producer required"
            )

        if not isinstance(
            producer,
            RuntimeNodeEventProducerProtocol,
        ):
            raise TypeError(
                "node event producer contract required"
            )

        self.runner = runner
        self.producer = producer

    async def run(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> NodeExecutionResult:
        await self.producer.node_started(
            node,
            context,
        )

        result = await self.runner.run(
            node,
            context,
        )

        if result.success:
            await self.producer.node_finished(
                node,
                result,
            )
        else:
            await self.producer.node_failed(
                node,
                result,
            )

        return result

    def ready(self) -> bool:
        return (
            self.runner.ready()
            and self.producer.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "NodeEventProducingRunner",
]
