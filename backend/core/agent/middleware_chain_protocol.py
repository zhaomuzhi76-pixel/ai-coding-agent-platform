from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_middleware_protocol import (
    AgentMiddlewareProtocol,
)
from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.execution.execution_request_protocol import (
    ExecutionRequestProtocol,
)
from backend.core.protocols.dumpable import (
    DumpableProtocol,
)
from backend.core.protocols.ready import (
    ReadyProtocol,
)


@runtime_checkable
class MiddlewareChainProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Core-owned contract for the agent middleware chain.

    Responsibility:
        - accept middleware capabilities
        - expose middleware lifecycle operations
        - expose readiness and diagnostics

    Not Responsible:
        - middleware construction
        - middleware implementation policy
        - runtime execution
        - transport
    """

    def add(
        self,
        middleware: AgentMiddlewareProtocol,
    ) -> None:
        ...

    async def on_start(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
    ) -> None:
        ...

    async def before(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
    ) -> None:
        ...

    async def after(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
        result: CoreValue,
    ) -> CoreValue:
        ...

    async def on_success(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
        result: CoreValue,
    ) -> None:
        ...

    async def on_failure(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
        error: Exception,
    ) -> None:
        ...

    async def on_finish(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
    ) -> None:
        ...


__all__ = [
    "MiddlewareChainProtocol",
]
