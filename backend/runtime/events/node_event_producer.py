from __future__ import annotations

from backend.core.context.context_protocol import ContextProtocol
from backend.core.events.contracts import EventBusProtocol
from backend.core.events.types import CoreEventType
from backend.core.execution import ExecutionNodeProtocol
from backend.runtime.contracts.node_events import (
    RuntimeNodeEventProducerProtocol,
)
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.runtime.events.event import RuntimeEvent


class RuntimeNodeEventProducer(
    RuntimeNodeEventProducerProtocol,
):
    """Runtime-owned node execution event producer."""

    VERSION = "2.0"
    SOURCE = "runtime.node_execution"

    def __init__(
        self,
        event_bus: EventBusProtocol,
    ) -> None:
        if not isinstance(event_bus, EventBusProtocol):
            raise TypeError(
                "event bus contract required"
            )
        self.event_bus = event_bus
        self.emitted_count = 0
        self.failure_count = 0

    async def node_started(
        self,
        node: ExecutionNodeProtocol,
        context: ContextProtocol,
    ) -> None:
        self._validate_node(node)
        if context is None:
            raise ValueError("context required")
        await self._publish(
            RuntimeEvent.create(
                CoreEventType.NODE_START,
                {
                    "node_id": node.node_id,
                    "executor_type": node.executor_type,
                },
                source=self.SOURCE,
                node_id=node.node_id,
            )
        )

    async def node_finished(
        self,
        node: ExecutionNodeProtocol,
        result: NodeExecutionResult,
    ) -> None:
        await self._publish_result(
            node,
            result,
            CoreEventType.NODE_FINISH,
        )

    async def node_failed(
        self,
        node: ExecutionNodeProtocol,
        result: NodeExecutionResult,
    ) -> None:
        await self._publish_result(
            node,
            result,
            CoreEventType.NODE_FAILED,
        )

    async def _publish_result(
        self,
        node: ExecutionNodeProtocol,
        result: NodeExecutionResult,
        event_type: str,
    ) -> None:
        self._validate_node(node)
        if not isinstance(result, NodeExecutionResult):
            raise TypeError(
                "result must NodeExecutionResult"
            )
        await self._publish(
            RuntimeEvent.create(
                event_type,
                {
                    "node_id": node.node_id,
                    "executor_type": node.executor_type,
                    "success": result.success,
                },
                source=self.SOURCE,
                node_id=node.node_id,
            )
        )

    async def _publish(
        self,
        event: RuntimeEvent,
    ) -> None:
        try:
            await self.event_bus.publish(event)
            self.emitted_count += 1
        except Exception:
            self.failure_count += 1

    def ready(self) -> bool:
        return self.event_bus.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "emitted_count": self.emitted_count,
            "failure_count": self.failure_count,
        }

    @staticmethod
    def _validate_node(
        node: ExecutionNodeProtocol,
    ) -> None:
        if not isinstance(
            node,
            ExecutionNodeProtocol,
        ):
            raise TypeError(
                "node must ExecutionNodeProtocol"
            )


__all__ = [
    "RuntimeNodeEventProducer",
]
