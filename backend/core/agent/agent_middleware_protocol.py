from __future__ import annotations

from typing import Protocol, runtime_checkable

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
class AgentMiddlewareProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Core-owned semantic middleware capability.

    Responsibility:
        - define agent middleware lifecycle hooks
        - expose readiness and diagnostics

    Not Responsible:
        - middleware construction
        - runtime execution
        - planning
        - transport
        - persistence
    """

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

    def is_enabled(
        self,
    ) -> bool:
        ...


__all__ = [
    "AgentMiddlewareProtocol",
]
