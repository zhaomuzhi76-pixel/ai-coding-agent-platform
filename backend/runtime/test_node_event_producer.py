from __future__ import annotations

import asyncio

from backend.core.events.types import CoreEventType
from backend.runtime.bootstrap.providers import (
    RuntimeComponentProvider,
)
from backend.runtime.execution.node_event_producing_runner import (
    NodeEventProducingRunner,
)
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.core.execution import ExecutionNodeProtocol


class FakeContext:
    pass


class FakeRunner:
    def ready(self) -> bool:
        return True

    async def run(
        self,
        node: ExecutionNodeProtocol,
        context: FakeContext,
    ) -> NodeExecutionResult:
        return NodeExecutionResult.succeeded(
            node.node_id,
            {
                "tested": True,
            },
        )


async def main() -> None:
    runtime = RuntimeComponentProvider(workspace_root=".")

    bus = runtime.resolve_capability(
        "events.bus"
    )
    producer = runtime.resolve_capability(
        "events.node_producer"
    )

    received: list[str] = []

    async def handler(event) -> None:
        received.append(event.type)

    bus.subscribe(
        CoreEventType.NODE_START,
        handler,
    )
    bus.subscribe(
        CoreEventType.NODE_FINISH,
        handler,
    )

    runner = NodeEventProducingRunner(
        runner=FakeRunner(),
        producer=producer,
    )

    node = ExecutionNodeProtocol(
        node_id="test-node",
        executor_type="test",
        node_type="test",
        description="event producer test",
    )

    result = await runner.run(
        node,
        FakeContext(),
    )

    assert result.success is True
    assert received == [
        CoreEventType.NODE_START,
        CoreEventType.NODE_FINISH,
    ]

    print("NODE_EVENT_PRODUCER_TEST=PASS")
