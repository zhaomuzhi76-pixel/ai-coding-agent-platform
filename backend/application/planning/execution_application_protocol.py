from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import (
    AgentRequest,
)
from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.result import (
    ExecutionResult,
)


@runtime_checkable
class PlanningExecutionApplicationProtocol(
    Protocol,
):
    """
    Application-owned execution application port.

    Planning depends only on this execution capability.
    """

    async def run(
        self,
        *,
        request: AgentRequest,
        context: ContextProtocol,
    ) -> ExecutionResult:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "PlanningExecutionApplicationProtocol",
]
