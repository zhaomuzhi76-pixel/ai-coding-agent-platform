from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.execution.execution_lifecycle_state import (
    ExecutionLifecycleState,
)
from backend.core.execution.execution_request_protocol import (
    ExecutionRequestProtocol,
)
from backend.core.execution.execution_stream_protocol import (
    ExecutionStreamProtocol,
)
from backend.core.protocols.dumpable import (
    DumpableProtocol,
)
from backend.core.protocols.ready import (
    ReadyProtocol,
)
from backend.core.result import (
    ExecutionResult,
)


@runtime_checkable
class RuntimeExecutionProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Core-owned runtime execution port.

    Owns only the cross-layer execution contract.
    It does not depend on Agent-layer implementations.
    """

    async def run(
        self,
        request: ExecutionRequestProtocol,
        context: ContextProtocol,
        lifecycle_state: ExecutionLifecycleState,
        stream: ExecutionStreamProtocol | None = None,
    ) -> ExecutionResult:
        ...


__all__ = [
    "RuntimeExecutionProtocol",
]
