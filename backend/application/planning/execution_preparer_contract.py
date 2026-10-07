from __future__ import annotations

from backend.core.contracts.value import CoreValue

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from backend.application.planning.execution_application_protocol import (
    PlanningExecutionApplicationProtocol,
)
from backend.core.agent.agent_request import (
    AgentRequest,
)
from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)
from backend.core.protocols.dumpable import (
    DumpableProtocol,
)
from backend.core.protocols.ready import (
    ReadyProtocol,
)


@runtime_checkable
class PlanningExecutionPreparerProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Application planning execution preparation contract.

    Responsibility:
        - prepare canonical RuntimeExecutionInput
        - expose readiness
        - expose diagnostics

    Does not depend on backend.runtime contracts.
    """

    async def prepare(
        self,
        request: AgentRequest,
        context: ContextProtocol,
        stream_callback: Callable[..., object] | None = None,
    ) -> RuntimeExecutionInput:
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
    "PlanningExecutionPreparerProtocol",
]
