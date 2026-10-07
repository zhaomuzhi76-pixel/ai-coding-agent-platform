from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.context.context_protocol import (
    ContextProtocol,
)

from backend.core.execution import (
    ExecutionNodeProtocol,
)

from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)


@runtime_checkable
class RuntimeNodeEventProducerProtocol(
    Protocol,
):
    """
    Runtime node event producer contract.

    Responsibility:
        - publish node lifecycle events

    Not Responsible:
        - execution
        - scheduling
        - state mutation
    """

    async def node_started(
        self,
        node: ExecutionNodeProtocol,
        context: ContextProtocol,
    ) -> None:
        ...

    async def node_finished(
        self,
        node: ExecutionNodeProtocol,
        result: NodeExecutionResult,
    ) -> None:
        ...

    async def node_failed(
        self,
        node: ExecutionNodeProtocol,
        result: NodeExecutionResult,
    ) -> None:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "RuntimeNodeEventProducerProtocol",
]
